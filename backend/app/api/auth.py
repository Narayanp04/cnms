"""ConnectXperts NMS - Authentication API"""
from datetime import datetime, timezone, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, init_db
from app.models.user import User, Role, UserRole, Customer
from app.schemas.user import (
    UserCreate, UserResponse, LoginRequest, TokenResponse,
    RefreshTokenRequest, PasswordChangeRequest, CustomerCreate, CustomerResponse
)
from app.utils.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, decode_token,
    get_current_user, check_role_permissions
)
from app.config import settings
from app.services.event_log_service import EventLogService

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])
event_log_service = EventLogService()


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    # Find user
    result = await db.execute(
        select(User).where(User.username == credentials.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.flush()
    
    # Log event
    await event_log_service.log_login(
        user_id=user.id,
        username=user.username,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent")
    )
    
    # Generate tokens
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token."""
    payload = decode_token(token_data.refresh_token)
    username = payload.get("sub")
    
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid refresh token")
    
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid user")
    
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role.value},
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client-side token removal)."""
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password."""
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.flush()
    
    return {"message": "Password changed successfully"}


# Admin endpoints
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """List all users (Admin only)."""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """Create new user (Admin only)."""
    # Check if username or email exists
    existing = await db.execute(
        select(User).where(
            (User.username == user_data.username) | (User.email == user_data.email)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        company=user_data.company,
        phone=user_data.phone,
        role=user_data.role,
        customer_id=user_data.customer_id,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    await db.flush()
    
    return UserResponse.model_validate(user)


@router.get("/customers", response_model=List[CustomerResponse])
async def list_customers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all customers."""
    result = await db.execute(select(Customer))
    customers = result.scalars().all()
    return [
        CustomerResponse(
            **{k: getattr(c, k) for k in CustomerResponse.model_fields.keys() if hasattr(c, k)},
            device_count=0
        )
        for c in customers
    ]


@router.post("/customers", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """Create new customer (Admin only)."""
    customer = Customer(**customer_data.model_dump())
    db.add(customer)
    await db.flush()
    
    return CustomerResponse.model_validate(customer)

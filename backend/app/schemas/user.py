"""ConnectXperts NMS - User Schemas"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models.user import Role


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    role: Role = Role.READ_ONLY
    customer_id: Optional[int] = None
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email address')
        return v.lower()


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[Role] = None
    customer_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    is_verified: bool
    role: Role
    customer_id: Optional[int] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: str = Field(..., min_length=2, max_length=50)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = None


class CustomerResponse(BaseModel):
    id: int
    name: str
    code: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool
    notes: Optional[str] = None
    created_at: datetime
    device_count: Optional[int] = 0
    
    class Config:
        from_attributes = True

"""ConnectXperts NMS - Customer Management API"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, Role, Customer
from app.schemas.user import CustomerCreate, CustomerResponse
from app.utils.security import get_current_user, check_role_permissions

router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])


@router.get("", response_model=List[CustomerResponse])
async def list_customers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all customers."""
    result = await db.execute(select(Customer).where(Customer.is_active == True))
    customers = result.scalars().all()
    
    # Get device counts
    from app.models.device import Device
    from sqlalchemy import func
    
    response = []
    for c in customers:
        count_result = await db.execute(
            select(func.count(Device.id)).where(
                Device.customer_id == c.id,
                Device.is_deleted == False
            )
        )
        device_count = count_result.scalar() or 0
        
        response.append(CustomerResponse(
            **{k: getattr(c, k) for k in CustomerResponse.model_fields.keys() if hasattr(c, k)},
            device_count=device_count
        ))
    
    return response


@router.post("", response_model=CustomerResponse)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """Create a new customer."""
    customer = Customer(**customer_data.model_dump())
    db.add(customer)
    await db.flush()
    return CustomerResponse.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get customer details."""
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    from app.models.device import Device
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count(Device.id)).where(
            Device.customer_id == customer.id,
            Device.is_deleted == False
        )
    )
    
    return CustomerResponse(
        **{k: getattr(customer, k) for k in CustomerResponse.model_fields.keys() if hasattr(customer, k)},
        device_count=count_result.scalar() or 0
    )


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """Update customer."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    for field, value in customer_data.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)
    
    return CustomerResponse.model_validate(customer)

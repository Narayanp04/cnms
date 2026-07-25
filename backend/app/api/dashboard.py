"""ConnectXperts NMS - Dashboard API"""
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, Role
from app.schemas.dashboard import DashboardWidgetData, RegionSummary
from app.services.dashboard_service import DashboardService
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])
dashboard_service = DashboardService()


@router.get("/", response_model=DashboardWidgetData)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get complete dashboard data with all widgets."""
    customer_id = current_user.customer_id if current_user.role != Role.ADMIN else None
    return await dashboard_service.get_full_dashboard(db, customer_id)


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics only."""
    customer_id = current_user.customer_id if current_user.role != Role.ADMIN else None
    return await dashboard_service.get_dashboard_stats(db, customer_id)


@router.get("/regions", response_model=list)
async def get_region_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get device summary by region."""
    from sqlalchemy import select, func, case
    from app.models.device import Device, DeviceStatus
    
    query = select(
        Device.region,
        func.count(Device.id).label('total'),
        func.sum(case((Device.status == DeviceStatus.UP, 1), else_=0)).label('up'),
        func.sum(case((Device.status == DeviceStatus.DOWN, 1), else_=0)).label('down'),
        func.sum(case((Device.status == DeviceStatus.WARNING, 1), else_=0)).label('warning'),
        func.avg(Device.current_latency).label('avg_latency')
    ).where(
        Device.is_deleted == False,
        Device.region.isnot(None)
    ).group_by(Device.region)
    
    if current_user.role != Role.ADMIN and current_user.customer_id:
        query = query.where(Device.customer_id == current_user.customer_id)
    
    result = await db.execute(query)
    rows = result.all()
    
    return [
        RegionSummary(
            region=row.region,
            total=int(row.total),
            up=int(row.up or 0),
            down=int(row.down or 0),
            warning=int(row.warning or 0),
            avg_latency=round(float(row.avg_latency), 2) if row.avg_latency else None
        )
        for row in rows
    ]

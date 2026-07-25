"""ConnectXperts NMS - SLA API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.user import User, Role
from app.models.sla_report import SLAReport, SLAReportPeriod
from app.models.device import Device
from app.schemas.sla_report import SLAReportResponse, SLAReportListResponse
from app.services.sla_service import SLAService
from app.utils.security import get_current_user, check_role_permissions

router = APIRouter(prefix="/api/v1/sla", tags=["SLA"])
sla_service = SLAService()


@router.get("/reports", response_model=SLAReportListResponse)
async def list_sla_reports(
    device_id: Optional[int] = None,
    period: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List SLA reports with filters."""
    query = select(SLAReport)
    
    if current_user.role != Role.ADMIN and current_user.customer_id:
        query = query.where(
            SLAReport.device_id.in_(
                select(Device.id).where(Device.customer_id == current_user.customer_id)
            )
        )
    
    if device_id:
        query = query.where(SLAReport.device_id == device_id)
    if period:
        query = query.where(SLAReport.period == period)
    
    from sqlalchemy import func
    count_query = query.with_only_columns(func.count(SLAReport.id))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    query = query.order_by(desc(SLAReport.period_start)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    reports = result.scalars().all()
    
    return SLAReportListResponse(
        total=total,
        items=[SLAReportResponse.model_validate(r) for r in reports],
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 1
    )


@router.post("/reports/generate")
async def generate_sla_report(
    device_id: int,
    period: str = Query(..., regex="^(daily|weekly|monthly|yearly)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role_permissions([Role.ADMIN, Role.OPERATOR]))
):
    """Generate SLA report for a device."""
    from datetime import datetime, timezone, timedelta
    
    now = datetime.now(timezone.utc)
    period_map = {
        "daily": (now - timedelta(days=1), SLAReportPeriod.DAILY),
        "weekly": (now - timedelta(weeks=1), SLAReportPeriod.WEEKLY),
        "monthly": (now - timedelta(days=30), SLAReportPeriod.MONTHLY),
        "yearly": (now - timedelta(days=365), SLAReportPeriod.YEARLY),
    }
    
    start, sla_period = period_map[period]
    report = await sla_service.generate_sla_report(db, device_id, sla_period, start, now)
    
    if not report:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return SLAReportResponse.model_validate(report)


@router.get("/device/{device_id}")
async def get_device_sla(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get SLA summary for a device."""
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.is_deleted == False)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return {
        "device_id": device.id,
        "hostname": device.hostname,
        "sla_24h": device.sla_24h or 100.0,
        "sla_7d": device.sla_7d or 100.0,
        "sla_30d": device.sla_30d or 100.0,
        "sla_365d": device.sla_365d or 100.0,
        "total_uptime_seconds": device.total_uptime_seconds or 0,
        "total_downtime_seconds": device.total_downtime_seconds or 0,
        "uptime_human": _format_seconds(device.total_uptime_seconds),
        "downtime_human": _format_seconds(device.total_downtime_seconds)
    }


def _format_seconds(seconds: int) -> str:
    if not seconds:
        return "0s"
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    parts = []
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    if secs > 0: parts.append(f"{secs}s")
    return " ".join(parts)

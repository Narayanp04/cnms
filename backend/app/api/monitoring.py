"""ConnectXperts NMS - Real-time Monitoring API"""
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.database import get_db
from app.models.user import User, Role
from app.models.device import Device, DeviceStatus
from app.models.ping_result import PingResult, PingStatus
from app.schemas.ping_result import PingResultResponse, PingChartData, PingStats
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])


@router.get("/devices/status")
async def get_all_device_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get real-time status for all devices."""
    query = select(Device).where(Device.is_deleted == False)
    
    if current_user.role != Role.ADMIN and current_user.customer_id:
        query = query.where(Device.customer_id == current_user.customer_id)
    
    result = await db.execute(query)
    devices = result.scalars().all()
    
    return [
        {
            "id": d.id,
            "hostname": d.hostname,
            "ip_address": d.ip_address,
            "display_name": d.display_name,
            "status": d.status.value if d.status else "unknown",
            "current_latency": d.current_latency,
            "current_packet_loss": d.current_packet_loss,
            "current_jitter": d.current_jitter,
            "response_time": d.current_response_time,
            "last_response": d.last_response.isoformat() if d.last_response else None,
            "sla_24h": d.sla_24h or 100.0,
            "customer_name": d.customer_name,
            "site_name": d.site_name,
            "is_monitoring_enabled": d.is_monitoring_enabled,
            "color": "green" if d.status == DeviceStatus.UP else "red" if d.status == DeviceStatus.DOWN else "yellow" if d.status == DeviceStatus.WARNING else "gray"
        }
        for d in devices
    ]


@router.get("/device/{device_id}/history", response_model=PingChartData)
async def get_device_ping_history(
    device_id: int,
    period: str = Query("24h", regex="^(1h|6h|12h|24h|7d|30d|90d|180d|365d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ping history for charts."""
    # Verify device access
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.is_deleted == False)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if current_user.role != Role.ADMIN and current_user.customer_id:
        if device.customer_id != current_user.customer_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate time range
    now = datetime.now(timezone.utc)
    time_map = {
        "1h": timedelta(hours=1), "6h": timedelta(hours=6),
        "12h": timedelta(hours=12), "24h": timedelta(hours=24),
        "7d": timedelta(days=7), "30d": timedelta(days=30),
        "90d": timedelta(days=90), "180d": timedelta(days=180),
        "365d": timedelta(days=365)
    }
    since = now - time_map.get(period, timedelta(hours=24))
    
    # Get ping results
    ping_result = await db.execute(
        select(PingResult).where(
            PingResult.device_id == device_id,
            PingResult.timestamp >= since
        ).order_by(PingResult.timestamp.asc())
    )
    results = ping_result.scalars().all()
    
    return PingChartData(
        timestamps=[r.timestamp for r in results],
        latency=[r.latency_ms for r in results],
        packet_loss=[r.packet_loss_percent for r in results],
        jitter=[r.jitter_ms for r in results],
        response_time=[r.response_time_ms for r in results],
        status=[r.status.value for r in results]
    )


@router.get("/device/{device_id}/stats", response_model=PingStats)
async def get_device_ping_stats(
    device_id: int,
    period: str = Query("24h", regex="^(24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ping statistics for a device."""
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.is_deleted == False)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    now = datetime.now(timezone.utc)
    time_map = {"24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30)}
    since = now - time_map.get(period, timedelta(hours=24))
    
    from sqlalchemy import func, case
    
    stats_result = await db.execute(
        select(
            func.count(PingResult.id).label('total'),
            func.sum(case((PingResult.status == PingStatus.SUCCESS, 1), else_=0)).label('successful'),
            func.avg(PingResult.latency_ms).label('avg_latency'),
            func.max(PingResult.latency_ms).label('max_latency'),
            func.min(PingResult.latency_ms).label('min_latency'),
            func.avg(PingResult.packet_loss_percent).label('avg_packet_loss'),
            func.avg(PingResult.jitter_ms).label('avg_jitter'),
        ).where(
            PingResult.device_id == device_id,
            PingResult.timestamp >= since
        )
    )
    stats = stats_result.one()
    
    total = stats.total or 0
    successful = stats.successful or 0
    
    return PingStats(
        device_id=device_id,
        total_pings=total,
        successful_pings=int(successful),
        failed_pings=total - int(successful),
        availability=(successful / total * 100) if total > 0 else 100.0,
        avg_latency=float(stats.avg_latency) if stats.avg_latency else None,
        max_latency=float(stats.max_latency) if stats.max_latency else None,
        min_latency=float(stats.min_latency) if stats.min_latency else None,
        avg_packet_loss=float(stats.avg_packet_loss) if stats.avg_packet_loss else None,
        avg_jitter=float(stats.avg_jitter) if stats.avg_jitter else None,
        start_time=since,
        end_time=now
    )


@router.get("/device/{device_id}/live")
async def get_live_device_status(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get latest live ping status for a device."""
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.is_deleted == False)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get last 10 ping results
    ping_result = await db.execute(
        select(PingResult).where(PingResult.device_id == device_id)
        .order_by(PingResult.timestamp.desc()).limit(10)
    )
    recent_pings = ping_result.scalars().all()
    
    return {
        "device": {
            "id": device.id,
            "hostname": device.hostname,
            "ip_address": device.ip_address,
            "status": device.status.value if device.status else "unknown",
            "current_latency": device.current_latency,
            "current_packet_loss": device.current_packet_loss,
            "current_jitter": device.current_jitter,
            "response_time": device.current_response_time,
            "last_response": device.last_response.isoformat() if device.last_response else None,
            "last_down_time": device.last_down_time.isoformat() if device.last_down_time else None,
            "sla_24h": device.sla_24h,
            "sla_7d": device.sla_7d,
        },
        "recent_pings": [
            {
                "timestamp": p.timestamp.isoformat(),
                "status": p.status.value,
                "latency": p.latency_ms,
                "packet_loss": p.packet_loss_percent,
            }
            for p in recent_pings
        ],
        "color": "green" if device.status == DeviceStatus.UP else "red" if device.status == DeviceStatus.DOWN else "yellow"
    }

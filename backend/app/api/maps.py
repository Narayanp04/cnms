"""ConnectXperts NMS - Maps API"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, Role
from app.models.device import Device, DeviceStatus
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/v1/maps", tags=["Maps"])


@router.get("/devices")
async def get_map_devices(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get device locations for map display with status colors."""
    query = select(Device).where(
        Device.is_deleted == False,
        Device.latitude.isnot(None),
        Device.longitude.isnot(None)
    )
    
    if current_user.role != Role.ADMIN and current_user.customer_id:
        query = query.where(Device.customer_id == current_user.customer_id)
    
    result = await db.execute(query)
    devices = result.scalars().all()
    
    features = []
    for d in devices:
        # Color coding
        if d.status == DeviceStatus.UP:
            color = "#22c55e"  # Green
            status_text = "UP"
        elif d.status == DeviceStatus.DOWN:
            color = "#ef4444"  # Red
            status_text = "DOWN"
        elif d.status == DeviceStatus.WARNING:
            color = "#eab308"  # Yellow
            status_text = "Warning"
        else:
            color = "#6b7280"  # Gray
            status_text = "Unknown"
        
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [d.longitude, d.latitude]
            },
            "properties": {
                "id": d.id,
                "hostname": d.hostname,
                "display_name": d.display_name or d.hostname,
                "ip_address": d.ip_address,
                "status": status_text,
                "color": color,
                "latency": f"{d.current_latency}ms" if d.current_latency else "N/A",
                "packet_loss": f"{d.current_packet_loss}%" if d.current_packet_loss else "N/A",
                "customer": d.customer_name or "N/A",
                "site": d.site_name or "N/A",
                "region": d.region or "N/A",
                "provider": d.provider or "N/A",
                "circuit_id": d.circuit_id or "N/A",
                "sla_24h": f"{d.sla_24h:.2f}%",
            }
        })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }


@router.get("/heatmap")
async def get_heatmap_data(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get heatmap data for latency visualization."""
    query = select(Device).where(
        Device.is_deleted == False,
        Device.latitude.isnot(None),
        Device.longitude.isnot(None),
        Device.current_latency.isnot(None)
    )
    
    if current_user.role != Role.ADMIN and current_user.customer_id:
        query = query.where(Device.customer_id == current_user.customer_id)
    
    result = await db.execute(query)
    devices = result.scalars().all()
    
    # Normalize latency for heatmap intensity (0-1)
    latencies = [d.current_latency for d in devices if d.current_latency]
    max_latency = max(latencies) if latencies else 1
    
    points = []
    for d in devices:
        if d.current_latency:
            intensity = min(d.current_latency / max_latency, 1.0)
            points.append({
                "lat": d.latitude,
                "lng": d.longitude,
                "intensity": round(intensity, 3),
                "latency": d.current_latency,
                "hostname": d.hostname
            })
    
    return {"points": points}

"""ConnectXperts NMS - AI Analysis API"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User, Role
from app.models.device import Device
from app.services.ai_service import AIService
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/v1/ai", tags=["AI Analysis"])
ai_service = AIService()


@router.get("/device/{device_id}")
async def analyze_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get AI-powered analysis for a specific device."""
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.is_deleted == False)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if current_user.role != Role.ADMIN and current_user.customer_id:
        if device.customer_id != current_user.customer_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    analysis = await ai_service.analyze_device(device_id)
    return analysis


@router.get("/summary")
async def get_ai_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get AI summary for all monitored devices."""
    query = select(Device).where(
        Device.is_monitoring_enabled == True,
        Device.is_deleted == False
    )
    
    if current_user.role != Role.ADMIN and current_user.customer_id:
        query = query.where(Device.customer_id == current_user.customer_id)
    
    result = await db.execute(query)
    devices = result.scalars().all()
    
    summaries = []
    for device in devices:
        analysis = await ai_service.analyze_device(device.id)
        summaries.append({
            "device_id": device.id,
            "hostname": device.hostname,
            "ip_address": device.ip_address,
            "health_score": analysis.get("health_scores", {}).get("overall_health", "unknown"),
            "isp_grade": analysis.get("isp_quality_score", {}).get("grade", "N/A"),
            "failure_risk": analysis.get("predictions", {}).get("failure_risk", "low"),
            "summary": analysis.get("ai_summary", "Analysis not available")
        })
    
    return {"devices_analyzed": len(summaries), "summaries": summaries}


@router.get("/isp-quality/{device_id}")
async def get_isp_quality(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ISP quality score for a device."""
    analysis = await ai_service.analyze_device(device_id)
    return analysis.get("isp_quality_score", {})


@router.get("/health-score/{device_id}")
async def get_device_health(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get device health and network stability scores."""
    analysis = await ai_service.analyze_device(device_id)
    return analysis.get("health_scores", {})

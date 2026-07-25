"""ConnectXperts NMS - Alert Management API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User, Role
from app.models.alert import (
    Alert, AlertRecipient, AlertGroup, AlertHistory,
    AlertStatus, AlertType
)
from app.models.device import Device
from app.schemas.alert import (
    AlertResponse, AlertRecipientCreate, AlertRecipientResponse,
    AlertGroupCreate, AlertGroupResponse, AlertAcknowledgeRequest
)
from app.services.alert_service import AlertService
from app.utils.security import get_current_user, check_role_permissions

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])
alert_service = AlertService()


@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    alert_type: Optional[str] = None,
    device_id: Optional[int] = None,
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List alerts with filters."""
    query = select(Alert).options(selectinload(Alert.device))
    
    if current_user.role != Role.ADMIN and current_user.customer_id:
        query = query.where(
            Alert.device_id.in_(
                select(Device.id).where(Device.customer_id == current_user.customer_id)
            )
        )
    
    if status:
        query = query.where(Alert.status == status)
    if severity:
        query = query.where(Alert.severity == severity)
    if alert_type:
        query = query.where(Alert.alert_type == alert_type)
    if device_id:
        query = query.where(Alert.device_id == device_id)
    
    query = query.order_by(desc(Alert.triggered_at)).limit(limit)
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return [
        AlertResponse(
            **{k: getattr(a, k) for k in AlertResponse.model_fields.keys() if hasattr(a, k)},
            device_hostname=a.device.hostname if a.device else None,
            device_ip=a.device.ip_address if a.device else None
        )
        for a in alerts
    ]


@router.get("/unresolved", response_model=List[AlertResponse])
async def get_unresolved_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all unresolved alerts."""
    query = select(Alert).options(selectinload(Alert.device)).where(
        Alert.status.in_([AlertStatus.TRIGGERED, AlertStatus.ACKNOWLEDGED]),
        Alert.is_recovered == False
    )
    
    if current_user.role != Role.ADMIN and current_user.customer_id:
        query = query.where(
            Alert.device_id.in_(
                select(Device.id).where(Device.customer_id == current_user.customer_id)
            )
        )
    
    query = query.order_by(desc(Alert.triggered_at))
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return [
        AlertResponse(
            **{k: getattr(a, k) for k in AlertResponse.model_fields.keys() if hasattr(a, k)},
            device_hostname=a.device.hostname if a.device else None,
            device_ip=a.device.ip_address if a.device else None
        )
        for a in alerts
    ]


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge an alert."""
    await alert_service.acknowledge_alert(alert_id, current_user.id)
    return {"message": "Alert acknowledged"}


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role_permissions([Role.ADMIN, Role.OPERATOR]))
):
    """Manually resolve an alert."""
    await alert_service.resolve_alert(alert_id, current_user.id)
    return {"message": "Alert resolved"}


@router.get("/groups", response_model=List[AlertGroupResponse])
async def list_alert_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List alert groups."""
    result = await db.execute(select(AlertGroup))
    groups = result.scalars().all()
    return [AlertGroupResponse.model_validate(g) for g in groups]


@router.post("/groups", response_model=AlertGroupResponse)
async def create_alert_group(
    group_data: AlertGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """Create alert group."""
    group = AlertGroup(**group_data.model_dump())
    db.add(group)
    await db.flush()
    return AlertGroupResponse.model_validate(group)


@router.post("/recipients", response_model=AlertRecipientResponse)
async def create_alert_recipient(
    recipient_data: AlertRecipientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """Create alert recipient."""
    recipient = AlertRecipient(**recipient_data.model_dump())
    db.add(recipient)
    await db.flush()
    return AlertRecipientResponse.model_validate(recipient)


@router.get("/history", response_model=List)
async def get_alert_history(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get delivery history for an alert."""
    result = await db.execute(
        select(AlertHistory).where(AlertHistory.alert_id == alert_id)
        .order_by(AlertHistory.sent_at.desc())
    )
    return result.scalars().all()

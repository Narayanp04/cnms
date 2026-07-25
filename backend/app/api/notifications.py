"""ConnectXperts NMS - Notification Management API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.user import User, Role
from app.models.notification import NotificationHistory
from app.schemas.notification import NotificationHistoryResponse, WhatsAppTestMessage
from app.services.whatsapp_service import WhatsAppService
from app.utils.security import get_current_user, check_role_permissions

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get("/history", response_model=List[NotificationHistoryResponse])
async def get_notification_history(
    channel: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notification delivery history."""
    query = select(NotificationHistory)
    
    if channel:
        query = query.where(NotificationHistory.channel == channel)
    if status:
        query = query.where(NotificationHistory.status == status)
    
    query = query.order_by(desc(NotificationHistory.sent_at)).limit(limit)
    result = await db.execute(query)
    notifications = result.scalars().all()
    
    return [NotificationHistoryResponse.model_validate(n) for n in notifications]


@router.post("/whatsapp/test")
async def test_whatsapp_message(
    message: WhatsAppTestMessage,
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """Send a test WhatsApp message."""
    whatsapp = WhatsAppService()
    result = await whatsapp.send_message(message.phone, message.message)
    
    if not result or result.get("status") != "sent":
        raise HTTPException(status_code=500, detail="Failed to send WhatsApp message")
    
    return {"message": "Test WhatsApp message sent successfully", "details": result}


@router.get("/stats")
async def get_notification_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get notification statistics."""
    from sqlalchemy import func
    
    result = await db.execute(
        select(
            func.count(NotificationHistory.id).label('total'),
            NotificationHistory.channel,
            NotificationHistory.status,
            func.count(NotificationHistory.id).label('count')
        ).group_by(NotificationHistory.channel, NotificationHistory.status)
    )
    rows = result.all()
    
    stats = {}
    for row in rows:
        if row.channel not in stats:
            stats[row.channel] = {"total": 0, "sent": 0, "delivered": 0, "failed": 0}
        stats[row.channel]["total"] += row.count
        if row.status in stats[row.channel]:
            stats[row.channel][row.status] = row.count
    
    return stats

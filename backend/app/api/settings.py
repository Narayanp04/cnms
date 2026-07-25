"""ConnectXperts NMS - Settings API"""
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, Role
from app.models.alert import AlertRecipient
from app.schemas.alert import AlertConfigUpdate
from app.schemas.notification import WhatsAppConfig
from app.utils.security import get_current_user, check_role_permissions
from app.services.whatsapp_service import WhatsAppService

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])


@router.get("/system")
async def get_system_settings(
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """Get system configuration settings."""
    from app.config import settings
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "sla_target": settings.SLA_TARGET_PERCENTAGE,
        "high_latency_threshold": settings.HIGH_LATENCY_THRESHOLD,
        "critical_latency_threshold": settings.CRITICAL_LATENCY_THRESHOLD,
        "high_packet_loss_threshold": settings.HIGH_PACKET_LOSS_THRESHOLD,
        "critical_packet_loss_threshold": settings.CRITICAL_PACKET_LOSS_THRESHOLD,
        "alert_cooldown_seconds": settings.ALERT_COOLDOWN_SECONDS,
        "ping_timeout": settings.PING_TIMEOUT,
        "ping_count": settings.PING_COUNT,
        "ping_threads": settings.PING_THREADS,
        "history_retention_days": settings.HISTORY_RETENTION_DAYS,
        "auto_backup_enabled": settings.AUTO_BACKUP_ENABLED,
        "auto_backup_interval_hours": settings.AUTO_BACKUP_INTERVAL_HOURS,
        "backup_retention_days": settings.BACKUP_RETENTION_DAYS,
    }


@router.get("/notifications")
async def get_notification_settings(
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """Get notification configuration."""
    from app.config import settings
    return {
        "whatsapp_configured": bool(settings.WHATSAPP_PHONE_NUMBER_ID and settings.WHATSAPP_ACCESS_TOKEN),
        "email_configured": bool(settings.SMTP_HOST and settings.SMTP_USER),
        "telegram_configured": bool(settings.TELEGRAM_BOT_TOKEN),
    }


@router.post("/notifications/whatsapp/test")
async def test_whatsapp(
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """Test WhatsApp API connection."""
    whatsapp = WhatsAppService()
    result = await whatsapp.test_connection()
    return {"success": result, "message": "WhatsApp API connected" if result else "WhatsApp API connection failed"}

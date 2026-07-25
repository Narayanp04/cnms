"""ConnectXperts NMS - Alert Service"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from sqlalchemy import select, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.database import AsyncSessionLocal
from app.models.alert import (
    Alert, AlertRecipient, AlertGroup, AlertHistory, 
    AlertStatus, AlertSeverity, AlertType, AlertChannel
)
from app.models.device import Device
from app.models.event_log import EventLog, EventType
from app.models.notification import NotificationHistory, DeliveryStatus, NotificationChannel
from app.config import settings
from app.services.whatsapp_service import WhatsAppService
from app.services.email_service import EmailService
from app.services.telegram_service import TelegramService
from app.services.webhook_service import WebhookService

logger = logging.getLogger(__name__)


class AlertService:
    """Service for managing alerts and notifications."""
    
    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.email_service = EmailService()
        self.telegram_service = TelegramService()
        self.webhook_service = WebhookService()
    
    async def send_alert_notifications(self, alert_id: int):
        """Send alert notifications through all configured channels."""
        async with AsyncSessionLocal() as db:
            try:
                # Get alert
                result = await db.execute(
                    select(Alert).where(Alert.id == alert_id)
                )
                alert = result.scalar_one_or_none()
                if not alert:
                    logger.error(f"Alert {alert_id} not found")
                    return
                
                # Get device info
                device_result = await db.execute(
                    select(Device).where(Device.id == alert.device_id)
                )
                device = device_result.scalar_one_or_none()
                
                # Get all active recipients
                recipients_result = await db.execute(
                    select(AlertRecipient).where(
                        AlertRecipient.is_active == True
                    )
                )
                recipients = recipients_result.scalars().all()
                
                if not recipients:
                    logger.info("No alert recipients configured")
                    return
                
                # Send notifications through each channel
                for recipient in recipients:
                    await self._send_to_recipient(db, alert, device, recipient)
                    
                logger.info(f"Alert {alert_id} notifications sent to {len(recipients)} recipients")
                
            except Exception as e:
                logger.error(f"Error sending alert notifications: {str(e)}")
    
    async def _send_to_recipient(
        self, db: AsyncSession, alert: Alert, device: Device, recipient: AlertRecipient
    ):
        """Send alert to a single recipient through configured channels."""
        message_text = self._format_alert_message(alert, device)
        
        # WhatsApp
        if recipient.whatsapp_enabled and recipient.phone:
            await self._send_channel_notification(
                db, alert, device, recipient,
                NotificationChannel.WHATSAPP, recipient.phone,
                self.whatsapp_service.send_message, message_text
            )
        
        # Email
        if recipient.email_enabled and recipient.email:
            await self._send_channel_notification(
                db, alert, device, recipient,
                NotificationChannel.EMAIL, recipient.email,
                self.email_service.send_email, 
                alert.title, message_text, recipient.email
            )
        
        # Telegram
        if recipient.telegram_enabled and recipient.telegram_chat_id:
            await self._send_channel_notification(
                db, alert, device, recipient,
                NotificationChannel.TELEGRAM, recipient.telegram_chat_id,
                self.telegram_service.send_message, message_text
            )
        
        # Webhook
        if recipient.webhook_enabled and recipient.webhook_url:
            await self._send_channel_notification(
                db, alert, device, recipient,
                NotificationChannel.WEBHOOK, recipient.webhook_url,
                self.webhook_service.send_webhook,
                {"alert": alert.title, "message": message_text, "severity": alert.severity.value}
            )
    
    async def _send_channel_notification(
        self, db: AsyncSession, alert: Alert, device: Device,
        recipient: AlertRecipient, channel: NotificationChannel,
        target: str, send_func, *args, **kwargs
    ):
        """Send notification through a specific channel and track it."""
        try:
            result = await send_func(*args, **kwargs)
            
            notification = NotificationHistory(
                alert_id=alert.id,
                channel=channel,
                recipient=target,
                recipient_name=recipient.name,
                message_type="text",
                message_title=alert.title,
                message_body=self._format_alert_message(alert, device),
                status=DeliveryStatus.SENT if result else DeliveryStatus.FAILED,
                provider_message_id=result.get('message_id') if isinstance(result, dict) else None,
                sent_at=datetime.now(timezone.utc)
            )
            db.add(notification)
            
            # Add to alert history
            alert_history = AlertHistory(
                alert_id=alert.id,
                channel=AlertChannel[channel.value.upper()],
                recipient=target,
                status="sent" if result else "failed",
                message_id=notification.provider_message_id,
                sent_at=datetime.now(timezone.utc)
            )
            db.add(alert_history)
            
            await db.flush()
            
        except Exception as e:
            logger.error(f"Failed to send {channel.value} notification to {target}: {str(e)}")
            
            notification = NotificationHistory(
                alert_id=alert.id,
                channel=channel,
                recipient=target,
                recipient_name=recipient.name,
                message_type="text",
                message_title=alert.title,
                status=DeliveryStatus.FAILED,
                error_message=str(e),
                retry_count=0,
                sent_at=datetime.now(timezone.utc)
            )
            db.add(notification)
            await db.flush()
    
    def _format_alert_message(self, alert: Alert, device: Device) -> str:
        """Format alert message for notifications."""
        if alert.alert_type == AlertType.RECOVERY:
            return (
                f"🟢 Device Restored\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📌 Site: {device.site_name or 'N/A'}\n"
                f"👤 Customer: {device.customer_name or 'N/A'}\n"
                f"🌐 IP: {device.ip_address}\n"
                f"⏰ Time: {alert.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if alert.resolved_at else 'N/A'}\n"
                f"⏱ Downtime Duration: {self._format_duration(alert.downtime_duration_seconds)}\n"
                f"📊 Latency: {alert.latency_ms or 'N/A'}ms\n"
                f"📉 Packet Loss: {alert.packet_loss_percent or 'N/A'}%"
            )
        
        return (
            f"🔴 Device Down Alert\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📌 Site: {device.site_name or 'N/A'}\n"
            f"👤 Customer: {device.customer_name or 'N/A'}\n"
            f"🌐 IP: {device.ip_address}\n"
            f"⏰ Time: {alert.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📊 Latency: {alert.latency_ms or 'N/A'}ms\n"
            f"📉 Packet Loss: {alert.packet_loss_percent or 'N/A'}%\n"
            f"🔌 Circuit: {device.circuit_id or 'N/A'}\n"
            f"🏢 Provider: {device.provider or 'N/A'}"
        )
    
    def _format_duration(self, seconds: Optional[int]) -> str:
        """Format duration in seconds to human readable string."""
        if not seconds:
            return "N/A"
        
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        parts = []
        if days > 0: parts.append(f"{days}d")
        if hours > 0: parts.append(f"{hours}h")
        if minutes > 0: parts.append(f"{minutes}m")
        if secs > 0 or not parts: parts.append(f"{secs}s")
        
        return " ".join(parts)
    
    async def resolve_alert(self, alert_id: int, user_id: Optional[int] = None):
        """Resolve an alert (device recovered)."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Alert).where(Alert.id == alert_id)
            )
            alert = result.scalar_one_or_none()
            if not alert:
                return
            
            now = datetime.now(timezone.utc)
            
            # Calculate downtime
            if alert.triggered_at:
                downtime = (now - alert.triggered_at).total_seconds()
                alert.downtime_duration_seconds = int(downtime)
            
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = now
            alert.is_recovered = True
            
            # Create recovery alert
            device_result = await db.execute(
                select(Device).where(Device.id == alert.device_id)
            )
            device = device_result.scalar_one_or_none()
            
            recovery_alert = Alert(
                device_id=alert.device_id,
                alert_type=AlertType.RECOVERY,
                severity=AlertSeverity.INFO,
                status=AlertStatus.RESOLVED,
                title=f"🟢 Device Restored - {device.hostname if device else 'Unknown'}",
                message=self._format_alert_message(alert, device),
                triggered_at=now,
                resolved_at=now,
                is_recovered=True,
                downtime_duration_seconds=alert.downtime_duration_seconds,
                recovery_alert_id=alert.id
            )
            db.add(recovery_alert)
            
            await db.flush()
            
            # Send recovery notifications
            await self.send_alert_notifications(recovery_alert.id)
    
    async def acknowledge_alert(self, alert_id: int, user_id: int):
        """Acknowledge an alert."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Alert).where(Alert.id == alert_id)
            )
            alert = result.scalar_one_or_none()
            if alert:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.now(timezone.utc)
                alert.acknowledged_by = user_id
                await db.flush()
    
    async def get_active_alerts(self, db: AsyncSession) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        result = await db.execute(
            select(Alert).where(
                Alert.status.in_([AlertStatus.TRIGGERED, AlertStatus.ACKNOWLEDGED]),
                Alert.is_recovered == False
            ).order_by(Alert.triggered_at.desc())
        )
        return result.scalars().all()
    
    async def get_recent_alerts(self, db: AsyncSession, limit: int = 50) -> List[Alert]:
        """Get recent alerts."""
        result = await db.execute(
            select(Alert).order_by(Alert.triggered_at.desc()).limit(limit)
        )
        return result.scalars().all()

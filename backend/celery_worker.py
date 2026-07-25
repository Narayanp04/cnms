"""ConnectXperts NMS - Celery Worker for Background Tasks"""
import logging
from datetime import datetime, timezone, timedelta
from celery import Celery
from celery.schedules import crontab

from app.config import settings
from app.database import sync_engine
from app.models.device import Device, DeviceStatus
from app.models.ping_result import PingResult, PingStatus
from app.models.alert import Alert, AlertStatus, AlertType, AlertSeverity
from app.models.event_log import EventLog, EventType
from app.models.sla_report import SLAReport, SLAReportPeriod
from app.services.sla_service import SLAService
from app.services.backup_service import BackupService
from app.utils.ping import ping_device_sync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "cnms_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["celery_worker"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
)


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks."""
    # SLA calculation - every hour
    sender.add_periodic_task(3600.0, calculate_sla.s(), name="calculate-sla-hourly")
    
    # Daily report generation - midnight
    sender.add_periodic_task(
        crontab(hour=0, minute=30),
        generate_daily_reports.s(),
        name="generate-daily-reports"
    )
    
    # Weekly report - Sunday midnight
    sender.add_periodic_task(
        crontab(hour=1, minute=0, day_of_week=0),
        generate_daily_reports.s(period="weekly"),
        name="generate-weekly-reports"
    )
    
    # Monthly report - 1st of month
    sender.add_periodic_task(
        crontab(hour=2, minute=0, day_of_month=1),
        generate_daily_reports.s(period="monthly"),
        name="generate-monthly-reports"
    )
    
    # Database backup - every 24 hours
    if settings.AUTO_BACKUP_ENABLED:
        sender.add_periodic_task(
            settings.AUTO_BACKUP_INTERVAL_HOURS * 3600,
            create_database_backup.s(),
            name="create-database-backup"
        )
    
    # Cleanup old ping history - daily
    sender.add_periodic_task(
        crontab(hour=3, minute=0),
        cleanup_old_data.s(),
        name="cleanup-old-data"
    )


@celery_app.task(bind=True, max_retries=3)
def ping_device_task(self, device_id: int, ip_address: str, ping_timeout: float = 5.0, ping_count: int = 4):
    """Task to ping a single device."""
    from sqlalchemy.orm import Session, sessionmaker
    from sqlalchemy import select
    
    SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)
    session = SessionLocal()
    
    try:
        # Ping the device
        result = ping_device_sync(ip_address, timeout=ping_timeout, count=ping_count)
        now = datetime.now(timezone.utc)
        
        # Get device
        device = session.query(Device).filter(Device.id == device_id).first()
        if not device:
            logger.error(f"Device {device_id} not found")
            return {"error": "Device not found"}
        
        # Create ping result
        ping_result = PingResult(
            device_id=device_id,
            status=PingStatus.SUCCESS if result['status'] == 'success' else PingStatus.FAILURE,
            latency_ms=result.get('latency_ms'),
            packet_loss_percent=result.get('packet_loss_percent'),
            jitter_ms=result.get('jitter_ms'),
            response_time_ms=result.get('response_time_ms'),
            rtt_min=result.get('rtt_min'),
            rtt_max=result.get('rtt_max'),
            rtt_avg=result.get('rtt_avg'),
            error_message=result.get('error_message'),
            timestamp=now,
            monitored_by="celery"
        )
        session.add(ping_result)
        
        # Update device status
        old_status = device.status
        device.total_pings = (device.total_pings or 0) + 1
        
        if result['status'] == 'success':
            device.current_latency = result.get('latency_ms')
            device.current_packet_loss = result.get('packet_loss_percent')
            device.current_jitter = result.get('jitter_ms')
            device.last_response = now
            device.successful_pings = (device.successful_pings or 0) + 1
            device.status = DeviceStatus.UP
        else:
            device.status = DeviceStatus.DOWN
            device.failed_pings = (device.failed_pings or 0) + 1
            device.current_packet_loss = 100.0
        
        session.commit()
        
        return {
            "device_id": device_id,
            "status": result['status'],
            "latency_ms": result.get('latency_ms'),
            "packet_loss": result.get('packet_loss_percent'),
            "timestamp": now.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Ping task failed for device {device_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)
        
    finally:
        session.close()


@celery_app.task
def calculate_sla():
    """Calculate SLA for all devices."""
    from sqlalchemy.orm import Session, sessionmaker
    
    SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)
    session = SessionLocal()
    
    try:
        sla_service = SLAService()
        devices = session.query(Device).filter(
            Device.is_monitoring_enabled == True,
            Device.is_deleted == False
        ).all()
        
        now = datetime.now(timezone.utc)
        
        for device in devices:
            # Calculate SLA for different periods
            for period_name, delta_days in [
                ('sla_24h', 1), ('sla_7d', 7), 
                ('sla_30d', 30), ('sla_365d', 365)
            ]:
                since = now - timedelta(days=delta_days)
                
                total = session.query(PingResult).filter(
                    PingResult.device_id == device.id,
                    PingResult.timestamp >= since
                ).count()
                
                successful = session.query(PingResult).filter(
                    PingResult.device_id == device.id,
                    PingResult.timestamp >= since,
                    PingResult.status == PingStatus.SUCCESS
                ).count()
                
                sla = (successful / total * 100) if total > 0 else 100.0
                setattr(device, period_name, round(sla, 3))
            
            # Generate monthly SLA report
            period_start = now - timedelta(days=30)
            sla_report = SLAReport(
                device_id=device.id,
                customer_id=device.customer_id,
                period=SLAReportPeriod.DAILY,
                period_start=period_start,
                period_end=now,
                availability_percent=device.sla_30d or 100.0,
                uptime_seconds=0,
                downtime_seconds=0,
                total_pings=0,
                successful_pings=0,
                failed_pings=0,
                sla_target_percent=settings.SLA_TARGET_PERCENTAGE,
                sla_met=(device.sla_30d or 100.0) >= settings.SLA_TARGET_PERCENTAGE,
                generated_at=now
            )
            session.add(sla_report)
        
        session.commit()
        logger.info("SLA calculation completed for all devices")
        
    except Exception as e:
        logger.error(f"SLA calculation error: {str(e)}")
        session.rollback()
    finally:
        session.close()


@celery_app.task
def generate_daily_reports(period: str = "daily"):
    """Generate periodic reports."""
    import asyncio
    from app.services.report_service import ReportService
    
    report_service = ReportService()
    logger.info(f"Generating {period} reports...")
    
    try:
        # Use asyncio to run the async report generation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        if period == "daily":
            report_data = loop.run_until_complete(report_service.generate_daily_report())
        elif period == "weekly":
            report_data = loop.run_until_complete(report_service.generate_weekly_report())
        elif period == "monthly":
            report_data = loop.run_until_complete(report_service.generate_monthly_report())
        
        loop.close()
        logger.info(f"{period.title()} reports generated successfully")
        
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")


@celery_app.task
def create_database_backup():
    """Create automatic database backup."""
    backup_service = BackupService()
    filepath = backup_service.create_backup()
    
    if filepath:
        logger.info(f"Automatic backup created: {filepath}")
    else:
        logger.error("Automatic backup failed")


@celery_app.task
def cleanup_old_data():
    """Cleanup old ping history and event logs."""
    from sqlalchemy.orm import Session, sessionmaker
    
    SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)
    session = SessionLocal()
    
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.HISTORY_RETENTION_DAYS)
        
        # Clean old ping results
        old_pings = session.query(PingResult).filter(
            PingResult.timestamp < cutoff
        ).delete()
        
        # Keep event logs for 90 days
        event_cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        old_events = session.query(EventLog).filter(
            EventLog.timestamp < event_cutoff
        ).delete()
        
        session.commit()
        
        logger.info(f"Cleaned up {old_pings} old ping results and {old_events} old events")
        
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        session.rollback()
    finally:
        session.close()


@celery_app.task
def send_bulk_notifications():
    """Send pending notifications (retry logic)."""
    import asyncio
    from sqlalchemy.orm import Session, sessionmaker
    
    SessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False)
    session = SessionLocal()
    
    try:
        # Get failed notifications that need retry
        from app.models.notification import NotificationHistory, DeliveryStatus
        
        pending = session.query(NotificationHistory).filter(
            NotificationHistory.status.in_([
                DeliveryStatus.FAILED, DeliveryStatus.RETRYING
            ]),
            NotificationHistory.retry_count < NotificationHistory.max_retries
        ).all()
        
        for notification in pending:
            notification.retry_count += 1
            notification.status = DeliveryStatus.RETRYING
            
            # Attempt resend based on channel
            if notification.channel.value == "whatsapp":
                try:
                    import requests as sync_requests
                    url = f"{settings.WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
                    headers = {
                        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": notification.recipient,
                        "type": "text",
                        "text": {"body": notification.message_body or ""}
                    }
                    response = sync_requests.post(url, headers=headers, json=payload, timeout=30)
                    if response.status_code == 200:
                        notification.status = DeliveryStatus.SENT
                        notification.delivered_at = datetime.now(timezone.utc)
                except Exception as e:
                    logger.error(f"WhatsApp retry failed: {str(e)}")
            
            session.commit()
        
        logger.info(f"Retried {len(pending)} notifications")
        
    except Exception as e:
        logger.error(f"Notification retry error: {str(e)}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    celery_app.start()

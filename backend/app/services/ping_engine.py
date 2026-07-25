"""ConnectXperts NMS - Ping Monitoring Engine"""
import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional
from collections import defaultdict

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.database import AsyncSessionLocal, SyncSessionLocal
from app.models.device import Device, DeviceStatus, PollingInterval
from app.models.ping_result import PingResult, PingStatus
from app.models.event_log import EventLog, EventType
from app.models.alert import Alert, AlertType, AlertSeverity, AlertStatus
from app.config import settings
from app.utils.ping import async_ping_device, ping_device_sync

logger = logging.getLogger(__name__)


class PingEngine:
    """Multi-threaded ping monitoring engine."""
    
    def __init__(self):
        self._running = False
        self._tasks = {}
        self._ping_cache = {}
        self._device_status_cache = {}
    
    async def start_monitoring(self):
        """Start the monitoring engine."""
        self._running = True
        logger.info("Ping monitoring engine started")
        
        while self._running:
            try:
                await self._monitoring_cycle()
            except Exception as e:
                logger.error(f"Monitoring cycle error: {str(e)}")
            
            await asyncio.sleep(1)  # Check every second
    
    async def stop_monitoring(self):
        """Stop the monitoring engine."""
        self._running = False
        logger.info("Ping monitoring engine stopped")
    
    async def _monitoring_cycle(self):
        """Execute one monitoring cycle."""
        async with AsyncSessionLocal() as db:
            try:
                devices = await self._get_active_devices(db)
                
                if not devices:
                    await asyncio.sleep(5)
                    return
                
                # Group devices by polling interval
                interval_groups = defaultdict(list)
                for device in devices:
                    interval_seconds = self._get_interval_seconds(device.polling_interval)
                    interval_groups[interval_seconds].append(device)
                
                now = time.time()
                
                for interval, device_group in interval_groups.items():
                    # Check if it's time to poll this group
                    # Poll devices that are due
                    due_devices = []
                    for device in device_group:
                        last_ping_time = self._ping_cache.get(device.id, {}).get('timestamp', 0)
                        if now - last_ping_time >= interval:
                            due_devices.append(device)
                    
                    if not due_devices:
                        continue
                    
                    # Ping all due devices (limited concurrency)
                    semaphore = asyncio.Semaphore(settings.PING_THREADS)
                    
                    async def ping_with_semaphore(device):
                        async with semaphore:
                            return await self._ping_device(device)
                    
                    tasks = [ping_with_semaphore(d) for d in due_devices]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for device, result in zip(due_devices, results):
                        if isinstance(result, Exception):
                            logger.error(f"Ping error for {device.hostname}: {str(result)}")
                            continue
                        
                        await self._process_ping_result(db, device, result)
                
                # Update SLA stats periodically
                await self._update_sla_stats_if_needed(db)
                
            except Exception as e:
                logger.error(f"Monitoring cycle error: {str(e)}")
                await db.rollback()
    
    async def _get_active_devices(self, db: AsyncSession) -> List[Device]:
        """Get all active devices that should be monitored."""
        result = await db.execute(
            select(Device).where(
                Device.is_monitoring_enabled == True,
                Device.is_deleted == False
            )
        )
        return result.scalars().all()
    
    def _get_interval_seconds(self, interval: PollingInterval) -> int:
        """Convert polling interval enum to seconds."""
        mapping = {
            PollingInterval.FIVE_SEC: 5,
            PollingInterval.TEN_SEC: 10,
            PollingInterval.THIRTY_SEC: 30,
            PollingInterval.ONE_MIN: 60,
            PollingInterval.FIVE_MIN: 300,
        }
        return mapping.get(interval, 30)
    
    async def _ping_device(self, device: Device) -> Dict:
        """Ping a single device."""
        return await async_ping_device(
            ip_address=device.ip_address,
            timeout=device.ping_timeout,
            count=device.ping_count
        )
    
    async def _process_ping_result(self, db: AsyncSession, device: Device, result: Dict):
        """Process and store a ping result."""
        now = datetime.now(timezone.utc)
        timestamp = now.timestamp()
        
        # Update cache
        self._ping_cache[device.id] = {
            'timestamp': timestamp,
            'result': result
        }
        
        # Create ping result record
        ping_result = PingResult(
            device_id=device.id,
            status=PingStatus.SUCCESS if result['status'] == 'success' else PingStatus.FAILURE,
            latency_ms=result.get('latency_ms'),
            packet_loss_percent=result.get('packet_loss_percent'),
            jitter_ms=result.get('jitter_ms'),
            response_time_ms=result.get('response_time_ms'),
            rtt_min=result.get('rtt_min'),
            rtt_max=result.get('rtt_max'),
            rtt_avg=result.get('rtt_avg'),
            error_message=result.get('error_message'),
            timestamp=now
        )
        db.add(ping_result)
        
        # Determine device status
        old_status = device.status
        
        if result['status'] == 'success':
            latency = result.get('latency_ms', 0)
            packet_loss = result.get('packet_loss_percent', 0)
            
            if packet_loss > device.threshold_packet_loss_critical or latency > device.threshold_latency_critical:
                device.status = DeviceStatus.WARNING
            elif packet_loss > device.threshold_packet_loss_warning or latency > device.threshold_latency_warning:
                device.status = DeviceStatus.WARNING
            else:
                device.status = DeviceStatus.UP
            
            device.current_latency = latency
            device.current_packet_loss = packet_loss
            device.current_jitter = result.get('jitter_ms')
            device.current_response_time = result.get('response_time_ms')
            device.last_response = now
            device.successful_pings = (device.successful_pings or 0) + 1
            
        else:
            device.status = DeviceStatus.DOWN
            device.current_latency = None
            device.current_packet_loss = 100.0
            device.failed_pings = (device.failed_pings or 0) + 1
            device.last_down_time = now
        
        device.total_pings = (device.total_pings or 0) + 1
        
        # Check for status change
        if old_status != device.status:
            await self._handle_status_change(db, device, old_status, device.status, now)
        
        # Check for alerts
        if device.status == DeviceStatus.DOWN:
            await self._check_alert_conditions(db, device, result, now)
        
        # Log event
        event_log = EventLog(
            event_type=EventType.PING_RESULT,
            device_id=device.id,
            device_name=device.hostname,
            title=f"Ping {'Success' if result['status'] == 'success' else 'Failure'} - {device.hostname}",
            description=f"Latency: {result.get('latency_ms', 'N/A')}ms, Packet Loss: {result.get('packet_loss_percent', 100)}%",
            details=result,
            severity="info" if result['status'] == 'success' else "warning",
            timestamp=now
        )
        db.add(event_log)
        
        await db.flush()
    
    async def _handle_status_change(
        self, db: AsyncSession, device: Device,
        old_status: DeviceStatus, new_status: DeviceStatus, now: datetime
    ):
        """Handle device status change."""
        event_type = EventType.DEVICE_STATUS_CHANGE
        
        if new_status == DeviceStatus.DOWN:
            title = f"🔴 Device Down - {device.hostname}"
            severity = "critical"
        elif new_status == DeviceStatus.UP:
            title = f"🟢 Device Up - {device.hostname}"
            severity = "info"
        else:
            title = f"🟡 Device Warning - {device.hostname}"
            severity = "warning"
        
        event_log = EventLog(
            event_type=event_type,
            device_id=device.id,
            device_name=device.hostname,
            title=title,
            description=f"Status changed from {old_status.value} to {new_status.value}",
            details={
                "old_status": old_status.value,
                "new_status": new_status.value,
                "device_ip": device.ip_address,
                "customer": device.customer_name,
                "site": device.site_name,
            },
            severity=severity,
            timestamp=now
        )
        db.add(event_log)
        
        # Update uptime/downtime tracking
        if new_status == DeviceStatus.DOWN:
            device.last_down_time = now
        elif new_status == DeviceStatus.UP and old_status == DeviceStatus.DOWN:
            device.last_up_time = now
            if device.last_down_time:
                downtime = (now - device.last_down_time).total_seconds()
                device.total_downtime_seconds = (device.total_downtime_seconds or 0) + int(downtime)
    
    async def _check_alert_conditions(self, db: AsyncSession, device: Device, result: Dict, now: datetime):
        """Check if alert conditions are met."""
        from app.models.alert import Alert, AlertType, AlertSeverity, AlertStatus
        
        # Check if there's already an active alert for this device
        existing_alerts = await db.execute(
            select(Alert).where(
                Alert.device_id == device.id,
                Alert.status.in_([AlertStatus.TRIGGERED, AlertStatus.ACKNOWLEDGED]),
                Alert.is_recovered == False
            )
        )
        active_alert = existing_alerts.scalar_one_or_none()
        
        if active_alert:
            # Alert already active, check if it needs escalation
            time_since_trigger = (now - active_alert.triggered_at).total_seconds()
            if time_since_trigger > 600 and not active_alert.is_escalated:  # 10 minutes
                active_alert.is_escalated = True
                active_alert.escalation_count += 1
            return
        
        # Check alert cooldown
        recent_alerts = await db.execute(
            select(Alert).where(
                Alert.device_id == device.id,
                Alert.triggered_at > now.replace(second=now.second - settings.ALERT_COOLDOWN_SECONDS)
            )
        )
        if recent_alerts.scalar_one_or_none():
            return
        
        # Determine alert type and severity
        alert_type = AlertType.DEVICE_DOWN
        severity = AlertSeverity.CRITICAL
        title = f"🔴 Device Down - {device.hostname}"
        
        message = (
            f"🔴 Device Down Alert\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📌 Site: {device.site_name or 'N/A'}\n"
            f"👤 Customer: {device.customer_name or 'N/A'}\n"
            f"🌐 IP: {device.ip_address}\n"
            f"⏰ Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"📊 Latency: {result.get('latency_ms', 'N/A')}ms\n"
            f"📉 Packet Loss: {result.get('packet_loss_percent', 100)}%\n"
            f"🔌 Circuit: {device.circuit_id or 'N/A'}\n"
            f"🏢 Provider: {device.provider or 'N/A'}"
        )
        
        alert = Alert(
            device_id=device.id,
            alert_type=alert_type,
            severity=severity,
            status=AlertStatus.TRIGGERED,
            title=title,
            message=message,
            latency_ms=result.get('latency_ms'),
            packet_loss_percent=result.get('packet_loss_percent'),
            jitter_ms=result.get('jitter_ms'),
            triggered_at=now,
            is_recovered=False
        )
        db.add(alert)
        await db.flush()
    
    async def _update_sla_stats_if_needed(self, db: AsyncSession):
        """Update SLA statistics periodically."""
        from app.services.sla_service import SLAService
        
        sla_service = SLAService()
        await sla_service.update_device_sla_cache(db)
    
    def get_device_status(self, device_id: int) -> Optional[Dict]:
        """Get cached device status."""
        return self._ping_cache.get(device_id)
    
    def get_all_device_status(self) -> Dict[int, Dict]:
        """Get all cached device statuses."""
        return self._ping_cache.copy()


# Singleton instance
ping_engine = PingEngine()

"""ConnectXperts NMS - SLA Calculation Service"""
import logging
from datetime import datetime, timezone, timedelta, date
from typing import List, Optional, Dict
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.database import AsyncSessionLocal, SyncSessionLocal
from app.models.device import Device, DeviceStatus
from app.models.ping_result import PingResult, PingStatus
from app.models.sla_report import SLAReport, SLAReportPeriod
from app.models.event_log import EventLog, EventType
from app.config import settings

logger = logging.getLogger(__name__)


class SLAService:
    """Service for calculating and managing SLA metrics."""
    
    async def update_device_sla_cache(self, db: AsyncSession):
        """Update cached SLA values for all devices."""
        result = await db.execute(
            select(Device).where(Device.is_monitoring_enabled == True, Device.is_deleted == False)
        )
        devices = result.scalars().all()
        
        for device in devices:
            now = datetime.now(timezone.utc)
            
            device.sla_24h = await self._calculate_sla(db, device.id, now - timedelta(hours=24))
            device.sla_7d = await self._calculate_sla(db, device.id, now - timedelta(days=7))
            device.sla_30d = await self._calculate_sla(db, device.id, now - timedelta(days=30))
            device.sla_365d = await self._calculate_sla(db, device.id, now - timedelta(days=365))
        
        await db.flush()
    
    async def _calculate_sla(self, db: AsyncSession, device_id: int, since: datetime) -> float:
        """Calculate SLA percentage for a device since a given time."""
        result = await db.execute(
            select(
                func.count(PingResult.id).label('total'),
                func.sum(
                    case((PingResult.status == PingStatus.SUCCESS, 1), else_=0)
                ).label('successful')
            ).where(
                PingResult.device_id == device_id,
                PingResult.timestamp >= since
            )
        )
        row = result.one()
        total = row.total or 0
        successful = row.successful or 0
        
        if total == 0:
            return 100.0
        
        return round((successful / total) * 100, 3)
    
    async def generate_sla_report(
        self, db: AsyncSession,
        device_id: int, period: SLAReportPeriod,
        start: datetime, end: datetime
    ) -> Optional[SLAReport]:
        """Generate an SLA report for a device in a given period."""
        # Get device
        device_result = await db.execute(
            select(Device).where(Device.id == device_id)
        )
        device = device_result.scalar_one_or_none()
        if not device:
            return None
        
        # Get ping results for the period
        ping_result = await db.execute(
            select(
                func.count(PingResult.id).label('total'),
                func.sum(
                    case((PingResult.status == PingStatus.SUCCESS, 1), else_=0)
                ).label('successful'),
                func.avg(PingResult.latency_ms).label('avg_latency'),
                func.max(PingResult.latency_ms).label('max_latency'),
                func.min(PingResult.latency_ms).label('min_latency'),
                func.avg(PingResult.packet_loss_percent).label('avg_packet_loss'),
            ).where(
                PingResult.device_id == device_id,
                PingResult.timestamp >= start,
                PingResult.timestamp <= end
            )
        )
        stats = ping_result.one()
        
        total = stats.total or 0
        successful = stats.successful or 0
        availability = (successful / total * 100) if total > 0 else 100.0
        downtime_seconds = int((total - successful) * (settings.PING_TIMEOUT * 2)) if total > 0 else 0
        
        # Calculate outage events
        outage_events = await self._get_outage_events(db, device_id, start, end)
        
        report = SLAReport(
            device_id=device_id,
            customer_id=device.customer_id,
            period=period,
            period_start=start,
            period_end=end,
            availability_percent=round(availability, 3),
            uptime_seconds=int((availability / 100) * (end - start).total_seconds()) if total > 0 else 0,
            downtime_seconds=downtime_seconds,
            total_pings=total,
            successful_pings=int(successful or 0),
            failed_pings=total - int(successful or 0),
            avg_latency_ms=float(stats.avg_latency) if stats.avg_latency else None,
            max_latency_ms=float(stats.max_latency) if stats.max_latency else None,
            min_latency_ms=float(stats.min_latency) if stats.min_latency else None,
            avg_packet_loss_percent=float(stats.avg_packet_loss) if stats.avg_packet_loss else None,
            outage_count=len(outage_events),
            total_outage_duration=downtime_seconds,
            longest_outage_duration=max([e.get('duration', 0) for e in outage_events]) if outage_events else 0,
            outage_events=outage_events,
            sla_target_percent=settings.SLA_TARGET_PERCENTAGE,
            sla_met=availability >= settings.SLA_TARGET_PERCENTAGE,
            generated_at=datetime.now(timezone.utc)
        )
        
        db.add(report)
        await db.flush()
        
        # Log event
        event_log = EventLog(
            event_type=EventType.SLA_CALCULATED,
            device_id=device_id,
            device_name=device.hostname if device else None,
            title=f"SLA Report Generated - {device.hostname}",
            description=f"Period: {start.date()} to {end.date()}, Availability: {availability:.2f}%",
            details={
                "period": period.value,
                "availability": availability,
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            severity="info",
            timestamp=datetime.now(timezone.utc)
        )
        db.add(event_log)
        
        return report
    
    async def _get_outage_events(self, db: AsyncSession, device_id: int, start: datetime, end: datetime) -> List[Dict]:
        """Get outage events for a device in a given period."""
        # Find consecutive failure events
        results = await db.execute(
            select(PingResult).where(
                PingResult.device_id == device_id,
                PingResult.timestamp >= start,
                PingResult.timestamp <= end,
                PingResult.status == PingStatus.FAILURE
            ).order_by(PingResult.timestamp.asc())
        )
        failures = results.scalars().all()
        
        if not failures:
            return []
        
        # Group consecutive failures into outages
        outages = []
        current_outage = None
        
        for failure in failures:
            if current_outage is None:
                current_outage = {
                    'start': failure.timestamp.isoformat(),
                    'end': failure.timestamp.isoformat(),
                    'duration': 0,
                    'ping_count': 1
                }
            else:
                time_diff = (failure.timestamp - datetime.fromisoformat(current_outage['end']).replace(tzinfo=timezone.utc)).total_seconds()
                if time_diff <= 60:  # Within 60 seconds = same outage
                    current_outage['end'] = failure.timestamp.isoformat()
                    current_outage['ping_count'] += 1
                else:
                    # Calculate duration
                    start_dt = datetime.fromisoformat(current_outage['start'])
                    end_dt = datetime.fromisoformat(current_outage['end'])
                    current_outage['duration'] = int((end_dt - start_dt).total_seconds())
                    outages.append(current_outage)
                    current_outage = {
                        'start': failure.timestamp.isoformat(),
                        'end': failure.timestamp.isoformat(),
                        'duration': 0,
                        'ping_count': 1
                    }
        
        # Don't forget the last outage
        if current_outage:
            start_dt = datetime.fromisoformat(current_outage['start'])
            end_dt = datetime.fromisoformat(current_outage['end'])
            current_outage['duration'] = int((end_dt - start_dt).total_seconds())
            outages.append(current_outage)
        
        return outages
    
    async def generate_reports_for_all_devices(self, period: SLAReportPeriod):
        """Generate SLA reports for all devices."""
        async with AsyncSessionLocal() as db:
            now = datetime.now(timezone.utc)
            
            if period == SLAReportPeriod.DAILY:
                start = now - timedelta(days=1)
            elif period == SLAReportPeriod.WEEKLY:
                start = now - timedelta(weeks=1)
            elif period == SLAReportPeriod.MONTHLY:
                start = now - timedelta(days=30)
            else:  # YEARLY
                start = now - timedelta(days=365)
            
            result = await db.execute(
                select(Device).where(Device.is_monitoring_enabled == True, Device.is_deleted == False)
            )
            devices = result.scalars().all()
            
            for device in devices:
                try:
                    await self.generate_sla_report(db, device.id, period, start, now)
                except Exception as e:
                    logger.error(f"Error generating SLA report for device {device.hostname}: {str(e)}")
            
            await db.commit()

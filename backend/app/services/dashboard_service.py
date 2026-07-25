"""ConnectXperts NMS - Dashboard Service"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.device import Device, DeviceStatus
from app.models.ping_result import PingResult, PingStatus
from app.models.alert import Alert, AlertStatus, AlertType
from app.models.user import Customer
from app.schemas.dashboard import (
    DashboardStats, TopHighLatencyDevice, TopPacketLossDevice,
    RecentAlertWidget, DeviceAvailabilityWidget, SLAWidget,
    CustomerSummaryWidget, ISPProviderSummary, DashboardWidgetData
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for aggregating dashboard data."""
    
    async def get_dashboard_stats(self, db: AsyncSession, customer_id: Optional[int] = None) -> DashboardStats:
        """Get main dashboard statistics."""
        # Base query
        device_query = select(Device).where(Device.is_deleted == False)
        if customer_id:
            device_query = device_query.where(Device.customer_id == customer_id)
        
        result = await db.execute(device_query)
        devices = result.scalars().all()
        
        total = len(devices)
        up = sum(1 for d in devices if d.status == DeviceStatus.UP)
        down = sum(1 for d in devices if d.status == DeviceStatus.DOWN)
        warning = sum(1 for d in devices if d.status == DeviceStatus.WARNING)
        disabled = sum(1 for d in devices if d.status == DeviceStatus.DISABLED or not d.is_monitoring_enabled)
        
        # Average latency
        latencies = [d.current_latency for d in devices if d.current_latency is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else None
        
        # Average packet loss
        losses = [d.current_packet_loss for d in devices if d.current_packet_loss is not None]
        avg_loss = sum(losses) / len(losses) if losses else None
        
        # Average SLA
        sla_values = [d.sla_24h for d in devices if d.sla_24h is not None]
        avg_sla = sum(sla_values) / len(sla_values) if sla_values else 100.0
        
        # Recent alerts count (24h)
        now = datetime.now(timezone.utc)
        alert_query = select(func.count(Alert.id)).where(
            Alert.triggered_at >= now - timedelta(hours=24)
        )
        if customer_id:
            alert_query = alert_query.where(
                Alert.device_id.in_(
                    select(Device.id).where(Device.customer_id == customer_id)
                )
            )
        alert_result = await db.execute(alert_query)
        recent_alerts = alert_result.scalar() or 0
        
        # Unresolved alerts
        unresolved_query = select(func.count(Alert.id)).where(
            Alert.status.in_([AlertStatus.TRIGGERED, AlertStatus.ACKNOWLEDGED]),
            Alert.is_recovered == False
        )
        if customer_id:
            unresolved_query = unresolved_query.where(
                Alert.device_id.in_(
                    select(Device.id).where(Device.customer_id == customer_id)
                )
            )
        unresolved_result = await db.execute(unresolved_query)
        unresolved = unresolved_result.scalar() or 0
        
        # Customer count
        customer_query = select(func.count(Customer.id)).where(Customer.is_active == True)
        customer_result = await db.execute(customer_query)
        customer_count = customer_result.scalar() or 0
        
        # Monitored devices
        monitored = sum(1 for d in devices if d.is_monitoring_enabled and d.status != DeviceStatus.DISABLED)
        
        return DashboardStats(
            total_devices=total,
            up_devices=up,
            down_devices=down,
            warning_devices=warning,
            disabled_devices=disabled,
            average_latency=round(avg_latency, 2) if avg_latency else None,
            average_packet_loss=round(avg_loss, 2) if avg_loss else None,
            average_sla_percent=round(avg_sla, 3),
            last_updated=datetime.now(timezone.utc),
            new_alerts_24h=recent_alerts,
            unresolved_alerts=unresolved,
            total_customers=customer_count,
            monitored_devices=monitored
        )
    
    async def get_top_high_latency(self, db: AsyncSession, limit: int = 10, customer_id: Optional[int] = None) -> List[TopHighLatencyDevice]:
        """Get top devices by highest latency."""
        query = select(Device).where(
            Device.is_deleted == False,
            Device.current_latency.isnot(None),
            Device.is_monitoring_enabled == True
        )
        if customer_id:
            query = query.where(Device.customer_id == customer_id)
        
        query = query.order_by(Device.current_latency.desc()).limit(limit)
        result = await db.execute(query)
        devices = result.scalars().all()
        
        return [
            TopHighLatencyDevice(
                id=d.id,
                hostname=d.hostname,
                ip_address=d.ip_address,
                customer_name=d.customer_name,
                site_name=d.site_name,
                current_latency=d.current_latency,
                status=d.status.value
            )
            for d in devices
        ]
    
    async def get_top_packet_loss(self, db: AsyncSession, limit: int = 10, customer_id: Optional[int] = None) -> List[TopPacketLossDevice]:
        """Get top devices by highest packet loss."""
        query = select(Device).where(
            Device.is_deleted == False,
            Device.current_packet_loss.isnot(None),
            Device.is_monitoring_enabled == True
        )
        if customer_id:
            query = query.where(Device.customer_id == customer_id)
        
        query = query.order_by(Device.current_packet_loss.desc()).limit(limit)
        result = await db.execute(query)
        devices = result.scalars().all()
        
        return [
            TopPacketLossDevice(
                id=d.id,
                hostname=d.hostname,
                ip_address=d.ip_address,
                customer_name=d.customer_name,
                site_name=d.site_name,
                packet_loss=d.current_packet_loss,
                status=d.status.value
            )
            for d in devices
        ]
    
    async def get_recent_alerts(self, db: AsyncSession, limit: int = 10, customer_id: Optional[int] = None) -> List[RecentAlertWidget]:
        """Get most recent alerts."""
        query = select(Alert).options(selectinload(Alert.device))
        
        if customer_id:
            query = query.where(
                Alert.device_id.in_(
                    select(Device.id).where(Device.customer_id == customer_id)
                )
            )
        
        query = query.order_by(Alert.triggered_at.desc()).limit(limit)
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        return [
            RecentAlertWidget(
                id=a.id,
                device_id=a.device_id,
                device_hostname=a.device.hostname if a.device else None,
                device_ip=a.device.ip_address if a.device else None,
                alert_type=a.alert_type.value if a.alert_type else "",
                severity=a.severity.value if a.severity else "",
                title=a.title,
                status=a.status.value if a.status else "",
                triggered_at=a.triggered_at,
                is_recovered=a.is_recovered
            )
            for a in alerts
        ]
    
    async def get_device_availability(self, db: AsyncSession, customer_id: Optional[int] = None) -> DeviceAvailabilityWidget:
        """Get device availability summary."""
        query = select(Device).where(Device.is_deleted == False)
        if customer_id:
            query = query.where(Device.customer_id == customer_id)
        
        result = await db.execute(query)
        devices = result.scalars().all()
        
        total = len(devices)
        up = sum(1 for d in devices if d.status == DeviceStatus.UP)
        down = sum(1 for d in devices if d.status == DeviceStatus.DOWN)
        warning = sum(1 for d in devices if d.status == DeviceStatus.WARNING)
        disabled = sum(1 for d in devices if d.status == DeviceStatus.DISABLED or not d.is_monitoring_enabled)
        
        return DeviceAvailabilityWidget(
            total=total,
            up=up,
            down=down,
            warning=warning,
            disabled=disabled,
            up_percent=round((up / total) * 100, 1) if total > 0 else 0,
            down_percent=round((down / total) * 100, 1) if total > 0 else 0,
            warning_percent=round((warning / total) * 100, 1) if total > 0 else 0
        )
    
    async def get_sla_summary(self, db: AsyncSession, customer_id: Optional[int] = None) -> List[SLAWidget]:
        """Get SLA summary for all devices."""
        query = select(Device).where(
            Device.is_deleted == False,
            Device.is_monitoring_enabled == True
        )
        if customer_id:
            query = query.where(Device.customer_id == customer_id)
        
        query = query.order_by(Device.sla_24h.asc()).limit(20)
        result = await db.execute(query)
        devices = result.scalars().all()
        
        return [
            SLAWidget(
                device_id=d.id,
                hostname=d.hostname,
                customer_name=d.customer_name,
                sla_24h=d.sla_24h or 100.0,
                sla_7d=d.sla_7d or 100.0,
                sla_30d=d.sla_30d or 100.0,
                sla_365d=d.sla_365d or 100.0
            )
            for d in devices
        ]
    
    async def get_customer_summary(self, db: AsyncSession) -> List[CustomerSummaryWidget]:
        """Get summary for each customer."""
        result = await db.execute(
            select(Device.customer_id, Device.customer_name, func.count(Device.id).label('total'))
            .where(Device.is_deleted == False, Device.customer_name.isnot(None))
            .group_by(Device.customer_id, Device.customer_name)
        )
        rows = result.all()
        
        summaries = []
        for row in rows:
            devices_result = await db.execute(
                select(Device).where(
                    Device.customer_id == row.customer_id,
                    Device.is_deleted == False
                )
            )
            devices = devices_result.scalars().all()
            
            up = sum(1 for d in devices if d.status == DeviceStatus.UP)
            down = sum(1 for d in devices if d.status == DeviceStatus.DOWN)
            latencies = [d.current_latency for d in devices if d.current_latency]
            sla_values = [d.sla_24h for d in devices if d.sla_24h]
            
            summaries.append(CustomerSummaryWidget(
                customer_id=row.customer_id,
                customer_name=row.customer_name,
                total_devices=row.total,
                up_devices=up,
                down_devices=down,
                average_latency=round(sum(latencies) / len(latencies), 2) if latencies else None,
                average_sla=round(sum(sla_values) / len(sla_values), 2) if sla_values else 100.0
            ))
        
        return summaries
    
    async def get_isp_summary(self, db: AsyncSession) -> List[ISPProviderSummary]:
        """Get summary grouped by ISP provider."""
        result = await db.execute(
            select(Device.provider, func.count(Device.id).label('total'))
            .where(Device.is_deleted == False, Device.provider.isnot(None))
            .group_by(Device.provider)
        )
        rows = result.all()
        
        summaries = []
        for row in rows:
            devices_result = await db.execute(
                select(Device).where(
                    Device.provider == row.provider,
                    Device.is_deleted == False
                )
            )
            devices = devices_result.scalars().all()
            
            up = sum(1 for d in devices if d.status == DeviceStatus.UP)
            down = sum(1 for d in devices if d.status == DeviceStatus.DOWN)
            latencies = [d.current_latency for d in devices if d.current_latency]
            sla_values = [d.sla_24h for d in devices if d.sla_24h]
            
            summaries.append(ISPProviderSummary(
                provider=row.provider,
                total_devices=row.total,
                up_devices=up,
                down_devices=down,
                average_latency=round(sum(latencies) / len(latencies), 2) if latencies else None,
                average_sla=round(sum(sla_values) / len(sla_values), 2) if sla_values else 100.0
            ))
        
        return summaries
    
    async def get_full_dashboard(self, db: AsyncSession, customer_id: Optional[int] = None) -> DashboardWidgetData:
        """Get complete dashboard data with all widgets."""
        stats_task = self.get_dashboard_stats(db, customer_id)
        latency_task = self.get_top_high_latency(db, customer_id=customer_id)
        loss_task = self.get_top_packet_loss(db, customer_id=customer_id)
        alerts_task = self.get_recent_alerts(db, customer_id=customer_id)
        availability_task = self.get_device_availability(db, customer_id=customer_id)
        sla_task = self.get_sla_summary(db, customer_id=customer_id)
        customer_task = self.get_customer_summary(db) if not customer_id else None
        isp_task = self.get_isp_summary(db) if not customer_id else None
        
        import asyncio
        results = await asyncio.gather(
            stats_task, latency_task, loss_task, alerts_task,
            availability_task, sla_task,
            customer_task or asyncio.sleep(0),
            isp_task or asyncio.sleep(0)
        )
        
        return DashboardWidgetData(
            stats=results[0],
            top_high_latency=results[1],
            top_packet_loss=results[2],
            recent_alerts=results[3],
            device_availability=results[4],
            sla_summary=results[5],
            customer_summary=results[6] if not customer_id else [],
            isp_summary=results[7] if not customer_id else []
        )

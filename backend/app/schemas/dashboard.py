"""ConnectXperts NMS - Dashboard Schemas"""
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class DashboardStats(BaseModel):
    total_devices: int
    up_devices: int
    down_devices: int
    warning_devices: int
    disabled_devices: int
    average_latency: Optional[float] = None
    average_packet_loss: Optional[float] = None
    average_sla_percent: float = 100.0
    last_updated: datetime
    
    # Quick stats
    new_alerts_24h: int = 0
    unresolved_alerts: int = 0
    total_customers: int = 0
    monitored_devices: int = 0


class TopHighLatencyDevice(BaseModel):
    id: int
    hostname: str
    ip_address: str
    customer_name: Optional[str] = None
    site_name: Optional[str] = None
    current_latency: Optional[float] = None
    status: str


class TopPacketLossDevice(BaseModel):
    id: int
    hostname: str
    ip_address: str
    customer_name: Optional[str] = None
    site_name: Optional[str] = None
    packet_loss: Optional[float] = None
    status: str


class RecentAlertWidget(BaseModel):
    id: int
    device_id: int
    device_hostname: Optional[str] = None
    device_ip: Optional[str] = None
    alert_type: str
    severity: str
    title: str
    status: str
    triggered_at: datetime
    is_recovered: bool


class DeviceAvailabilityWidget(BaseModel):
    total: int
    up: int
    down: int
    warning: int
    disabled: int
    up_percent: float
    down_percent: float
    warning_percent: float


class SLAWidget(BaseModel):
    device_id: int
    hostname: str
    customer_name: Optional[str] = None
    sla_24h: float
    sla_7d: float
    sla_30d: float
    sla_365d: float


class CustomerSummaryWidget(BaseModel):
    customer_id: int
    customer_name: str
    total_devices: int
    up_devices: int
    down_devices: int
    average_latency: Optional[float] = None
    average_sla: float = 100.0


class ISPProviderSummary(BaseModel):
    provider: str
    total_devices: int
    up_devices: int
    down_devices: int
    average_latency: Optional[float] = None
    average_sla: float = 100.0


class DashboardWidgetData(BaseModel):
    stats: DashboardStats
    top_high_latency: List[TopHighLatencyDevice]
    top_packet_loss: List[TopPacketLossDevice]
    recent_alerts: List[RecentAlertWidget]
    device_availability: DeviceAvailabilityWidget
    sla_summary: List[SLAWidget]
    customer_summary: List[CustomerSummaryWidget]
    isp_summary: List[ISPProviderSummary]


class RegionSummary(BaseModel):
    region: str
    total: int
    up: int
    down: int
    warning: int
    avg_latency: Optional[float] = None

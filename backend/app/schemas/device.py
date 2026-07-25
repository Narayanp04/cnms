"""ConnectXperts NMS - Device Schemas"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models.device import DeviceStatus, PollingInterval


class DeviceTagSchema(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    color: str = "#6366f1"
    
    class Config:
        from_attributes = True


class DeviceCreate(BaseModel):
    hostname: str = Field(..., min_length=1, max_length=255)
    ip_address: str = Field(..., min_length=7, max_length=45)
    display_name: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    site_name: Optional[str] = None
    region: Optional[str] = None
    circuit_id: Optional[str] = None
    bandwidth: Optional[str] = None
    provider: Optional[str] = None
    category: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None
    polling_interval: PollingInterval = PollingInterval.THIRTY_SEC
    ping_timeout: float = 5.0
    ping_count: int = 4
    threshold_latency_warning: int = 150
    threshold_latency_critical: int = 300
    threshold_packet_loss_warning: float = 5.0
    threshold_packet_loss_critical: float = 20.0
    is_monitoring_enabled: bool = True
    notes: Optional[str] = None
    tags: Optional[List[DeviceTagSchema]] = None
    
    @validator('ip_address')
    def validate_ip(cls, v):
        import ipaddress
        try:
            ipaddress.ip_address(v)
        except ValueError:
            # Allow hostnames too
            if len(v) < 3:
                raise ValueError('Invalid IP address or hostname')
        return v


class DeviceUpdate(BaseModel):
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    display_name: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    site_name: Optional[str] = None
    region: Optional[str] = None
    circuit_id: Optional[str] = None
    bandwidth: Optional[str] = None
    provider: Optional[str] = None
    category: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None
    polling_interval: Optional[PollingInterval] = None
    is_monitoring_enabled: Optional[bool] = None
    notes: Optional[str] = None
    tags: Optional[List[DeviceTagSchema]] = None


class DeviceResponse(BaseModel):
    id: int
    hostname: str
    ip_address: str
    display_name: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    site_name: Optional[str] = None
    region: Optional[str] = None
    circuit_id: Optional[str] = None
    bandwidth: Optional[str] = None
    provider: Optional[str] = None
    category: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location: Optional[str] = None
    polling_interval: PollingInterval
    is_monitoring_enabled: bool
    status: DeviceStatus
    current_latency: Optional[float] = None
    current_packet_loss: Optional[float] = None
    current_jitter: Optional[float] = None
    current_response_time: Optional[float] = None
    last_response: Optional[datetime] = None
    last_down_time: Optional[datetime] = None
    last_up_time: Optional[datetime] = None
    sla_24h: float
    sla_7d: float
    sla_30d: float
    sla_365d: float
    total_pings: int
    successful_pings: int
    failed_pings: int
    notes: Optional[str] = None
    tags: Optional[List[DeviceTagSchema]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    total: int
    items: List[DeviceResponse]
    page: int = 1
    page_size: int = 20
    total_pages: int = 1


class BulkImportResult(BaseModel):
    total: int
    success: int
    failed: int
    errors: List[str] = []


class DeviceMapData(BaseModel):
    id: int
    hostname: str
    display_name: Optional[str] = None
    ip_address: str
    status: DeviceStatus
    latitude: float
    longitude: float
    current_latency: Optional[float] = None
    customer_name: Optional[str] = None
    site_name: Optional[str] = None

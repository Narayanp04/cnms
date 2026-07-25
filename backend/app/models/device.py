"""ConnectXperts NMS - Device Model"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class DeviceStatus(str, enum.Enum):
    UP = "up"
    DOWN = "down"
    WARNING = "warning"
    UNKNOWN = "unknown"
    DISABLED = "disabled"


class PollingInterval(str, enum.Enum):
    FIVE_SEC = "5s"
    TEN_SEC = "10s"
    THIRTY_SEC = "30s"
    ONE_MIN = "1m"
    FIVE_MIN = "5m"


class DeviceTag(Base):
    __tablename__ = "device_tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    color = Column(String(7), default="#6366f1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    devices = relationship("Device", secondary="device_tag_association", back_populates="tags")


class DeviceTagAssociation(Base):
    __tablename__ = "device_tag_association"
    
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("device_tags.id", ondelete="CASCADE"), primary_key=True)


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    display_name = Column(String(255))
    
    # Customer & Site Info
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    customer_name = Column(String(255), index=True)
    site_name = Column(String(255), index=True)
    region = Column(String(255), index=True)
    
    # Circuit Info
    circuit_id = Column(String(100), index=True)
    bandwidth = Column(String(50))
    provider = Column(String(255), index=True)
    category = Column(String(100), index=True)
    
    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location = Column(String(500))
    
    # Monitoring Configuration
    polling_interval = Column(Enum(PollingInterval), default=PollingInterval.THIRTY_SEC)
    ping_timeout = Column(Float, default=5.0)
    ping_count = Column(Integer, default=4)
    threshold_latency_warning = Column(Integer, default=150)
    threshold_latency_critical = Column(Integer, default=300)
    threshold_packet_loss_warning = Column(Float, default=5.0)
    threshold_packet_loss_critical = Column(Float, default=20.0)
    
    is_monitoring_enabled = Column(Boolean, default=True)
    is_monitored_24x7 = Column(Boolean, default=True)
    
    # Current Status
    status = Column(Enum(DeviceStatus), default=DeviceStatus.UNKNOWN)
    current_latency = Column(Float, nullable=True)
    current_packet_loss = Column(Float, nullable=True)
    current_jitter = Column(Float, nullable=True)
    current_response_time = Column(Float, nullable=True)
    last_response = Column(DateTime(timezone=True), nullable=True)
    last_down_time = Column(DateTime(timezone=True), nullable=True)
    last_up_time = Column(DateTime(timezone=True), nullable=True)
    
    # SLA Stats (cached)
    sla_24h = Column(Float, default=100.0)
    sla_7d = Column(Float, default=100.0)
    sla_30d = Column(Float, default=100.0)
    sla_365d = Column(Float, default=100.0)
    
    total_uptime_seconds = Column(Integer, default=0)
    total_downtime_seconds = Column(Integer, default=0)
    total_pings = Column(Integer, default=0)
    successful_pings = Column(Integer, default=0)
    failed_pings = Column(Integer, default=0)
    
    # Metadata
    notes = Column(Text)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="devices")
    ping_results = relationship(
        "PingResult",
        back_populates="device",
        lazy="dynamic",
        order_by="PingResult.timestamp.desc()"
    )
    tags = relationship(
        "DeviceTag",
        secondary="device_tag_association",
        back_populates="devices",
        lazy="selectin"
    )
    alerts = relationship("Alert", back_populates="device")
    event_logs = relationship("EventLog", back_populates="device")

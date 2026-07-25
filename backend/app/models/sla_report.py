"""ConnectXperts NMS - SLA Report Model"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum, Text, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class SLAReportPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SLAReport(Base):
    __tablename__ = "sla_reports"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Report Period
    period = Column(Enum(SLAReportPeriod), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    
    # SLA Metrics
    availability_percent = Column(Float, nullable=False)
    uptime_seconds = Column(Integer, default=0)
    downtime_seconds = Column(Integer, default=0)
    total_pings = Column(Integer, default=0)
    successful_pings = Column(Integer, default=0)
    failed_pings = Column(Integer, default=0)
    
    # Latency Metrics
    avg_latency_ms = Column(Float, nullable=True)
    max_latency_ms = Column(Float, nullable=True)
    min_latency_ms = Column(Float, nullable=True)
    avg_packet_loss_percent = Column(Float, nullable=True)
    
    # Outage Details
    outage_count = Column(Integer, default=0)
    total_outage_duration = Column(Integer, default=0)
    longest_outage_duration = Column(Integer, default=0)
    outage_events = Column(JSON, nullable=True)
    
    # SLA Target
    sla_target_percent = Column(Float, default=99.9)
    sla_met = Column(Boolean, default=True)
    
    # Metadata
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text)
    
    # Relationships
    device = relationship("Device")
    customer = relationship("Customer")
    
    def __repr__(self):
        return f"<SLAReport(device={self.device_id}, period={self.period}, availability={self.availability_percent:.2f}%)>"

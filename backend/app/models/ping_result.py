"""ConnectXperts NMS - Ping Result Model"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class PingStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"


class PingResult(Base):
    __tablename__ = "ping_results"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Ping Results
    status = Column(Enum(PingStatus), nullable=False, index=True)
    latency_ms = Column(Float, nullable=True)
    packet_loss_percent = Column(Float, nullable=True)
    jitter_ms = Column(Float, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    ttl = Column(Integer, nullable=True)
    packet_size = Column(Integer, nullable=True)
    rtt_min = Column(Float, nullable=True)
    rtt_max = Column(Float, nullable=True)
    rtt_avg = Column(Float, nullable=True)
    
    # Error Info
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    
    # Metadata
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    monitored_by = Column(String(100), default="system")
    is_alert_triggered = Column(Boolean, default=False)
    
    # Relationships
    device = relationship("Device", back_populates="ping_results")
    
    def __repr__(self):
        return f"<PingResult(device={self.device_id}, status={self.status}, latency={self.latency_ms})>"

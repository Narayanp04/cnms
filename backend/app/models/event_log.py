"""ConnectXperts NMS - Event Log Model"""
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Enum, Text, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class EventType(str, enum.Enum):
    PING_RESULT = "ping_result"
    ALERT_TRIGGERED = "alert_triggered"
    ALERT_RESOLVED = "alert_resolved"
    DEVICE_ADDED = "device_added"
    DEVICE_UPDATED = "device_updated"
    DEVICE_DELETED = "device_deleted"
    DEVICE_STATUS_CHANGE = "device_status_change"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    CONFIG_CHANGE = "config_change"
    SYSTEM_ERROR = "system_error"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    REPORT_GENERATED = "report_generated"
    SLA_CALCULATED = "sla_calculated"
    WHATSAPP_SENT = "whatsapp_sent"
    EMAIL_SENT = "email_sent"
    API_CALL = "api_call"
    CUSTOM = "custom"


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(Enum(EventType), nullable=False, index=True)
    
    # Who
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # What
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, index=True)
    device_name = Column(String(255))
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True)
    
    # Details
    title = Column(String(500))
    description = Column(Text)
    details = Column(JSON)
    severity = Column(String(20), default="info")  # info, warning, error, critical
    
    # Timing
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="event_logs")
    device = relationship("Device", back_populates="event_logs")
    
    def __repr__(self):
        return f"<EventLog(id={self.id}, type={self.event_type}, time={self.timestamp})>"

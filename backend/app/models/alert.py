"""ConnectXperts NMS - Alert Models"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Enum, Text, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, enum.Enum):
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class AlertType(str, enum.Enum):
    DEVICE_DOWN = "device_down"
    HIGH_LATENCY = "high_latency"
    PACKET_LOSS = "packet_loss"
    HIGH_JITTER = "high_jitter"
    RECOVERY = "recovery"
    SLA_BREACH = "sla_breach"
    CUSTOM = "custom"


class AlertChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    SMS = "sms"


class AlertGroup(Base):
    __tablename__ = "alert_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    recipients = relationship("AlertRecipient", back_populates="group")


class AlertRecipient(Base):
    __tablename__ = "alert_recipients"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("alert_groups.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    # Contact Info
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    telegram_chat_id = Column(String(100))
    webhook_url = Column(String(500))
    
    # Channels
    whatsapp_enabled = Column(Boolean, default=False)
    email_enabled = Column(Boolean, default=False)
    telegram_enabled = Column(Boolean, default=False)
    webhook_enabled = Column(Boolean, default=False)
    
    # Escalation
    escalation_level = Column(Integer, default=0)
    escalation_delay_minutes = Column(Integer, default=5)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    group = relationship("AlertGroup", back_populates="recipients")
    user = relationship("User", back_populates="notification_recipients")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), index=True)
    
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.MEDIUM)
    status = Column(Enum(AlertStatus), default=AlertStatus.TRIGGERED)
    
    # Alert Details
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # Device State at Alert Time
    latency_ms = Column(Float, nullable=True)
    packet_loss_percent = Column(Float, nullable=True)
    jitter_ms = Column(Float, nullable=True)
    
    # Timing
    triggered_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Recovery
    recovery_alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=True)
    downtime_duration_seconds = Column(Integer, nullable=True)
    is_recovered = Column(Boolean, default=False)
    
    # Escalation
    is_escalated = Column(Boolean, default=False)
    escalation_count = Column(Integer, default=0)
    
    # Relationships
    device = relationship("Device", back_populates="alerts")
    recovery_alert = relationship("Alert", remote_side=[id], foreign_keys=[recovery_alert_id])
    history = relationship("AlertHistory", back_populates="alert")


class AlertHistory(Base):
    __tablename__ = "alert_history"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    channel = Column(Enum(AlertChannel), nullable=False)
    recipient = Column(String(255))
    status = Column(String(50))  # sent, delivered, failed, retrying
    message_id = Column(String(255))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    
    alert = relationship("Alert", back_populates="history")

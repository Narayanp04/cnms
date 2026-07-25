"""ConnectXperts NMS - Notification History Model"""
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class NotificationChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    SMS = "sms"


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationHistory(Base):
    __tablename__ = "notification_history"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True)
    
    # Channel Info
    channel = Column(Enum(NotificationChannel), nullable=False)
    recipient = Column(String(255), nullable=False)
    recipient_name = Column(String(255))
    
    # Message
    message_type = Column(String(50), default="text")  # text, template, media, pdf
    message_title = Column(String(500))
    message_body = Column(Text)
    message_template = Column(String(255))
    media_url = Column(String(500))
    
    # Delivery Status
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.PENDING)
    provider_message_id = Column(String(255))
    provider_status = Column(String(255))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timing
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Custom metadata (stored as JSON)
    extra_data = Column(JSON)
    
    def __repr__(self):
        return f"<Notification(id={self.id}, channel={self.channel}, status={self.status})>"

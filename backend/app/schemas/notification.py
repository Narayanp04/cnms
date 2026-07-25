"""ConnectXperts NMS - Notification Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.notification import NotificationChannel, DeliveryStatus


class NotificationHistoryResponse(BaseModel):
    id: int
    alert_id: Optional[int] = None
    channel: NotificationChannel
    recipient: str
    recipient_name: Optional[str] = None
    message_type: str
    message_title: Optional[str] = None
    message_body: Optional[str] = None
    status: DeliveryStatus
    provider_message_id: Optional[str] = None
    provider_status: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    sent_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WhatsAppTestMessage(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    message: str = Field(..., min_length=1, max_length=1000)


class WhatsAppConfig(BaseModel):
    phone_number_id: str
    access_token: str
    api_version: str = "v18.0"
    business_account_id: Optional[str] = None

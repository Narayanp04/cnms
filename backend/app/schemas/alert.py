"""ConnectXperts NMS - Alert Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.alert import AlertSeverity, AlertStatus, AlertType, AlertChannel


class AlertRecipientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = None
    phone: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    webhook_url: Optional[str] = None
    whatsapp_enabled: bool = False
    email_enabled: bool = False
    telegram_enabled: bool = False
    webhook_enabled: bool = False
    escalation_level: int = 0
    escalation_delay_minutes: int = 5
    group_id: Optional[int] = None


class AlertRecipientResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    webhook_url: Optional[str] = None
    whatsapp_enabled: bool
    email_enabled: bool
    telegram_enabled: bool
    webhook_enabled: bool
    escalation_level: int
    is_active: bool
    group_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class AlertGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class AlertGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    recipients: Optional[List[AlertRecipientResponse]] = []
    
    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: int
    device_id: int
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    latency_ms: Optional[float] = None
    packet_loss_percent: Optional[float] = None
    jitter_ms: Optional[float] = None
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    is_recovered: bool
    downtime_duration_seconds: Optional[int] = None
    is_escalated: bool
    device_hostname: Optional[str] = None
    device_ip: Optional[str] = None
    
    class Config:
        from_attributes = True


class AlertAcknowledgeRequest(BaseModel):
    alert_id: int


class AlertConfigUpdate(BaseModel):
    whatsapp_enabled: bool = False
    email_enabled: bool = False
    telegram_enabled: bool = False
    webhook_enabled: bool = False
    slack_webhook_url: Optional[str] = None
    whatsapp_api_key: Optional[str] = None
    whatsapp_phone_number_id: Optional[str] = None
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    telegram_bot_token: Optional[str] = None

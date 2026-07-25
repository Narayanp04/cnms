"""ConnectXperts NMS - Event Log Schemas"""
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from app.models.event_log import EventType


class EventLogResponse(BaseModel):
    id: int
    event_type: EventType
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    device_id: Optional[int] = None
    device_name: Optional[str] = None
    alert_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    details: Optional[Any] = None
    severity: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class EventLogListResponse(BaseModel):
    total: int
    items: List[EventLogResponse]
    page: int
    page_size: int
    total_pages: int


class EventLogFilter(BaseModel):
    event_types: Optional[List[EventType]] = None
    severity: Optional[str] = None
    user_id: Optional[int] = None
    device_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None

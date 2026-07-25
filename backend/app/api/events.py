"""ConnectXperts NMS - Event Logs API"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, Role
from app.models.event_log import EventType
from app.schemas.event_log import EventLogListResponse, EventLogResponse
from app.services.event_log_service import EventLogService
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/v1/events", tags=["Events"])
event_log_service = EventLogService()


@router.get("", response_model=EventLogListResponse)
async def list_events(
    event_type: Optional[str] = None,
    severity: Optional[str] = Query(None, regex="^(info|warning|error|critical)$"),
    user_id: Optional[int] = None,
    device_id: Optional[int] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List event logs with filters."""
    from datetime import datetime
    
    event_types = [EventType(event_type)] if event_type else None
    dt_from = datetime.fromisoformat(date_from) if date_from else None
    dt_to = datetime.fromisoformat(date_to) if date_to else None
    
    result = await event_log_service.get_events(
        db=db,
        event_types=event_types,
        severity=severity,
        user_id=user_id,
        device_id=device_id,
        date_from=dt_from,
        date_to=dt_to,
        search=search,
        page=page,
        page_size=page_size
    )
    
    return EventLogListResponse(
        total=result["total"],
        items=[EventLogResponse.model_validate(e) for e in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"]
    )


@router.get("/recent", response_model=list)
async def get_recent_events(
    limit: int = Query(20, le=100),
    event_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent event logs."""
    event_types = [EventType(event_type)] if event_type else None
    events = await event_log_service.get_recent_events(db, limit, event_types)
    
    return [
        EventLogResponse.model_validate(e) for e in events
    ]

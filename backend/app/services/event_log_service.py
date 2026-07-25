"""ConnectXperts NMS - Event Log Service"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from app.database import AsyncSessionLocal
from app.models.event_log import EventLog, EventType
from app.config import settings

logger = logging.getLogger(__name__)


class EventLogService:
    """Service for managing event logs and audit trails."""
    
    async def log_event(
        self,
        event_type: EventType,
        title: str,
        description: Optional[str] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None,
        alert_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ) -> Optional[EventLog]:
        """Create a new event log entry."""
        async with AsyncSessionLocal() as db:
            try:
                event_log = EventLog(
                    event_type=event_type,
                    title=title,
                    description=description,
                    user_id=user_id,
                    username=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    device_id=device_id,
                    device_name=device_name,
                    alert_id=alert_id,
                    details=details,
                    severity=severity,
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(event_log)
                await db.flush()
                return event_log
                
            except Exception as e:
                logger.error(f"Error creating event log: {str(e)}")
                await db.rollback()
                return None
    
    async def get_events(
        self,
        db: AsyncSession,
        event_types: Optional[List[EventType]] = None,
        severity: Optional[str] = None,
        user_id: Optional[int] = None,
        device_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """Get paginated event logs with filters."""
        query = select(EventLog)
        
        conditions = []
        if event_types:
            conditions.append(EventLog.event_type.in_(event_types))
        if severity:
            conditions.append(EventLog.severity == severity)
        if user_id:
            conditions.append(EventLog.user_id == user_id)
        if device_id:
            conditions.append(EventLog.device_id == device_id)
        if date_from:
            conditions.append(EventLog.timestamp >= date_from)
        if date_to:
            conditions.append(EventLog.timestamp <= date_to)
        if search:
            search_filter = or_(
                EventLog.title.ilike(f"%{search}%"),
                EventLog.description.ilike(f"%{search}%"),
                EventLog.username.ilike(f"%{search}%"),
                EventLog.device_name.ilike(f"%{search}%")
            )
            conditions.append(search_filter)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Count total
        count_query = query.with_only_columns(func.count(EventLog.id))
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Get page
        query = query.order_by(EventLog.timestamp.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await db.execute(query)
        events = result.scalars().all()
        
        return {
            "total": total,
            "items": events,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
        }
    
    async def get_recent_events(
        self,
        db: AsyncSession,
        limit: int = 20,
        event_types: Optional[List[EventType]] = None
    ) -> List[EventLog]:
        """Get recent event logs."""
        query = select(EventLog)
        
        if event_types:
            query = query.where(EventLog.event_type.in_(event_types))
        
        query = query.order_by(EventLog.timestamp.desc()).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def log_login(self, user_id: int, username: str, ip_address: str, user_agent: Optional[str] = None):
        """Log user login event."""
        return await self.log_event(
            event_type=EventType.USER_LOGIN,
            title=f"User Login - {username}",
            description=f"User {username} logged in from {ip_address}",
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            severity="info"
        )
    
    async def log_device_change(self, device_id: int, device_name: str, change_type: str, details: Dict):
        """Log device configuration change."""
        event_type_map = {
            "created": EventType.DEVICE_ADDED,
            "updated": EventType.DEVICE_UPDATED,
            "deleted": EventType.DEVICE_DELETED,
        }
        
        return await self.log_event(
            event_type=event_type_map.get(change_type, EventType.CUSTOM),
            title=f"Device {change_type.title()} - {device_name}",
            description=f"Device {device_name} ({device_id}) was {change_type}",
            device_id=device_id,
            device_name=device_name,
            details=details,
            severity="info"
        )
    
    async def log_api_call(self, user_id: int, username: str, endpoint: str, method: str, ip_address: str):
        """Log API call for audit purposes."""
        return await self.log_event(
            event_type=EventType.API_CALL,
            title=f"API Call - {method} {endpoint}",
            description=f"User {username} called {method} {endpoint}",
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details={"endpoint": endpoint, "method": method},
            severity="info"
        )

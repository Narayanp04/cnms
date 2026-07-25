"""ConnectXperts NMS - Device Management API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, delete
import io
import csv
import json

from app.database import get_db
from app.models.user import User, Role
from app.models.device import Device, DeviceTag, DeviceStatus, PollingInterval
from app.schemas.device import (
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceListResponse,
    BulkImportResult, DeviceMapData, DeviceTagSchema
)
from app.utils.security import get_current_user, check_role_permissions
from app.services.event_log_service import EventLogService

router = APIRouter(prefix="/api/v1/devices", tags=["Devices"])
event_log_service = EventLogService()


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    region: Optional[str] = None,
    provider: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    is_monitored: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List devices with pagination and filters."""
    query = select(Device).where(Device.is_deleted == False)
    
    # Multi-customer support
    if current_user.role != Role.ADMIN and current_user.customer_id:
        query = query.where(Device.customer_id == current_user.customer_id)
    
    # Apply filters
    if status:
        query = query.where(Device.status == status)
    if customer_id:
        query = query.where(Device.customer_id == customer_id)
    if region:
        query = query.where(Device.region == region)
    if provider:
        query = query.where(Device.provider == provider)
    if category:
        query = query.where(Device.category == category)
    if search:
        search_filter = or_(
            Device.hostname.ilike(f"%{search}%"),
            Device.ip_address.ilike(f"%{search}%"),
            Device.customer_name.ilike(f"%{search}%"),
            Device.site_name.ilike(f"%{search}%"),
            Device.circuit_id.ilike(f"%{search}%"),
            Device.region.ilike(f"%{search}%"),
            Device.provider.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    if is_monitored is not None:
        query = query.where(Device.is_monitoring_enabled == is_monitored)
    
    # Count total
    from sqlalchemy import func
    count_query = query.with_only_columns(func.count(Device.id))
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Paginate
    query = query.order_by(Device.hostname.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    devices = result.scalars().all()
    
    return DeviceListResponse(
        total=total,
        items=[DeviceResponse.model_validate(d) for d in devices],
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size if total > 0 else 1
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get device by ID."""
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.is_deleted == False)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Multi-customer check
    if current_user.role != Role.ADMIN and current_user.customer_id:
        if device.customer_id != current_user.customer_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return DeviceResponse.model_validate(device)


@router.post("", response_model=DeviceResponse)
async def create_device(
    device_data: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role_permissions([Role.ADMIN, Role.OPERATOR]))
):
    """Create new device."""
    # Check for duplicate IP
    existing = await db.execute(
        select(Device).where(Device.ip_address == device_data.ip_address, Device.is_deleted == False)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Device with this IP already exists")
    
    device = Device(**device_data.model_dump(exclude={'tags'}), created_by=current_user.id)
    
    # Process tags
    if device_data.tags:
        for tag_data in device_data.tags:
            tag = await db.execute(
                select(DeviceTag).where(DeviceTag.name == tag_data.name)
            )
            existing_tag = tag.scalar_one_or_none()
            if existing_tag:
                device.tags.append(existing_tag)
            else:
                new_tag = DeviceTag(name=tag_data.name, color=tag_data.color)
                db.add(new_tag)
                await db.flush()
                device.tags.append(new_tag)
    
    db.add(device)
    await db.flush()
    
    # Log event
    await event_log_service.log_device_change(
        device.id, device.hostname, "created",
        {"ip": device.ip_address, "customer": device.customer_name}
    )
    
    return DeviceResponse.model_validate(device)


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role_permissions([Role.ADMIN, Role.OPERATOR]))
):
    """Update device configurations."""
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.is_deleted == False)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Update fields
    update_data = device_data.model_dump(exclude_unset=True, exclude={'tags'})
    for field, value in update_data.items():
        setattr(device, field, value)
    
    # Update tags
    if device_data.tags is not None:
        device.tags.clear()
        for tag_data in device_data.tags:
            tag = await db.execute(
                select(DeviceTag).where(DeviceTag.name == tag_data.name)
            )
            existing_tag = tag.scalar_one_or_none()
            if existing_tag:
                device.tags.append(existing_tag)
            else:
                new_tag = DeviceTag(name=tag_data.name, color=tag_data.color)
                db.add(new_tag)
                await db.flush()
                device.tags.append(new_tag)
    
    await db.flush()
    
    await event_log_service.log_device_change(
        device.id, device.hostname, "updated", update_data
    )
    
    return DeviceResponse.model_validate(device)


@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """Soft delete a device."""
    result = await db.execute(
        select(Device).where(Device.id == device_id, Device.is_deleted == False)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device.is_deleted = True
    device.is_monitoring_enabled = False
    
    await event_log_service.log_device_change(
        device.id, device.hostname, "deleted", {}
    )
    
    return {"message": "Device deleted successfully"}


@router.post("/bulk-import", response_model=BulkImportResult)
async def bulk_import_devices(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_role_permissions([Role.ADMIN, Role.OPERATOR]))
):
    """Bulk import devices from CSV or Excel file."""
    result = BulkImportResult(total=0, success=0, failed=0, errors=[])
    
    content = await file.read()
    
    if file.filename.endswith('.csv'):
        text = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please use CSV.")
    
    result.total = len(rows)
    
    for row in rows:
        try:
            device = Device(
                hostname=row.get('hostname', row.get('Hostname', '')),
                ip_address=row.get('ip_address', row.get('IP Address', row.get('IP', ''))),
                customer_name=row.get('customer_name', row.get('Customer', '')),
                site_name=row.get('site_name', row.get('Site', '')),
                region=row.get('region', row.get('Region', '')),
                circuit_id=row.get('circuit_id', row.get('Circuit ID', '')),
                bandwidth=row.get('bandwidth', row.get('Bandwidth', '')),
                provider=row.get('provider', row.get('Provider', '')),
                category=row.get('category', row.get('Category', '')),
                location=row.get('location', row.get('Location', '')),
                created_by=current_user.id
            )
            db.add(device)
            await db.flush()
            result.success += 1
            
        except Exception as e:
            result.failed += 1
            result.errors.append(f"Row {result.total - len(rows) + result.failed}: {str(e)}")
    
    return result


@router.get("/export/csv")
async def export_devices_csv(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export devices to CSV."""
    query = select(Device).where(Device.is_deleted == False)
    if current_user.role != Role.ADMIN and current_user.customer_id:
        query = query.where(Device.customer_id == current_user.customer_id)
    
    result = await db.execute(query)
    devices = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Hostname', 'IP Address', 'Customer', 'Site', 'Region', 'Status', 
                     'Latency', 'Packet Loss', 'Circuit ID', 'Provider', 'Category', 'SLA 24h'])
    
    for d in devices:
        writer.writerow([d.hostname, d.ip_address, d.customer_name, d.site_name,
                        d.region, d.status.value if d.status else '',
                        d.current_latency, d.current_packet_loss,
                        d.circuit_id, d.provider, d.category, d.sla_24h])
    
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=devices_export.csv"}
    )


@router.get("/map/data", response_model=List[DeviceMapData])
async def get_devices_for_map(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get devices with coordinates for map display."""
    query = select(Device).where(
        Device.is_deleted == False,
        Device.latitude.isnot(None),
        Device.longitude.isnot(None)
    )
    
    if current_user.role != Role.ADMIN and current_user.customer_id:
        query = query.where(Device.customer_id == current_user.customer_id)
    
    result = await db.execute(query)
    devices = result.scalars().all()
    
    return [
        DeviceMapData(
            id=d.id,
            hostname=d.hostname,
            display_name=d.display_name,
            ip_address=d.ip_address,
            status=d.status or DeviceStatus.UNKNOWN,
            latitude=d.latitude,
            longitude=d.longitude,
            current_latency=d.current_latency,
            customer_name=d.customer_name,
            site_name=d.site_name
        )
        for d in devices
    ]


@router.get("/tags/list", response_model=List[DeviceTagSchema])
async def list_tags(
    db: AsyncSession = Depends(get_db)
):
    """List all device tags."""
    result = await db.execute(select(DeviceTag))
    tags = result.scalars().all()
    return [DeviceTagSchema.model_validate(t) for t in tags]

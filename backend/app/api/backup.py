"""ConnectXperts NMS - Backup & Restore API"""
from fastapi import APIRouter, Depends, HTTPException
from app.models.user import User, Role
from app.utils.security import get_current_user, check_role_permissions
from app.services.backup_service import BackupService

router = APIRouter(prefix="/api/v1/backup", tags=["Backup"])
backup_service = BackupService()


@router.post("/create")
async def create_backup(
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """Create a database backup."""
    filepath = backup_service.create_backup()
    if not filepath:
        raise HTTPException(status_code=500, detail="Backup creation failed")
    
    return {"message": "Backup created successfully", "filepath": filepath}


@router.get("/list")
async def list_backups(
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """List all available backups."""
    backups = backup_service.list_backups()
    return {"backups": backups}


@router.post("/restore")
async def restore_backup(
    filepath: str,
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """Restore database from a backup."""
    success = backup_service.restore_backup(filepath)
    if not success:
        raise HTTPException(status_code=500, detail="Backup restoration failed")
    
    return {"message": "Database restored successfully"}


@router.delete("/delete")
async def delete_backup(
    filepath: str,
    current_user: User = Depends(check_role_permissions([Role.ADMIN]))
):
    """Delete a backup file."""
    success = backup_service.delete_backup(filepath)
    if not success:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    return {"message": "Backup deleted successfully"}

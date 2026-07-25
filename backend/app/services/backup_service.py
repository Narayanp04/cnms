"""ConnectXperts NMS - Backup & Restore Service"""
import logging
import os
import subprocess
import shutil
import gzip
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
import json

from app.config import settings

logger = logging.getLogger(__name__)


class BackupService:
    """Service for managing database backups and restores."""
    
    def __init__(self):
        self.backup_dir = settings.BACKUP_DIR
        self.retention_days = settings.BACKUP_RETENTION_DAYS
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self):
        """Ensure backup directory exists."""
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self) -> Optional[str]:
        """Create a database backup."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cnms_backup_{timestamp}.sql.gz"
            filepath = os.path.join(self.backup_dir, filename)
            
            # Extract database connection info from URL
            # postgresql+asyncpg://user:pass@host:port/db
            db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            
            # Use pg_dump for backup
            cmd = f'pg_dump "{db_url}" | gzip > "{filepath}"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database backup created: {filename}")
                
                # Cleanup old backups
                self._cleanup_old_backups()
                
                return filepath
            else:
                logger.error(f"Backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Backup error: {str(e)}")
            return None
    
    def restore_backup(self, filepath: str) -> bool:
        """Restore database from a backup file."""
        try:
            if not os.path.exists(filepath):
                logger.error(f"Backup file not found: {filepath}")
                return False
            
            db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            
            if filepath.endswith('.gz'):
                cmd = f'gunzip -c "{filepath}" | psql "{db_url}"'
            else:
                cmd = f'psql "{db_url}" < "{filepath}"'
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database restored from: {filepath}")
                return True
            else:
                logger.error(f"Restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Restore error: {str(e)}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """List all available backups."""
        backups = []
        
        try:
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("cnms_backup_") and filename.endswith((".sql", ".sql.gz")):
                    filepath = os.path.join(self.backup_dir, filename)
                    stat = os.stat(filepath)
                    
                    backups.append({
                        "filename": filename,
                        "path": filepath,
                        "size_bytes": stat.st_size,
                        "size_human": self._format_size(stat.st_size),
                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # Sort by creation time (newest first)
            backups.sort(key=lambda x: x["created_at"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing backups: {str(e)}")
        
        return backups
    
    def delete_backup(self, filepath: str) -> bool:
        """Delete a specific backup."""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Backup deleted: {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting backup: {str(e)}")
            return False
    
    def _cleanup_old_backups(self):
        """Remove backups older than retention period."""
        try:
            now = datetime.now()
            cutoff = now - timedelta(days=self.retention_days)
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("cnms_backup_") and filename.endswith((".sql", ".sql.gz")):
                    filepath = os.path.join(self.backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_time < cutoff:
                        os.remove(filepath)
                        logger.info(f"Removed old backup: {filename}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up backups: {str(e)}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size to human readable."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"

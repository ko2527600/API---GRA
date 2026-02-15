"""Backup service for scheduled and manual backups"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from app.utils.backup import DatabaseBackupManager
from app.config.backup_config import backup_config

logger = logging.getLogger(__name__)


class BackupService:
    """Service for managing database backups"""
    
    def __init__(self):
        """Initialize backup service"""
        self.backup_manager = DatabaseBackupManager(backup_dir=backup_config.BACKUP_DIR)
        self.last_backup_time: Optional[datetime] = None
        self.last_backup_status: Optional[bool] = None
    
    def perform_backup(self) -> Tuple[bool, str]:
        """
        Perform a database backup
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            logger.info("Starting database backup...")
            success, backup_file = self.backup_manager.create_backup(
                compress=backup_config.COMPRESS_BACKUPS
            )
            
            if success:
                self.last_backup_time = datetime.now()
                self.last_backup_status = True
                message = f"Backup completed successfully: {backup_file}"
                logger.info(message)
                
                # Verify backup integrity if enabled
                if backup_config.VERIFY_BACKUP_INTEGRITY:
                    self._verify_backup(backup_file)
                
                return True, message
            else:
                self.last_backup_status = False
                message = "Backup failed"
                logger.error(message)
                return False, message
        
        except Exception as e:
            self.last_backup_status = False
            logger.error(f"Backup service error: {e}")
            return False, str(e)
    
    def restore_from_backup(self, backup_file: str) -> Tuple[bool, str]:
        """
        Restore database from a backup file
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            logger.warning(f"Starting database restore from {backup_file}")
            success, message = self.backup_manager.restore_backup(backup_file)
            
            if success:
                logger.info(f"Restore completed: {message}")
            else:
                logger.error(f"Restore failed: {message}")
            
            return success, message
        
        except Exception as e:
            logger.error(f"Restore service error: {e}")
            return False, str(e)
    
    def cleanup_old_backups(self) -> Tuple[int, float]:
        """
        Clean up old backups based on retention policy
        
        Returns:
            Tuple of (deleted_count: int, freed_size_mb: float)
        """
        try:
            logger.info(f"Cleaning up backups older than {backup_config.BACKUP_RETENTION_DAYS} days")
            deleted_count, freed_size = self.backup_manager.cleanup_old_backups(
                retention_days=backup_config.BACKUP_RETENTION_DAYS
            )
            
            logger.info(f"Cleanup completed: {deleted_count} backups deleted, {freed_size} MB freed")
            return deleted_count, freed_size
        
        except Exception as e:
            logger.error(f"Cleanup service error: {e}")
            return 0, 0.0
    
    def get_backup_status(self) -> Dict:
        """
        Get current backup status
        
        Returns:
            Dictionary with backup status information
        """
        try:
            stats = self.backup_manager.get_backup_stats()
            backups = self.backup_manager.list_backups()
            
            return {
                "last_backup_time": self.last_backup_time.isoformat() if self.last_backup_time else None,
                "last_backup_status": self.last_backup_status,
                "total_backups": stats.get("total_backups", 0),
                "total_size_mb": stats.get("total_size_mb", 0),
                "oldest_backup": stats.get("oldest_backup"),
                "newest_backup": stats.get("newest_backup"),
                "backup_directory": stats.get("backup_directory"),
                "retention_days": backup_config.BACKUP_RETENTION_DAYS,
                "compression_enabled": backup_config.COMPRESS_BACKUPS,
                "scheduled_backups_enabled": backup_config.ENABLE_SCHEDULED_BACKUPS,
                "recent_backups": backups[:5]  # Last 5 backups
            }
        
        except Exception as e:
            logger.error(f"Failed to get backup status: {e}")
            return {}
    
    def _verify_backup(self, backup_file: str) -> bool:
        """
        Verify backup file integrity
        
        Args:
            backup_file: Path to backup file
            
        Returns:
            True if backup is valid, False otherwise
        """
        try:
            import gzip
            from pathlib import Path
            
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                logger.warning(f"Backup file not found for verification: {backup_file}")
                return False
            
            # Check file size
            file_size = backup_path.stat().st_size
            if file_size == 0:
                logger.warning(f"Backup file is empty: {backup_file}")
                return False
            
            # Verify compression if applicable
            if backup_file.endswith(".gz"):
                try:
                    with gzip.open(backup_file, "rb") as f:
                        # Read first chunk to verify integrity
                        f.read(1024)
                    logger.info(f"Backup integrity verified: {backup_file}")
                    return True
                except Exception as e:
                    logger.warning(f"Backup integrity check failed: {e}")
                    return False
            else:
                logger.info(f"Backup file verified: {backup_file}")
                return True
        
        except Exception as e:
            logger.error(f"Backup verification error: {e}")
            return False
    
    def get_retention_policy(self) -> Dict:
        """
        Get data retention policy information
        
        Returns:
            Dictionary with retention policy details
        """
        return {
            "backup_retention_days": backup_config.BACKUP_RETENTION_DAYS,
            "audit_log_retention_years": backup_config.AUDIT_LOG_RETENTION_YEARS,
            "submission_retention_years": backup_config.SUBMISSION_RETENTION_YEARS,
            "archive_after_days": backup_config.ARCHIVE_AFTER_DAYS,
            "archival_enabled": backup_config.ENABLE_ARCHIVAL,
            "archive_directory": backup_config.ARCHIVE_DIR,
            "compliance_notes": {
                "audit_logs": "Retained for 7 years per GRA compliance requirements",
                "submissions": "Retained for 7 years per GRA compliance requirements",
                "backups": f"Retained for {backup_config.BACKUP_RETENTION_DAYS} days for disaster recovery"
            }
        }

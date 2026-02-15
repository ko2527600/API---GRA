"""Backup configuration and scheduling"""
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class BackupConfig:
    """Backup configuration settings"""
    
    # Backup directory
    BACKUP_DIR: str = os.getenv("BACKUP_DIR", "backups")
    
    # Backup scheduling
    ENABLE_SCHEDULED_BACKUPS: bool = os.getenv("ENABLE_SCHEDULED_BACKUPS", "True").lower() == "true"
    BACKUP_SCHEDULE_HOUR: int = int(os.getenv("BACKUP_SCHEDULE_HOUR", "2"))  # 2 AM
    BACKUP_SCHEDULE_MINUTE: int = int(os.getenv("BACKUP_SCHEDULE_MINUTE", "0"))
    
    # Backup retention
    BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    AUDIT_LOG_RETENTION_YEARS: int = int(os.getenv("AUDIT_LOG_RETENTION_YEARS", "7"))
    SUBMISSION_RETENTION_YEARS: int = int(os.getenv("SUBMISSION_RETENTION_YEARS", "7"))
    
    # Backup compression
    COMPRESS_BACKUPS: bool = os.getenv("COMPRESS_BACKUPS", "True").lower() == "true"
    
    # Backup notifications
    ENABLE_BACKUP_NOTIFICATIONS: bool = os.getenv("ENABLE_BACKUP_NOTIFICATIONS", "False").lower() == "true"
    BACKUP_NOTIFICATION_EMAIL: Optional[str] = os.getenv("BACKUP_NOTIFICATION_EMAIL")
    
    # Backup verification
    VERIFY_BACKUP_INTEGRITY: bool = os.getenv("VERIFY_BACKUP_INTEGRITY", "True").lower() == "true"
    
    # Archival settings
    ENABLE_ARCHIVAL: bool = os.getenv("ENABLE_ARCHIVAL", "True").lower() == "true"
    ARCHIVE_DIR: str = os.getenv("ARCHIVE_DIR", "archives")
    ARCHIVE_AFTER_DAYS: int = int(os.getenv("ARCHIVE_AFTER_DAYS", "365"))  # Archive after 1 year
    
    # Remote backup (optional)
    ENABLE_REMOTE_BACKUP: bool = os.getenv("ENABLE_REMOTE_BACKUP", "False").lower() == "true"
    REMOTE_BACKUP_URL: Optional[str] = os.getenv("REMOTE_BACKUP_URL")
    REMOTE_BACKUP_API_KEY: Optional[str] = os.getenv("REMOTE_BACKUP_API_KEY")


# Create config instance
backup_config = BackupConfig()

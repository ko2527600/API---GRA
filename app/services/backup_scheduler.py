"""Backup scheduler for automated database backups and audit log retention"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.audit_log_service import AuditLogService
from app.database import SessionLocal

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: BackgroundScheduler = None
_backup_service = None


def init_backup_scheduler():
    """Initialize and start the backup scheduler"""
    global _scheduler, _backup_service
    
    # Import here to avoid circular imports
    from app.config.backup_config import backup_config
    from app.services.backup_service import BackupService
    
    if not backup_config.ENABLE_SCHEDULED_BACKUPS:
        logger.info("Scheduled backups are disabled")
        return
    
    try:
        _backup_service = BackupService()
        _scheduler = BackgroundScheduler()
        
        # Schedule daily backup
        trigger = CronTrigger(
            hour=backup_config.BACKUP_SCHEDULE_HOUR,
            minute=backup_config.BACKUP_SCHEDULE_MINUTE
        )
        
        _scheduler.add_job(
            _perform_scheduled_backup,
            trigger=trigger,
            id="daily_backup",
            name="Daily Database Backup",
            replace_existing=True
        )
        
        # Schedule cleanup of old backups (weekly)
        cleanup_trigger = CronTrigger(
            day_of_week="sun",
            hour=3,
            minute=0
        )
        
        _scheduler.add_job(
            _cleanup_old_backups,
            trigger=cleanup_trigger,
            id="backup_cleanup",
            name="Backup Cleanup",
            replace_existing=True
        )
        
        # Schedule audit log retention (monthly on the 1st at 2 AM)
        audit_retention_trigger = CronTrigger(
            day=1,
            hour=2,
            minute=0
        )
        
        _scheduler.add_job(
            _cleanup_old_audit_logs,
            trigger=audit_retention_trigger,
            id="audit_log_retention",
            name="Audit Log Retention",
            replace_existing=True
        )
        
        _scheduler.start()
        logger.info(
            f"Backup scheduler started. "
            f"Daily backup scheduled at {backup_config.BACKUP_SCHEDULE_HOUR}:"
            f"{backup_config.BACKUP_SCHEDULE_MINUTE:02d}"
        )
    
    except Exception as e:
        logger.error(f"Failed to initialize backup scheduler: {e}")


def shutdown_backup_scheduler():
    """Shutdown the backup scheduler"""
    global _scheduler
    
    if _scheduler and _scheduler.running:
        try:
            _scheduler.shutdown()
            logger.info("Backup scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down backup scheduler: {e}")


def _perform_scheduled_backup():
    """Perform scheduled backup"""
    try:
        logger.info("Executing scheduled database backup...")
        success, message = _backup_service.perform_backup()
        
        if success:
            logger.info(f"Scheduled backup completed: {message}")
        else:
            logger.error(f"Scheduled backup failed: {message}")
    
    except Exception as e:
        logger.error(f"Scheduled backup error: {e}")


def _cleanup_old_backups():
    """Cleanup old backups"""
    try:
        logger.info("Executing backup cleanup...")
        deleted_count, freed_size = _backup_service.cleanup_old_backups()
        logger.info(f"Backup cleanup completed: {deleted_count} backups deleted, {freed_size} MB freed")
    
    except Exception as e:
        logger.error(f"Backup cleanup error: {e}")


def _cleanup_old_audit_logs():
    """Cleanup old audit logs based on retention policy"""
    try:
        from app.config.backup_config import backup_config
        
        logger.info("Executing audit log retention cleanup...")
        db = SessionLocal()
        try:
            deleted_count = AuditLogService.delete_old_audit_logs(
                db=db,
                days_to_keep=backup_config.AUDIT_LOG_RETENTION_YEARS * 365
            )
            logger.info(
                f"Audit log retention completed: {deleted_count} logs deleted "
                f"(older than {backup_config.AUDIT_LOG_RETENTION_YEARS} years)"
            )
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Audit log retention error: {e}")


def get_scheduler_status() -> dict:
    """Get backup scheduler status"""
    global _scheduler
    
    if not _scheduler:
        return {
            "enabled": False,
            "running": False,
            "jobs": []
        }
    
    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
        })
    
    from app.config.backup_config import backup_config
    
    return {
        "enabled": backup_config.ENABLE_SCHEDULED_BACKUPS,
        "running": _scheduler.running,
        "jobs": jobs
    }

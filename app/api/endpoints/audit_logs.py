"""API endpoints for audit log retrieval"""
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth_dependency import verify_auth
from app.services.audit_log_service import AuditLogService
from app.logger import get_logger
from app.services.backup_scheduler import get_scheduler_status

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/audit-logs", tags=["audit-logs"])


async def get_current_business_id(
    business: dict = Depends(verify_auth),
) -> UUID:
    """Extract business ID from authenticated business data"""
    if not business or "id" not in business:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return UUID(business["id"])


@router.get("/retention/policy")
async def get_retention_policy():
    """
    Get audit log retention policy
    
    Returns:
    - retention_years: Number of years to retain audit logs
    - retention_days: Number of days to retain audit logs
    - scheduler_status: Status of the retention scheduler
    """
    try:
        from app.config import settings
        scheduler_status = get_scheduler_status()
        
        # Get retention years from settings
        retention_years = settings.AUDIT_LOG_RETENTION_DAYS // 365
        
        return {
            "retention_years": retention_years,
            "retention_days": settings.AUDIT_LOG_RETENTION_DAYS,
            "scheduler_enabled": scheduler_status.get("enabled", False),
            "scheduler_running": scheduler_status.get("running", False),
            "scheduled_jobs": [
                job for job in scheduler_status.get("jobs", [])
                if "audit" in job.get("id", "").lower()
            ],
        }
    except Exception as e:
        logger.error(
            f"Failed to get retention policy: {str(e)}",
            extra={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail="Failed to get retention policy")


@router.post("/retention/cleanup")
async def trigger_audit_log_cleanup(
    db: Session = Depends(get_db),
):
    """
    Manually trigger audit log retention cleanup
    
    This endpoint allows manual cleanup of audit logs older than the retention period.
    Typically called by administrators or scheduled tasks.
    
    Returns:
    - deleted_count: Number of audit logs deleted
    - retention_days: Number of days retained
    - cutoff_date: Date before which logs were deleted
    """
    try:
        from app.config import settings
        from datetime import timedelta
        
        retention_days = settings.AUDIT_LOG_RETENTION_DAYS
        retention_years = retention_days // 365
        
        deleted_count = AuditLogService.delete_old_audit_logs(
            db=db,
            days_to_keep=retention_days,
        )
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        logger.info(
            f"Manual audit log cleanup triggered: {deleted_count} logs deleted",
            extra={
                "deleted_count": deleted_count,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
            }
        )
        
        return {
            "deleted_count": deleted_count,
            "retention_days": retention_days,
            "retention_years": retention_years,
            "cutoff_date": cutoff_date.isoformat(),
            "message": f"Successfully deleted {deleted_count} audit logs older than {retention_years} years",
        }
    except Exception as e:
        logger.error(
            f"Failed to trigger audit log cleanup: {str(e)}",
            extra={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail="Failed to trigger audit log cleanup")


@router.get("/by-action/{action}")
async def get_audit_logs_by_action(
    action: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    business_id: UUID = Depends(get_current_business_id),
):
    """
    Retrieve audit logs filtered by action type
    
    Path Parameters:
    - action: Action type to filter by
    
    Query Parameters:
    - limit: Maximum number of logs to return (1-1000, default 100)
    
    Returns:
    - List of audit log entries matching the action
    """
    try:
        logs = AuditLogService.get_audit_logs_by_action(
            db=db,
            business_id=business_id,
            action=action,
            limit=limit,
        )
        
        return {
            "logs": [
                {
                    "id": str(log.id),
                    "action": log.action,
                    "endpoint": log.endpoint,
                    "method": log.method,
                    "response_code": log.response_code,
                    "response_status": log.response_status,
                    "error_message": log.error_message,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat(),
                }
                for log in logs
            ],
            "total": len(logs),
        }
    except Exception as e:
        logger.error(
            f"Failed to retrieve audit logs by action: {str(e)}",
            extra={
                "business_id": str(business_id),
                "action": action,
                "error": str(e),
            }
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")


@router.get("/by-date-range/")
async def get_audit_logs_by_date_range(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    limit: int = Query(1000, ge=1, le=10000),
    db: Session = Depends(get_db),
    business_id: UUID = Depends(get_current_business_id),
):
    """
    Retrieve audit logs within a date range
    
    Query Parameters:
    - start_date: Start date (ISO format, required)
    - end_date: End date (ISO format, required)
    - limit: Maximum number of logs to return (1-10000, default 1000)
    
    Returns:
    - List of audit log entries within the date range
    """
    try:
        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before end_date"
            )
        
        logs = AuditLogService.get_audit_logs_by_date_range(
            db=db,
            business_id=business_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        
        return {
            "logs": [
                {
                    "id": str(log.id),
                    "action": log.action,
                    "endpoint": log.endpoint,
                    "method": log.method,
                    "response_code": log.response_code,
                    "response_status": log.response_status,
                    "error_message": log.error_message,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat(),
                }
                for log in logs
            ],
            "total": len(logs),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to retrieve audit logs by date range: {str(e)}",
            extra={
                "business_id": str(business_id),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "error": str(e),
            }
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")


@router.get("/{audit_log_id}")
async def get_audit_log(
    audit_log_id: UUID,
    db: Session = Depends(get_db),
    business_id: UUID = Depends(get_current_business_id),
):
    """
    Retrieve a specific audit log entry
    
    Path Parameters:
    - audit_log_id: Audit log identifier
    
    Returns:
    - Audit log entry details
    """
    try:
        log = AuditLogService.get_audit_log_by_id(
            db=db,
            business_id=business_id,
            audit_log_id=audit_log_id,
        )
        
        if not log:
            raise HTTPException(status_code=404, detail="Audit log not found")
        
        return {
            "id": str(log.id),
            "action": log.action,
            "endpoint": log.endpoint,
            "method": log.method,
            "request_payload": log.request_payload,
            "response_code": log.response_code,
            "response_status": log.response_status,
            "error_message": log.error_message,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "created_at": log.created_at.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to retrieve audit log: {str(e)}",
            extra={
                "business_id": str(business_id),
                "audit_log_id": str(audit_log_id),
                "error": str(e),
            }
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve audit log")


@router.get("")
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    business_id: UUID = Depends(get_current_business_id),
):
    """
    Retrieve audit logs for the authenticated business
    
    Query Parameters:
    - limit: Maximum number of logs to return (1-1000, default 100)
    - offset: Number of logs to skip (default 0)
    - action: Filter by action type (optional)
    - start_date: Filter by start date (ISO format, optional)
    - end_date: Filter by end date (ISO format, optional)
    
    Returns:
    - logs: List of audit log entries
    - total: Total number of logs matching the filter
    - limit: Limit used in query
    - offset: Offset used in query
    """
    try:
        logs, total = AuditLogService.get_audit_logs(
            db=db,
            business_id=business_id,
            limit=limit,
            offset=offset,
            action=action,
            start_date=start_date,
            end_date=end_date,
        )
        
        return {
            "logs": [
                {
                    "id": str(log.id),
                    "action": log.action,
                    "endpoint": log.endpoint,
                    "method": log.method,
                    "response_code": log.response_code,
                    "response_status": log.response_status,
                    "error_message": log.error_message,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat(),
                }
                for log in logs
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(
            f"Failed to retrieve audit logs: {str(e)}",
            extra={
                "business_id": str(business_id),
                "error": str(e),
            }
        )
        raise HTTPException(status_code=500, detail="Failed to retrieve audit logs")

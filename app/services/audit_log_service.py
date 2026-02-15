"""Service for managing audit logs"""
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session
from app.models.models import AuditLog
from app.logger import get_logger

logger = get_logger(__name__)


class AuditLogService:
    """Service for creating and retrieving audit logs"""
    
    @staticmethod
    def create_audit_log(
        db: Session,
        business_id: UUID,
        action: str,
        endpoint: str,
        method: str,
        response_code: int,
        response_status: str,
        request_payload: Optional[dict] = None,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Create an audit log entry
        
        Args:
            db: Database session
            business_id: Business identifier
            action: Action performed (e.g., API_REQUEST, API_RESPONSE, GRA_SUBMISSION)
            endpoint: API endpoint
            method: HTTP method
            response_code: HTTP response code
            response_status: Response status (SUCCESS, FAILED)
            request_payload: Request payload (optional, will be masked)
            error_message: Error message if applicable
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            AuditLog: Created audit log entry
        """
        try:
            audit_log = AuditLog(
                business_id=business_id,
                action=action,
                endpoint=endpoint,
                method=method,
                request_payload=request_payload,
                response_code=response_code,
                response_status=response_status,
                error_message=error_message,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
            
            logger.debug(
                f"Audit log created: {action} - {endpoint}",
                extra={
                    "audit_log_id": str(audit_log.id),
                    "business_id": str(business_id),
                    "action": action,
                }
            )
            
            return audit_log
        except Exception as e:
            db.rollback()
            logger.error(
                f"Failed to create audit log: {str(e)}",
                extra={
                    "business_id": str(business_id),
                    "action": action,
                    "error": str(e),
                }
            )
            raise
    
    @staticmethod
    def get_audit_logs(
        db: Session,
        business_id: UUID,
        limit: int = 100,
        offset: int = 0,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> tuple[List[AuditLog], int]:
        """
        Retrieve audit logs for a business
        
        Args:
            db: Database session
            business_id: Business identifier
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            action: Filter by action (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)
            
        Returns:
            Tuple of (audit logs, total count)
        """
        try:
            query = db.query(AuditLog).filter(AuditLog.business_id == business_id)
            
            # Apply filters
            if action:
                query = query.filter(AuditLog.action == action)
            
            if start_date:
                query = query.filter(AuditLog.created_at >= start_date)
            
            if end_date:
                query = query.filter(AuditLog.created_at <= end_date)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination and ordering
            logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()
            
            return logs, total_count
        except Exception as e:
            logger.error(
                f"Failed to retrieve audit logs: {str(e)}",
                extra={
                    "business_id": str(business_id),
                    "error": str(e),
                }
            )
            raise
    
    @staticmethod
    def get_audit_log_by_id(db: Session, business_id: UUID, audit_log_id: UUID) -> Optional[AuditLog]:
        """
        Retrieve a specific audit log
        
        Args:
            db: Database session
            business_id: Business identifier
            audit_log_id: Audit log identifier
            
        Returns:
            AuditLog or None if not found
        """
        try:
            return db.query(AuditLog).filter(
                and_(
                    AuditLog.id == audit_log_id,
                    AuditLog.business_id == business_id
                )
            ).first()
        except Exception as e:
            logger.error(
                f"Failed to retrieve audit log: {str(e)}",
                extra={
                    "business_id": str(business_id),
                    "audit_log_id": str(audit_log_id),
                    "error": str(e),
                }
            )
            raise
    
    @staticmethod
    def get_audit_logs_by_date_range(
        db: Session,
        business_id: UUID,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000,
    ) -> List[AuditLog]:
        """
        Retrieve audit logs within a date range
        
        Args:
            db: Database session
            business_id: Business identifier
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            limit: Maximum number of logs to return
            
        Returns:
            List of audit logs
        """
        try:
            return db.query(AuditLog).filter(
                and_(
                    AuditLog.business_id == business_id,
                    AuditLog.created_at >= start_date,
                    AuditLog.created_at <= end_date,
                )
            ).order_by(desc(AuditLog.created_at)).limit(limit).all()
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
            raise
    
    @staticmethod
    def get_audit_logs_by_action(
        db: Session,
        business_id: UUID,
        action: str,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        Retrieve audit logs by action type
        
        Args:
            db: Database session
            business_id: Business identifier
            action: Action type to filter by
            limit: Maximum number of logs to return
            
        Returns:
            List of audit logs
        """
        try:
            return db.query(AuditLog).filter(
                and_(
                    AuditLog.business_id == business_id,
                    AuditLog.action == action,
                )
            ).order_by(desc(AuditLog.created_at)).limit(limit).all()
        except Exception as e:
            logger.error(
                f"Failed to retrieve audit logs by action: {str(e)}",
                extra={
                    "business_id": str(business_id),
                    "action": action,
                    "error": str(e),
                }
            )
            raise
    
    @staticmethod
    def delete_old_audit_logs(
        db: Session,
        days_to_keep: int = 2555,  # 7 years
    ) -> int:
        """
        Delete audit logs older than specified days
        
        Args:
            db: Database session
            days_to_keep: Number of days to keep (default 7 years)
            
        Returns:
            Number of deleted logs
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            deleted_count = db.query(AuditLog).filter(
                AuditLog.created_at < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(
                f"Deleted {deleted_count} old audit logs (older than {days_to_keep} days)",
                extra={
                    "deleted_count": deleted_count,
                    "cutoff_date": cutoff_date.isoformat(),
                }
            )
            
            return deleted_count
        except Exception as e:
            db.rollback()
            logger.error(
                f"Failed to delete old audit logs: {str(e)}",
                extra={
                    "days_to_keep": days_to_keep,
                    "error": str(e),
                }
            )
            raise

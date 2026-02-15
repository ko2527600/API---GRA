"""Integration module for submission queue with API endpoints"""
from typing import Dict, Any, Optional
from uuid import UUID
import json

from app.config import settings
from app.logger import get_logger
from app.services.task_queue import TaskQueueManager

logger = get_logger(__name__)


class SubmissionQueueIntegration:
    """Handles integration of submission queue with API endpoints"""
    
    @staticmethod
    def queue_submission(
        submission_id: str,
        business_id: UUID,
        submission_type: str,
        request_data: Dict[str, Any],
        content_type: str = "application/json",
        priority: int = 5,
    ) -> str:
        """
        Queue a submission for async processing
        
        Args:
            submission_id: Submission ID
            business_id: Business ID
            submission_type: Type of submission (INVOICE, REFUND, PURCHASE, etc)
            request_data: Request data (dict for JSON, str for XML)
            content_type: Content type (application/json or application/xml)
            priority: Task priority (0-10, higher = more important)
            
        Returns:
            Celery task ID
            
        Raises:
            ValueError: If submission type is not supported
        """
        if not settings.CELERY_ENABLED:
            logger.warning(
                "Celery is disabled, submission will not be queued",
                extra={
                    "submission_id": submission_id,
                    "business_id": str(business_id),
                }
            )
            return None
        
        manager = TaskQueueManager()
        
        logger.info(
            f"Queueing {submission_type} submission: {submission_id}",
            extra={
                "submission_id": submission_id,
                "business_id": str(business_id),
                "submission_type": submission_type,
                "content_type": content_type,
                "priority": priority,
            }
        )
        
        try:
            if content_type == "application/json":
                task_id = manager.queue_json_submission(
                    submission_id=submission_id,
                    business_id=str(business_id),
                    request_data=request_data,
                    priority=priority,
                )
            elif content_type == "application/xml":
                task_id = manager.queue_xml_submission(
                    submission_id=submission_id,
                    business_id=str(business_id),
                    request_data=request_data,
                    priority=priority,
                )
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
            
            logger.info(
                f"Submission queued successfully: {submission_id}",
                extra={
                    "submission_id": submission_id,
                    "task_id": task_id,
                }
            )
            
            return task_id
        
        except Exception as e:
            logger.error(
                f"Failed to queue submission: {submission_id}",
                extra={
                    "submission_id": submission_id,
                    "business_id": str(business_id),
                    "error": str(e),
                }
            )
            raise
    
    @staticmethod
    def get_submission_status(task_id: str) -> Dict[str, Any]:
        """
        Get status of a queued submission
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Task status information
        """
        if not settings.CELERY_ENABLED:
            logger.warning("Celery is disabled, cannot get task status")
            return None
        
        manager = TaskQueueManager()
        
        try:
            status = manager.get_task_status(task_id)
            
            logger.info(
                f"Retrieved submission status: {task_id}",
                extra={
                    "task_id": task_id,
                    "status": status.get("status"),
                }
            )
            
            return status
        
        except Exception as e:
            logger.error(
                f"Failed to get submission status: {task_id}",
                extra={
                    "task_id": task_id,
                    "error": str(e),
                }
            )
            raise
    
    @staticmethod
    def cancel_submission(task_id: str) -> bool:
        """
        Cancel a queued submission
        
        Args:
            task_id: Celery task ID
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        if not settings.CELERY_ENABLED:
            logger.warning("Celery is disabled, cannot cancel task")
            return False
        
        manager = TaskQueueManager()
        
        try:
            result = manager.cancel_task(task_id)
            
            logger.info(
                f"Submission cancelled: {task_id}",
                extra={"task_id": task_id}
            )
            
            return result
        
        except Exception as e:
            logger.error(
                f"Failed to cancel submission: {task_id}",
                extra={
                    "task_id": task_id,
                    "error": str(e),
                }
            )
            raise


def get_submission_queue_integration() -> SubmissionQueueIntegration:
    """Get submission queue integration instance"""
    return SubmissionQueueIntegration()

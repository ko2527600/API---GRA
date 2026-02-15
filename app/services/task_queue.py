"""Async task queue for submission processing using Celery"""
from celery import Celery, Task
from celery.exceptions import MaxRetriesExceededError
from typing import Dict, Any, Optional
from datetime import datetime
import json
from uuid import UUID

from app.config import settings
from app.logger import get_logger
from app.database import SessionLocal
from app.models.models import Submission
from app.services.submission_processor import SubmissionProcessor
from app.services.gra_client import GRAClientError, ErrorType

logger = get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "gra_api",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.SUBMISSION_PROCESSING_TIMEOUT,
    task_soft_time_limit=settings.SUBMISSION_PROCESSING_TIMEOUT - 10,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


class SubmissionTask(Task):
    """Base task class for submission processing"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": settings.MAX_RETRIES}
    retry_backoff = settings.RETRY_BACKOFF_BASE
    retry_backoff_max = settings.RETRY_BACKOFF_MAX
    retry_jitter = True
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(
            f"Task {task_id} retrying due to: {str(exc)}",
            extra={
                "task_id": task_id,
                "exception": str(exc),
                "retry_count": self.request.retries,
            }
        )
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails after all retries"""
        logger.error(
            f"Task {task_id} failed after {self.request.retries} retries",
            extra={
                "task_id": task_id,
                "exception": str(exc),
                "retry_count": self.request.retries,
            }
        )
        
        # Update submission status to FAILED
        try:
            db = SessionLocal()
            submission_id = args[1] if len(args) > 1 else kwargs.get("submission_id")
            
            if submission_id:
                submission = db.query(Submission).filter(
                    Submission.id == submission_id
                ).first()
                
                if submission:
                    submission.submission_status = "FAILED"
                    submission.error_details = json.dumps({
                        "error": str(exc),
                        "error_type": "TASK_FAILURE",
                        "retry_count": self.request.retries,
                    })
                    submission.completed_at = datetime.utcnow()
                    db.commit()
                    
                    logger.info(
                        f"Updated submission {submission_id} status to FAILED",
                        extra={"submission_id": str(submission_id)}
                    )
            
            db.close()
        except Exception as e:
            logger.error(
                f"Failed to update submission status on task failure: {str(e)}",
                extra={"exception": str(e)}
            )
    
    def on_success(self, result, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(
            f"Task {task_id} completed successfully",
            extra={"task_id": task_id}
        )


@celery_app.task(
    base=SubmissionTask,
    bind=True,
    name="process_json_submission",
)
def process_json_submission_task(
    self,
    submission_id: str,
    business_id: str,
    request_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Async task to process JSON submission to GRA
    
    Args:
        submission_id: Submission ID
        business_id: Business ID
        request_data: Request data to submit to GRA
        
    Returns:
        Response from GRA
        
    Raises:
        GRAClientError: If GRA submission fails
    """
    import asyncio
    
    logger.info(
        f"Processing JSON submission task: {submission_id}",
        extra={
            "submission_id": submission_id,
            "business_id": business_id,
            "task_id": self.request.id,
        }
    )
    
    try:
        db = SessionLocal()
        
        # Convert business_id string to UUID
        business_uuid = UUID(business_id)
        
        # Run async submission processor
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                SubmissionProcessor.process_json_submission(
                    db=db,
                    submission_id=submission_id,
                    business_id=business_uuid,
                    request_data=request_data,
                )
            )
            
            logger.info(
                f"JSON submission task completed: {submission_id}",
                extra={
                    "submission_id": submission_id,
                    "business_id": business_id,
                    "task_id": self.request.id,
                }
            )
            
            return result
        
        finally:
            loop.close()
            db.close()
    
    except GRAClientError as e:
        logger.error(
            f"GRA client error in submission task: {submission_id}",
            extra={
                "submission_id": submission_id,
                "business_id": business_id,
                "error": str(e),
                "error_type": e.error_type.value if e.error_type else None,
                "task_id": self.request.id,
            }
        )
        
        # Determine if error is retryable
        if e.is_retryable():
            # Retry with exponential backoff
            raise self.retry(exc=e)
        else:
            # Don't retry permanent errors
            raise
    
    except Exception as e:
        logger.error(
            f"Unexpected error in submission task: {submission_id}",
            extra={
                "submission_id": submission_id,
                "business_id": business_id,
                "error": str(e),
                "task_id": self.request.id,
            }
        )
        raise


@celery_app.task(
    base=SubmissionTask,
    bind=True,
    name="process_xml_submission",
)
def process_xml_submission_task(
    self,
    submission_id: str,
    business_id: str,
    request_data: str,
) -> Dict[str, Any]:
    """
    Async task to process XML submission to GRA
    
    Args:
        submission_id: Submission ID
        business_id: Business ID
        request_data: XML request data to submit to GRA
        
    Returns:
        Response from GRA
        
    Raises:
        GRAClientError: If GRA submission fails
    """
    import asyncio
    
    logger.info(
        f"Processing XML submission task: {submission_id}",
        extra={
            "submission_id": submission_id,
            "business_id": business_id,
            "task_id": self.request.id,
        }
    )
    
    try:
        db = SessionLocal()
        
        # Convert business_id string to UUID
        business_uuid = UUID(business_id)
        
        # Run async submission processor
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                SubmissionProcessor.process_xml_submission(
                    db=db,
                    submission_id=submission_id,
                    business_id=business_uuid,
                    request_data=request_data,
                )
            )
            
            logger.info(
                f"XML submission task completed: {submission_id}",
                extra={
                    "submission_id": submission_id,
                    "business_id": business_id,
                    "task_id": self.request.id,
                }
            )
            
            return result
        
        finally:
            loop.close()
            db.close()
    
    except GRAClientError as e:
        logger.error(
            f"GRA client error in XML submission task: {submission_id}",
            extra={
                "submission_id": submission_id,
                "business_id": business_id,
                "error": str(e),
                "error_type": e.error_type.value if e.error_type else None,
                "task_id": self.request.id,
            }
        )
        
        # Determine if error is retryable
        if e.is_retryable():
            # Retry with exponential backoff
            raise self.retry(exc=e)
        else:
            # Don't retry permanent errors
            raise
    
    except Exception as e:
        logger.error(
            f"Unexpected error in XML submission task: {submission_id}",
            extra={
                "submission_id": submission_id,
                "business_id": business_id,
                "error": str(e),
                "task_id": self.request.id,
            }
        )
        raise


class TaskQueueManager:
    """Manager for async task queue operations"""
    
    @staticmethod
    def queue_json_submission(
        submission_id: str,
        business_id: str,
        request_data: Dict[str, Any],
        priority: int = 5,
    ) -> str:
        """
        Queue a JSON submission for async processing
        
        Args:
            submission_id: Submission ID
            business_id: Business ID
            request_data: Request data to submit to GRA
            priority: Task priority (0-10, higher = more important)
            
        Returns:
            Celery task ID
        """
        logger.info(
            f"Queueing JSON submission: {submission_id}",
            extra={
                "submission_id": submission_id,
                "business_id": business_id,
                "priority": priority,
            }
        )
        
        task = process_json_submission_task.apply_async(
            args=[submission_id, business_id, request_data],
            priority=priority,
            task_id=f"json-{submission_id}",
        )
        
        logger.info(
            f"JSON submission queued with task ID: {task.id}",
            extra={
                "submission_id": submission_id,
                "task_id": task.id,
            }
        )
        
        return task.id
    
    @staticmethod
    def queue_xml_submission(
        submission_id: str,
        business_id: str,
        request_data: str,
        priority: int = 5,
    ) -> str:
        """
        Queue an XML submission for async processing
        
        Args:
            submission_id: Submission ID
            business_id: Business ID
            request_data: XML request data to submit to GRA
            priority: Task priority (0-10, higher = more important)
            
        Returns:
            Celery task ID
        """
        logger.info(
            f"Queueing XML submission: {submission_id}",
            extra={
                "submission_id": submission_id,
                "business_id": business_id,
                "priority": priority,
            }
        )
        
        task = process_xml_submission_task.apply_async(
            args=[submission_id, business_id, request_data],
            priority=priority,
            task_id=f"xml-{submission_id}",
        )
        
        logger.info(
            f"XML submission queued with task ID: {task.id}",
            extra={
                "submission_id": submission_id,
                "task_id": task.id,
            }
        )
        
        return task.id
    
    @staticmethod
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """
        Get status of a queued task
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Task status information
        """
        task = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": task.status,
            "result": task.result if task.successful() else None,
            "error": str(task.info) if task.failed() else None,
        }
    
    @staticmethod
    def cancel_task(task_id: str) -> bool:
        """
        Cancel a queued task
        
        Args:
            task_id: Celery task ID
            
        Returns:
            True if task was cancelled, False otherwise
        """
        task = celery_app.AsyncResult(task_id)
        task.revoke(terminate=True)
        
        logger.info(
            f"Task cancelled: {task_id}",
            extra={"task_id": task_id}
        )
        
        return True


def get_task_queue_manager() -> TaskQueueManager:
    """Get task queue manager instance"""
    return TaskQueueManager()

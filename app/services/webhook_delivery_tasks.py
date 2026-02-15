"""Celery tasks for webhook delivery"""
from celery import Task
from celery.exceptions import MaxRetriesExceededError
from typing import Dict, Any
from uuid import UUID
import json
from datetime import datetime
import asyncio

from app.services.task_queue import celery_app, SubmissionTask
from app.services.webhook_delivery import WebhookDeliveryService
from app.config import settings
from app.logger import get_logger
from app.database import SessionLocal
from app.models.models import Webhook, WebhookDelivery

logger = get_logger(__name__)


@celery_app.task(
    base=SubmissionTask,
    bind=True,
    name="deliver_webhook",
)
def deliver_webhook_task(
    self,
    webhook_id: str,
    event_type: str,
    submission_id: str,
    submission_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Async task to deliver webhook with retry logic.
    
    Args:
        webhook_id: Webhook ID
        event_type: Event type (e.g., 'invoice.success')
        submission_id: Submission ID
        submission_data: Submission details
        
    Returns:
        Delivery result
        
    Raises:
        Exception: If delivery fails
    """
    logger.info(
        f"Delivering webhook task: {webhook_id}",
        extra={
            "webhook_id": webhook_id,
            "event_type": event_type,
            "submission_id": submission_id,
            "task_id": self.request.id,
        }
    )
    
    try:
        db = SessionLocal()
        
        # Convert IDs from strings to UUIDs
        webhook_uuid = UUID(webhook_id)
        submission_uuid = UUID(submission_id)
        
        # Get webhook
        webhook = db.query(Webhook).filter(
            Webhook.id == webhook_uuid
        ).first()
        
        if not webhook:
            logger.error(
                f"Webhook not found: {webhook_id}",
                extra={"webhook_id": webhook_id}
            )
            raise ValueError(f"Webhook not found: {webhook_id}")
        
        # Run async delivery
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            delivery = loop.run_until_complete(
                WebhookDeliveryService.deliver_webhook(
                    db=db,
                    webhook=webhook,
                    event_type=event_type,
                    submission_id=submission_uuid,
                    submission_data=submission_data,
                )
            )
            
            logger.info(
                f"Webhook delivery task completed: {webhook_id}",
                extra={
                    "webhook_id": webhook_id,
                    "event_type": event_type,
                    "submission_id": submission_id,
                    "delivery_status": delivery.delivery_status,
                    "task_id": self.request.id,
                }
            )
            
            return {
                "delivery_id": str(delivery.id),
                "webhook_id": webhook_id,
                "event_type": event_type,
                "submission_id": submission_id,
                "delivery_status": delivery.delivery_status,
                "response_code": delivery.response_code,
                "retry_count": delivery.retry_count,
            }
        
        finally:
            loop.close()
            db.close()
    
    except Exception as e:
        logger.error(
            f"Error in webhook delivery task: {webhook_id}",
            extra={
                "webhook_id": webhook_id,
                "event_type": event_type,
                "submission_id": submission_id,
                "error": str(e),
                "task_id": self.request.id,
            }
        )
        raise


@celery_app.task(
    bind=True,
    name="retry_pending_webhook_deliveries",
)
def retry_pending_webhook_deliveries_task(self, limit: int = 100) -> Dict[str, Any]:
    """
    Async task to retry pending webhook deliveries.
    
    Args:
        limit: Maximum number of deliveries to retry
        
    Returns:
        Retry result
    """
    logger.info(
        f"Retrying pending webhook deliveries task",
        extra={
            "limit": limit,
            "task_id": self.request.id,
        }
    )
    
    try:
        db = SessionLocal()
        
        # Run async retry
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            retried_count = loop.run_until_complete(
                WebhookDeliveryService.retry_pending_deliveries(db, limit)
            )
            
            logger.info(
                f"Retry pending webhook deliveries task completed",
                extra={
                    "retried_count": retried_count,
                    "task_id": self.request.id,
                }
            )
            
            return {
                "retried_count": retried_count,
                "limit": limit,
            }
        
        finally:
            loop.close()
            db.close()
    
    except Exception as e:
        logger.error(
            f"Error in retry pending webhook deliveries task",
            extra={
                "error": str(e),
                "task_id": self.request.id,
            }
        )
        raise


class WebhookDeliveryTaskManager:
    """Manager for webhook delivery tasks"""
    
    @staticmethod
    def queue_webhook_delivery(
        webhook_id: str,
        event_type: str,
        submission_id: str,
        submission_data: Dict[str, Any],
        priority: int = 5,
    ) -> str:
        """
        Queue a webhook delivery task.
        
        Args:
            webhook_id: Webhook ID
            event_type: Event type
            submission_id: Submission ID
            submission_data: Submission details
            priority: Task priority (0-10, higher = more important)
            
        Returns:
            Celery task ID
        """
        logger.info(
            f"Queueing webhook delivery: {webhook_id}",
            extra={
                "webhook_id": webhook_id,
                "event_type": event_type,
                "submission_id": submission_id,
                "priority": priority,
            }
        )
        
        task = deliver_webhook_task.apply_async(
            args=[webhook_id, event_type, submission_id, submission_data],
            priority=priority,
            task_id=f"webhook-{webhook_id}-{submission_id}",
        )
        
        logger.info(
            f"Webhook delivery queued with task ID: {task.id}",
            extra={
                "webhook_id": webhook_id,
                "task_id": task.id,
            }
        )
        
        return task.id
    
    @staticmethod
    def queue_retry_pending_deliveries(limit: int = 100) -> str:
        """
        Queue a task to retry pending webhook deliveries.
        
        Args:
            limit: Maximum number of deliveries to retry
            
        Returns:
            Celery task ID
        """
        logger.info(
            f"Queueing retry pending webhook deliveries",
            extra={"limit": limit}
        )
        
        task = retry_pending_webhook_deliveries_task.apply_async(
            args=[limit],
            priority=3,
        )
        
        logger.info(
            f"Retry pending deliveries queued with task ID: {task.id}",
            extra={"task_id": task.id}
        )
        
        return task.id


def get_webhook_delivery_task_manager() -> WebhookDeliveryTaskManager:
    """Get webhook delivery task manager instance"""
    return WebhookDeliveryTaskManager()

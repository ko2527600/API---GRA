"""Service for managing webhook events"""
from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy.orm import Session
import json

from app.models.models import Submission, Webhook
from app.logger import logger


class WebhookEventManager:
    """Manager for triggering webhook events"""
    
    # Map submission types and statuses to event types
    EVENT_TYPE_MAP = {
        ("INVOICE", "SUCCESS"): "invoice.success",
        ("INVOICE", "FAILED"): "invoice.failed",
        ("REFUND", "SUCCESS"): "refund.success",
        ("REFUND", "FAILED"): "refund.failed",
        ("PURCHASE", "SUCCESS"): "purchase.success",
        ("PURCHASE", "FAILED"): "purchase.failed",
    }
    
    @staticmethod
    def get_event_type(submission_type: str, submission_status: str) -> str:
        """
        Get event type for a submission.
        
        Args:
            submission_type: Type of submission (INVOICE, REFUND, PURCHASE, etc)
            submission_status: Status of submission (SUCCESS, FAILED)
            
        Returns:
            Event type string (e.g., 'invoice.success')
            
        Raises:
            ValueError: If event type not supported
        """
        key = (submission_type, submission_status)
        if key not in WebhookEventManager.EVENT_TYPE_MAP:
            raise ValueError(
                f"Unsupported event: {submission_type}.{submission_status}"
            )
        return WebhookEventManager.EVENT_TYPE_MAP[key]
    
    @staticmethod
    def build_submission_data(
        db: Session,
        submission: Submission,
    ) -> Dict[str, Any]:
        """
        Build submission data for webhook payload.
        
        Args:
            db: Database session
            submission: Submission record
            
        Returns:
            Dictionary with submission details
        """
        data = {
            "submission_id": str(submission.id),
            "submission_type": submission.submission_type,
            "status": submission.submission_status,
            "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
            "completed_at": submission.completed_at.isoformat() if submission.completed_at else None,
        }
        
        # Add GRA response details if available
        if submission.gra_response_code:
            data["gra_response_code"] = submission.gra_response_code
        
        if submission.gra_response_message:
            data["gra_response_message"] = submission.gra_response_message
        
        if submission.gra_invoice_id:
            data["gra_invoice_id"] = submission.gra_invoice_id
        
        if submission.gra_qr_code:
            data["gra_qr_code"] = submission.gra_qr_code
        
        if submission.gra_receipt_num:
            data["gra_receipt_num"] = submission.gra_receipt_num
        
        # Add error details if submission failed
        if submission.submission_status == "FAILED" and submission.error_details:
            try:
                data["error_details"] = json.loads(submission.error_details)
            except (json.JSONDecodeError, TypeError):
                data["error_details"] = submission.error_details
        
        return data
    
    @staticmethod
    def get_webhooks_for_event(
        db: Session,
        business_id: UUID,
        event_type: str,
    ) -> List[Webhook]:
        """
        Get all active webhooks subscribed to an event.
        
        Args:
            db: Database session
            business_id: Business ID
            event_type: Event type (e.g., 'invoice.success')
            
        Returns:
            List of Webhook records
        """
        webhooks = db.query(Webhook).filter(
            Webhook.business_id == business_id,
            Webhook.is_active == True,
        ).all()
        
        # Filter webhooks that have the event in their events list
        return [w for w in webhooks if event_type in w.events]
    
    @staticmethod
    def trigger_webhook_event(
        db: Session,
        submission: Submission,
    ) -> int:
        """
        Trigger webhook events for a submission.
        
        Args:
            db: Database session
            submission: Submission record
            
        Returns:
            Number of webhooks triggered
            
        Raises:
            ValueError: If event type not supported
        """
        # Lazy import to avoid circular dependency
        from app.services.webhook_delivery_tasks import WebhookDeliveryTaskManager
        
        try:
            # Get event type
            event_type = WebhookEventManager.get_event_type(
                submission.submission_type,
                submission.submission_status,
            )
            
            logger.info(
                f"Triggering webhook event: {event_type}",
                extra={
                    "submission_id": str(submission.id),
                    "business_id": str(submission.business_id),
                    "event_type": event_type,
                }
            )
            
            # Get webhooks subscribed to this event
            webhooks = WebhookEventManager.get_webhooks_for_event(
                db,
                submission.business_id,
                event_type,
            )
            
            if not webhooks:
                logger.info(
                    f"No webhooks subscribed to event: {event_type}",
                    extra={
                        "submission_id": str(submission.id),
                        "business_id": str(submission.business_id),
                        "event_type": event_type,
                    }
                )
                return 0
            
            # Build submission data
            submission_data = WebhookEventManager.build_submission_data(db, submission)
            
            # Queue webhook deliveries
            task_manager = WebhookDeliveryTaskManager()
            triggered_count = 0
            
            for webhook in webhooks:
                try:
                    task_manager.queue_webhook_delivery(
                        webhook_id=str(webhook.id),
                        event_type=event_type,
                        submission_id=str(submission.id),
                        submission_data=submission_data,
                        priority=5,
                    )
                    triggered_count += 1
                    
                    logger.info(
                        f"Webhook event queued: {webhook.id}",
                        extra={
                            "webhook_id": str(webhook.id),
                            "submission_id": str(submission.id),
                            "event_type": event_type,
                        }
                    )
                
                except Exception as e:
                    logger.error(
                        f"Error queueing webhook event: {webhook.id}",
                        extra={
                            "webhook_id": str(webhook.id),
                            "submission_id": str(submission.id),
                            "event_type": event_type,
                            "error": str(e),
                        }
                    )
            
            logger.info(
                f"Webhook events triggered: {triggered_count}",
                extra={
                    "submission_id": str(submission.id),
                    "business_id": str(submission.business_id),
                    "event_type": event_type,
                    "triggered_count": triggered_count,
                }
            )
            
            return triggered_count
        
        except ValueError as e:
            logger.warning(
                f"Unsupported event for webhook: {str(e)}",
                extra={
                    "submission_id": str(submission.id),
                    "submission_type": submission.submission_type,
                    "submission_status": submission.submission_status,
                }
            )
            return 0
        
        except Exception as e:
            logger.error(
                f"Error triggering webhook event: {str(e)}",
                extra={
                    "submission_id": str(submission.id),
                    "business_id": str(submission.business_id),
                    "error": str(e),
                }
            )
            return 0

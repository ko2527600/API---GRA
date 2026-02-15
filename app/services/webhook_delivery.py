"""Webhook delivery service with retry logic"""
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
import asyncio

from app.models.models import WebhookDelivery, Webhook, Submission
from app.logger import logger
from app.config import settings
from app.utils.hmac_signature import HMACSignatureManager


class WebhookDeliveryService:
    """Service for delivering webhooks with retry logic"""
    
    # Exponential backoff delays in seconds: 1s, 2s, 4s, 8s, 16s
    RETRY_DELAYS = [1, 2, 4, 8, 16]
    
    @staticmethod
    def calculate_next_retry_time(retry_count: int) -> datetime:
        """
        Calculate next retry time based on retry count.
        
        Args:
            retry_count: Current retry count (0-based)
            
        Returns:
            datetime: Next retry time
        """
        if retry_count >= len(WebhookDeliveryService.RETRY_DELAYS):
            # Use max delay for retries beyond the list
            delay_seconds = WebhookDeliveryService.RETRY_DELAYS[-1]
        else:
            delay_seconds = WebhookDeliveryService.RETRY_DELAYS[retry_count]
        
        return datetime.utcnow() + timedelta(seconds=delay_seconds)
    
    @staticmethod
    def create_webhook_payload(
        event_type: str,
        submission_id: UUID,
        submission_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create webhook payload for delivery.
        
        Args:
            event_type: Type of event (e.g., 'invoice.success')
            submission_id: Submission ID
            submission_data: Submission details
            
        Returns:
            Webhook payload
        """
        return {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "submission_id": str(submission_id),
            "data": submission_data,
        }
    
    @staticmethod
    def generate_webhook_signature(
        payload: Dict[str, Any],
        webhook_secret: str,
    ) -> str:
        """
        Generate HMAC signature for webhook payload.
        
        Args:
            payload: Webhook payload
            webhook_secret: Webhook secret for HMAC
            
        Returns:
            HMAC signature
        """
        payload_json = json.dumps(payload, sort_keys=True)
        signature = HMACSignatureManager.generate_signature(
            webhook_secret,
            payload_json,
        )
        return signature
    
    @staticmethod
    async def deliver_webhook(
        db: Session,
        webhook: Webhook,
        event_type: str,
        submission_id: UUID,
        submission_data: Dict[str, Any],
    ) -> WebhookDelivery:
        """
        Deliver webhook with retry logic.
        
        Args:
            db: Database session
            webhook: Webhook to deliver to
            event_type: Type of event
            submission_id: Submission ID
            submission_data: Submission details
            
        Returns:
            WebhookDelivery record
            
        Raises:
            Exception: If delivery fails after all retries
        """
        # Create webhook payload
        payload = WebhookDeliveryService.create_webhook_payload(
            event_type=event_type,
            submission_id=submission_id,
            submission_data=submission_data,
        )
        
        # Generate signature
        signature = WebhookDeliveryService.generate_webhook_signature(
            payload,
            webhook.secret,
        )
        
        # Create webhook delivery record
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=event_type,
            submission_id=submission_id,
            payload=payload,
            delivery_status="PENDING",
            retry_count=0,
        )
        
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        
        logger.info(
            f"Created webhook delivery record: {delivery.id}",
            extra={
                "delivery_id": str(delivery.id),
                "webhook_id": str(webhook.id),
                "event_type": event_type,
                "submission_id": str(submission_id),
            }
        )
        
        # Attempt delivery with retries
        max_attempts = settings.WEBHOOK_MAX_RETRIES
        
        for attempt in range(max_attempts):
            try:
                logger.info(
                    f"Attempting webhook delivery (attempt {attempt + 1}/{max_attempts}): {delivery.id}",
                    extra={
                        "delivery_id": str(delivery.id),
                        "webhook_id": str(webhook.id),
                        "attempt": attempt + 1,
                        "max_attempts": max_attempts,
                    }
                )
                
                # Attempt delivery
                response_code, response_body = await WebhookDeliveryService._send_webhook(
                    webhook_url=webhook.webhook_url,
                    payload=payload,
                    signature=signature,
                    timeout=settings.WEBHOOK_TIMEOUT,
                )
                
                # Check if delivery was successful
                if response_code == 200:
                    delivery.delivery_status = "SUCCESS"
                    delivery.response_code = response_code
                    delivery.response_body = response_body
                    delivery.last_attempt_at = datetime.utcnow()
                    db.commit()
                    
                    logger.info(
                        f"Webhook delivery successful: {delivery.id}",
                        extra={
                            "delivery_id": str(delivery.id),
                            "webhook_id": str(webhook.id),
                            "response_code": response_code,
                        }
                    )
                    
                    return delivery
                else:
                    # Non-200 response, retry if not last attempt
                    delivery.response_code = response_code
                    delivery.response_body = response_body
                    delivery.last_attempt_at = datetime.utcnow()
                    delivery.retry_count = attempt + 1
                    
                    if attempt < max_attempts - 1:
                        # Schedule next retry
                        delivery.next_retry_at = WebhookDeliveryService.calculate_next_retry_time(attempt)
                        delivery.delivery_status = "PENDING"
                        db.commit()
                        
                        logger.warning(
                            f"Webhook delivery failed with status {response_code}, scheduling retry: {delivery.id}",
                            extra={
                                "delivery_id": str(delivery.id),
                                "webhook_id": str(webhook.id),
                                "response_code": response_code,
                                "next_retry_at": delivery.next_retry_at.isoformat(),
                            }
                        )
                        
                        # Wait before next retry
                        await asyncio.sleep(WebhookDeliveryService.RETRY_DELAYS[attempt])
                    else:
                        # Last attempt failed
                        delivery.delivery_status = "FAILED"
                        db.commit()
                        
                        logger.error(
                            f"Webhook delivery failed after {max_attempts} attempts: {delivery.id}",
                            extra={
                                "delivery_id": str(delivery.id),
                                "webhook_id": str(webhook.id),
                                "response_code": response_code,
                                "max_attempts": max_attempts,
                            }
                        )
                        
                        return delivery
            
            except asyncio.TimeoutError:
                logger.warning(
                    f"Webhook delivery timeout (attempt {attempt + 1}/{max_attempts}): {delivery.id}",
                    extra={
                        "delivery_id": str(delivery.id),
                        "webhook_id": str(webhook.id),
                        "attempt": attempt + 1,
                        "timeout": settings.WEBHOOK_TIMEOUT,
                    }
                )
                
                delivery.last_attempt_at = datetime.utcnow()
                delivery.retry_count = attempt + 1
                
                if attempt < max_attempts - 1:
                    # Schedule next retry
                    delivery.next_retry_at = WebhookDeliveryService.calculate_next_retry_time(attempt)
                    delivery.delivery_status = "PENDING"
                    db.commit()
                    
                    # Wait before next retry
                    await asyncio.sleep(WebhookDeliveryService.RETRY_DELAYS[attempt])
                else:
                    # Last attempt failed
                    delivery.delivery_status = "FAILED"
                    db.commit()
                    
                    logger.error(
                        f"Webhook delivery failed after {max_attempts} timeout attempts: {delivery.id}",
                        extra={
                            "delivery_id": str(delivery.id),
                            "webhook_id": str(webhook.id),
                            "max_attempts": max_attempts,
                        }
                    )
                    
                    return delivery
            
            except Exception as e:
                logger.error(
                    f"Webhook delivery error (attempt {attempt + 1}/{max_attempts}): {delivery.id}",
                    extra={
                        "delivery_id": str(delivery.id),
                        "webhook_id": str(webhook.id),
                        "attempt": attempt + 1,
                        "error": str(e),
                    }
                )
                
                delivery.last_attempt_at = datetime.utcnow()
                delivery.retry_count = attempt + 1
                
                if attempt < max_attempts - 1:
                    # Schedule next retry
                    delivery.next_retry_at = WebhookDeliveryService.calculate_next_retry_time(attempt)
                    delivery.delivery_status = "PENDING"
                    db.commit()
                    
                    # Wait before next retry
                    await asyncio.sleep(WebhookDeliveryService.RETRY_DELAYS[attempt])
                else:
                    # Last attempt failed
                    delivery.delivery_status = "FAILED"
                    db.commit()
                    
                    logger.error(
                        f"Webhook delivery failed after {max_attempts} attempts: {delivery.id}",
                        extra={
                            "delivery_id": str(delivery.id),
                            "webhook_id": str(webhook.id),
                            "max_attempts": max_attempts,
                            "error": str(e),
                        }
                    )
                    
                    return delivery
        
        return delivery
    
    @staticmethod
    async def _send_webhook(
        webhook_url: str,
        payload: Dict[str, Any],
        signature: str,
        timeout: int,
    ) -> tuple[int, str]:
        """
        Send webhook HTTP request.
        
        Args:
            webhook_url: URL to send webhook to
            payload: Webhook payload
            signature: HMAC signature
            timeout: Request timeout in seconds
            
        Returns:
            Tuple of (response_code, response_body)
            
        Raises:
            Exception: If request fails
        """
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
        }
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                webhook_url,
                json=payload,
                headers=headers,
            )
            
            return response.status_code, response.text
    
    @staticmethod
    def get_pending_deliveries(
        db: Session,
        limit: int = 100,
    ) -> List[WebhookDelivery]:
        """
        Get pending webhook deliveries that are ready to retry.
        
        Args:
            db: Database session
            limit: Maximum number of deliveries to return
            
        Returns:
            List of pending WebhookDelivery records
        """
        now = datetime.utcnow()
        
        return db.query(WebhookDelivery).filter(
            WebhookDelivery.delivery_status == "PENDING",
            (WebhookDelivery.next_retry_at.is_(None)) | (WebhookDelivery.next_retry_at <= now),
        ).order_by(
            WebhookDelivery.next_retry_at.asc().nullsfirst(),
            WebhookDelivery.created_at.asc(),
        ).limit(limit).all()
    
    @staticmethod
    async def retry_pending_deliveries(
        db: Session,
        limit: int = 100,
    ) -> int:
        """
        Retry pending webhook deliveries.
        
        Args:
            db: Database session
            limit: Maximum number of deliveries to retry
            
        Returns:
            Number of deliveries retried
        """
        pending_deliveries = WebhookDeliveryService.get_pending_deliveries(db, limit)
        
        logger.info(
            f"Found {len(pending_deliveries)} pending webhook deliveries to retry",
            extra={"count": len(pending_deliveries)}
        )
        
        retried_count = 0
        
        for delivery in pending_deliveries:
            try:
                webhook = db.query(Webhook).filter(
                    Webhook.id == delivery.webhook_id
                ).first()
                
                if not webhook:
                    logger.warning(
                        f"Webhook not found for delivery: {delivery.id}",
                        extra={"delivery_id": str(delivery.id)}
                    )
                    delivery.delivery_status = "FAILED"
                    db.commit()
                    continue
                
                # Retry delivery
                await WebhookDeliveryService._retry_delivery(db, delivery, webhook)
                retried_count += 1
            
            except Exception as e:
                logger.error(
                    f"Error retrying webhook delivery: {delivery.id}",
                    extra={
                        "delivery_id": str(delivery.id),
                        "error": str(e),
                    }
                )
        
        logger.info(
            f"Retried {retried_count} webhook deliveries",
            extra={"retried_count": retried_count}
        )
        
        return retried_count
    
    @staticmethod
    async def _retry_delivery(
        db: Session,
        delivery: WebhookDelivery,
        webhook: Webhook,
    ) -> None:
        """
        Retry a single webhook delivery.
        
        Args:
            db: Database session
            delivery: WebhookDelivery record
            webhook: Webhook record
        """
        max_attempts = settings.WEBHOOK_MAX_RETRIES
        
        if delivery.retry_count >= max_attempts:
            logger.warning(
                f"Webhook delivery has exceeded max retries: {delivery.id}",
                extra={
                    "delivery_id": str(delivery.id),
                    "retry_count": delivery.retry_count,
                    "max_attempts": max_attempts,
                }
            )
            delivery.delivery_status = "FAILED"
            db.commit()
            return
        
        try:
            logger.info(
                f"Retrying webhook delivery: {delivery.id}",
                extra={
                    "delivery_id": str(delivery.id),
                    "webhook_id": str(webhook.id),
                    "retry_count": delivery.retry_count,
                }
            )
            
            # Attempt delivery
            response_code, response_body = await WebhookDeliveryService._send_webhook(
                webhook_url=webhook.webhook_url,
                payload=delivery.payload,
                signature=WebhookDeliveryService.generate_webhook_signature(
                    delivery.payload,
                    webhook.secret,
                ),
                timeout=settings.WEBHOOK_TIMEOUT,
            )
            
            # Check if delivery was successful
            if response_code == 200:
                delivery.delivery_status = "SUCCESS"
                delivery.response_code = response_code
                delivery.response_body = response_body
                delivery.last_attempt_at = datetime.utcnow()
                db.commit()
                
                logger.info(
                    f"Webhook delivery retry successful: {delivery.id}",
                    extra={
                        "delivery_id": str(delivery.id),
                        "webhook_id": str(webhook.id),
                        "response_code": response_code,
                    }
                )
            else:
                # Non-200 response, schedule next retry
                delivery.response_code = response_code
                delivery.response_body = response_body
                delivery.last_attempt_at = datetime.utcnow()
                delivery.retry_count += 1
                
                if delivery.retry_count < max_attempts:
                    # Schedule next retry
                    delivery.next_retry_at = WebhookDeliveryService.calculate_next_retry_time(
                        delivery.retry_count - 1
                    )
                    delivery.delivery_status = "PENDING"
                    db.commit()
                    
                    logger.warning(
                        f"Webhook delivery retry failed with status {response_code}, scheduling next retry: {delivery.id}",
                        extra={
                            "delivery_id": str(delivery.id),
                            "webhook_id": str(webhook.id),
                            "response_code": response_code,
                            "next_retry_at": delivery.next_retry_at.isoformat(),
                        }
                    )
                else:
                    # Max retries exceeded
                    delivery.delivery_status = "FAILED"
                    db.commit()
                    
                    logger.error(
                        f"Webhook delivery retry failed after max attempts: {delivery.id}",
                        extra={
                            "delivery_id": str(delivery.id),
                            "webhook_id": str(webhook.id),
                            "response_code": response_code,
                            "max_attempts": max_attempts,
                        }
                    )
        
        except asyncio.TimeoutError:
            logger.warning(
                f"Webhook delivery retry timeout: {delivery.id}",
                extra={
                    "delivery_id": str(delivery.id),
                    "webhook_id": str(webhook.id),
                    "timeout": settings.WEBHOOK_TIMEOUT,
                }
            )
            
            delivery.last_attempt_at = datetime.utcnow()
            delivery.retry_count += 1
            
            if delivery.retry_count < max_attempts:
                # Schedule next retry
                delivery.next_retry_at = WebhookDeliveryService.calculate_next_retry_time(
                    delivery.retry_count - 1
                )
                delivery.delivery_status = "PENDING"
                db.commit()
            else:
                # Max retries exceeded
                delivery.delivery_status = "FAILED"
                db.commit()
                
                logger.error(
                    f"Webhook delivery retry failed after max timeout attempts: {delivery.id}",
                    extra={
                        "delivery_id": str(delivery.id),
                        "webhook_id": str(webhook.id),
                        "max_attempts": max_attempts,
                    }
                )
        
        except Exception as e:
            logger.error(
                f"Error retrying webhook delivery: {delivery.id}",
                extra={
                    "delivery_id": str(delivery.id),
                    "webhook_id": str(webhook.id),
                    "error": str(e),
                }
            )
            
            delivery.last_attempt_at = datetime.utcnow()
            delivery.retry_count += 1
            
            if delivery.retry_count < max_attempts:
                # Schedule next retry
                delivery.next_retry_at = WebhookDeliveryService.calculate_next_retry_time(
                    delivery.retry_count - 1
                )
                delivery.delivery_status = "PENDING"
                db.commit()
            else:
                # Max retries exceeded
                delivery.delivery_status = "FAILED"
                db.commit()

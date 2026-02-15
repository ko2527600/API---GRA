"""Webhook management service"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import secrets
from typing import List, Optional, Dict, Any

from app.models.models import Webhook, Business
from app.logger import logger


class WebhookService:
    """Service for managing webhooks"""
    
    @staticmethod
    def register_webhook(
        db: Session,
        business_id: UUID,
        webhook_url: str,
        events: List[str]
    ) -> Webhook:
        """
        Register a new webhook for a business.
        
        Args:
            db: Database session
            business_id: Business ID
            webhook_url: URL to send webhook notifications to
            events: List of event types to subscribe to
            
        Returns:
            Webhook: Created webhook object
            
        Raises:
            ValueError: If business not found or webhook URL invalid
            IntegrityError: If webhook registration fails
        """
        try:
            # Verify business exists
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business:
                raise ValueError(f"Business with ID {business_id} not found")
            
            # Generate webhook secret for HMAC signature
            webhook_secret = secrets.token_urlsafe(32)
            
            # Create webhook
            webhook = Webhook(
                business_id=business_id,
                webhook_url=webhook_url,
                events=events,
                secret=webhook_secret,
                is_active=True
            )
            
            db.add(webhook)
            db.commit()
            db.refresh(webhook)
            
            logger.info(f"Webhook registered for business {business_id}: {webhook.id}")
            return webhook
            
        except ValueError:
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Webhook registration failed - integrity error: {str(e)}")
            raise ValueError("Failed to register webhook - duplicate or invalid data")
        except Exception as e:
            db.rollback()
            logger.error(f"Error registering webhook: {str(e)}")
            raise
    
    @staticmethod
    def get_webhook(
        db: Session,
        webhook_id: UUID,
        business_id: UUID
    ) -> Optional[Webhook]:
        """
        Get a webhook by ID, ensuring it belongs to the business.
        
        Args:
            db: Database session
            webhook_id: Webhook ID
            business_id: Business ID (for multi-tenant isolation)
            
        Returns:
            Webhook: Webhook object or None if not found
        """
        return db.query(Webhook).filter(
            Webhook.id == webhook_id,
            Webhook.business_id == business_id
        ).first()
    
    @staticmethod
    def list_webhooks(
        db: Session,
        business_id: UUID
    ) -> List[Webhook]:
        """
        List all webhooks for a business.
        
        Args:
            db: Database session
            business_id: Business ID
            
        Returns:
            List[Webhook]: List of webhooks
        """
        return db.query(Webhook).filter(
            Webhook.business_id == business_id
        ).order_by(Webhook.created_at.desc()).all()
    
    @staticmethod
    def update_webhook(
        db: Session,
        webhook_id: UUID,
        business_id: UUID,
        webhook_url: Optional[str] = None,
        events: Optional[List[str]] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Webhook]:
        """
        Update a webhook.
        
        Args:
            db: Database session
            webhook_id: Webhook ID
            business_id: Business ID (for multi-tenant isolation)
            webhook_url: New webhook URL (optional)
            events: New list of events (optional)
            is_active: New active status (optional)
            
        Returns:
            Webhook: Updated webhook object or None if not found
            
        Raises:
            ValueError: If update fails
        """
        try:
            webhook = db.query(Webhook).filter(
                Webhook.id == webhook_id,
                Webhook.business_id == business_id
            ).first()
            
            if not webhook:
                return None
            
            if webhook_url is not None:
                webhook.webhook_url = webhook_url
            
            if events is not None:
                webhook.events = events
            
            if is_active is not None:
                webhook.is_active = is_active
            
            db.commit()
            db.refresh(webhook)
            
            logger.info(f"Webhook updated: {webhook_id}")
            return webhook
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating webhook: {str(e)}")
            raise ValueError(f"Failed to update webhook: {str(e)}")
    
    @staticmethod
    def delete_webhook(
        db: Session,
        webhook_id: UUID,
        business_id: UUID
    ) -> bool:
        """
        Delete a webhook.
        
        Args:
            db: Database session
            webhook_id: Webhook ID
            business_id: Business ID (for multi-tenant isolation)
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            ValueError: If deletion fails
        """
        try:
            webhook = db.query(Webhook).filter(
                Webhook.id == webhook_id,
                Webhook.business_id == business_id
            ).first()
            
            if not webhook:
                return False
            
            db.delete(webhook)
            db.commit()
            
            logger.info(f"Webhook deleted: {webhook_id}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting webhook: {str(e)}")
            raise ValueError(f"Failed to delete webhook: {str(e)}")
    
    @staticmethod
    def get_active_webhooks_for_event(
        db: Session,
        business_id: UUID,
        event_type: str
    ) -> List[Webhook]:
        """
        Get all active webhooks for a business that are subscribed to an event.
        
        Args:
            db: Database session
            business_id: Business ID
            event_type: Event type to filter by
            
        Returns:
            List[Webhook]: List of active webhooks subscribed to the event
        """
        webhooks = db.query(Webhook).filter(
            Webhook.business_id == business_id,
            Webhook.is_active == True
        ).all()
        
        # Filter webhooks that have the event in their events list
        return [w for w in webhooks if event_type in w.events]

#!/usr/bin/env python
"""Script to write the webhooks.py file"""

content = '''"""Webhook management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.middleware.auth_dependency import verify_auth
from app.schemas.webhook import (
    WebhookRegisterRequest,
    WebhookResponse,
    WebhookUpdateRequest,
    WebhookListResponse,
    WebhookDeleteResponse
)
from app.services.webhook_service import WebhookService
from app.logger import logger
from datetime import datetime

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post(
    "/register",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a webhook",
    description="Register a new webhook URL for receiving notifications on specific events"
)
def register_webhook(
    request: WebhookRegisterRequest,
    business_id: UUID = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Register a new webhook for a business."""
    try:
        webhook = WebhookService.register_webhook(
            db=db,
            business_id=business_id,
            webhook_url=request.webhook_url,
            events=request.events
        )
        
        logger.info(f"Webhook registered for business {business_id}: {webhook.id}")
        
        return WebhookResponse(
            webhook_id=str(webhook.id),
            webhook_url=webhook.webhook_url,
            events=webhook.events,
            is_active=webhook.is_active,
            created_at=webhook.created_at
        )
        
    except ValueError as e:
        logger.warning(f"Webhook registration validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error registering webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register webhook"
        )


@router.get(
    "",
    response_model=List[WebhookListResponse],
    status_code=status.HTTP_200_OK,
    summary="List webhooks",
    description="Get all webhooks registered for the business"
)
def list_webhooks(
    business_id: UUID = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """List all webhooks for a business."""
    try:
        webhooks = WebhookService.list_webhooks(db=db, business_id=business_id)
        
        return [
            WebhookListResponse(
                webhook_id=str(webhook.id),
                webhook_url=webhook.webhook_url,
                events=webhook.events,
                is_active=webhook.is_active,
                created_at=webhook.created_at,
                updated_at=webhook.updated_at
            )
            for webhook in webhooks
        ]
        
    except Exception as e:
        logger.error(f"Error listing webhooks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list webhooks"
        )


@router.get(
    "/{webhook_id}",
    response_model=WebhookListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get webhook details",
    description="Get details of a specific webhook"
)
def get_webhook(
    webhook_id: UUID,
    business_id: UUID = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Get a specific webhook by ID."""
    try:
        webhook = WebhookService.get_webhook(
            db=db,
            webhook_id=webhook_id,
            business_id=business_id
        )
        
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        
        return WebhookListResponse(
            webhook_id=str(webhook.id),
            webhook_url=webhook.webhook_url,
            events=webhook.events,
            is_active=webhook.is_active,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve webhook"
        )


@router.put(
    "/{webhook_id}",
    response_model=WebhookListResponse,
    status_code=status.HTTP_200_OK,
    summary="Update webhook",
    description="Update webhook URL, events, or active status"
)
def update_webhook(
    webhook_id: UUID,
    request: WebhookUpdateRequest,
    business_id: UUID = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Update a webhook."""
    try:
        webhook = WebhookService.update_webhook(
            db=db,
            webhook_id=webhook_id,
            business_id=business_id,
            webhook_url=request.webhook_url,
            events=request.events,
            is_active=request.is_active
        )
        
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        
        logger.info(f"Webhook updated: {webhook_id}")
        
        return WebhookListResponse(
            webhook_id=str(webhook.id),
            webhook_url=webhook.webhook_url,
            events=webhook.events,
            is_active=webhook.is_active,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Webhook update validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update webhook"
        )


@router.delete(
    "/{webhook_id}",
    response_model=WebhookDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete webhook",
    description="Delete a webhook registration"
)
def delete_webhook(
    webhook_id: UUID,
    business_id: UUID = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Delete a webhook."""
    try:
        deleted = WebhookService.delete_webhook(
            db=db,
            webhook_id=webhook_id,
            business_id=business_id
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )
        
        logger.info(f"Webhook deleted: {webhook_id}")
        
        return WebhookDeleteResponse(
            webhook_id=str(webhook_id),
            message="Webhook successfully deleted",
            deleted_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Webhook deletion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete webhook"
        )
'''

with open('app/api/endpoints/webhooks.py', 'w') as f:
    f.write(content)

print("File written successfully")
print(f"File size: {len(content)} bytes")

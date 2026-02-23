"""Webhook management endpoints"""
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


@router.post("/register", response_model=WebhookResponse, status_code=201)
async def register_webhook(
    request_data: WebhookRegisterRequest,
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """
    Register a new webhook for the business.
    
    Args:
        request_data: Webhook registration data
        business: Authenticated business data
        db: Database session
        
    Returns:
        WebhookResponse: Created webhook details
    """
    try:
        webhook = WebhookService.register_webhook(
            db=db,
            business_id=UUID(business["id"]),
            webhook_url=request_data.webhook_url,
            events=request_data.events
        )
        
        return WebhookResponse(
            webhook_id=str(webhook.id),
            webhook_url=webhook.webhook_url,
            events=webhook.events,
            is_active=webhook.is_active,
            created_at=webhook.created_at.isoformat() if webhook.created_at else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register webhook")


@router.get("/list", response_model=dict)
async def list_webhooks(
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """
    List all webhooks for the business.
    
    Args:
        business: Authenticated business data
        db: Database session
        
    Returns:
        dict: List of webhooks
    """
    try:
        webhooks = WebhookService.list_webhooks(
            db=db,
            business_id=UUID(business["id"])
        )
        
        return {
            "webhooks": [
                {
                    "webhook_id": str(w.id),
                    "webhook_url": w.webhook_url,
                    "events": w.events,
                    "is_active": w.is_active,
                    "created_at": w.created_at.isoformat() if w.created_at else None,
                    "updated_at": w.updated_at.isoformat() if w.updated_at else None
                }
                for w in webhooks
            ]
        }
    except Exception as e:
        logger.error(f"Error listing webhooks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list webhooks")


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: UUID,
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """
    Get a specific webhook.
    
    Args:
        webhook_id: Webhook ID to retrieve
        business: Authenticated business data
        db: Database session
        
    Returns:
        WebhookResponse: Webhook details
    """
    try:
        webhook = WebhookService.get_webhook(
            db=db,
            webhook_id=webhook_id,
            business_id=UUID(business["id"])
        )
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        return WebhookResponse(
            webhook_id=str(webhook.id),
            webhook_url=webhook.webhook_url,
            events=webhook.events,
            is_active=webhook.is_active,
            created_at=webhook.created_at.isoformat() if webhook.created_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve webhook")



@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    request_data: WebhookUpdateRequest,
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """
    Update a webhook.
    
    Args:
        webhook_id: Webhook ID to update
        request_data: Updated webhook data
        business: Authenticated business data
        db: Database session
        
    Returns:
        WebhookResponse: Updated webhook details
    """
    try:
        webhook = WebhookService.update_webhook(
            db=db,
            webhook_id=webhook_id,
            business_id=UUID(business["id"]),
            webhook_url=request_data.webhook_url,
            events=request_data.events,
            is_active=request_data.is_active
        )
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        return WebhookResponse(
            webhook_id=str(webhook.id),
            webhook_url=webhook.webhook_url,
            events=webhook.events,
            is_active=webhook.is_active,
            created_at=webhook.created_at.isoformat() if webhook.created_at else None
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update webhook")


@router.delete("/{webhook_id}", response_model=WebhookDeleteResponse)
async def delete_webhook(
    webhook_id: UUID,
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """
    Delete a webhook.
    
    Args:
        webhook_id: Webhook ID to delete
        business: Authenticated business data
        db: Database session
        
    Returns:
        WebhookDeleteResponse: Deletion confirmation
    """
    try:
        deleted = WebhookService.delete_webhook(
            db=db,
            webhook_id=webhook_id,
            business_id=UUID(business["id"])
        )
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        return WebhookDeleteResponse(
            webhook_id=str(webhook_id),
            message="Webhook successfully deleted",
            deleted_at=datetime.utcnow().isoformat() + "Z"
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete webhook")

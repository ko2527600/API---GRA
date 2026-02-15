"""Schemas for Webhook management"""
from pydantic import BaseModel, Field, HttpUrl, validator
from typing import Optional, List
from datetime import datetime


class WebhookRegisterRequest(BaseModel):
    """Request to register a webhook"""
    webhook_url: str = Field(..., description="Webhook URL to receive notifications")
    events: List[str] = Field(
        ...,
        min_items=1,
        description="List of event types to subscribe to (e.g., invoice.success, invoice.failed)"
    )
    
    @validator("webhook_url")
    def validate_webhook_url(cls, v):
        """Validate webhook URL format"""
        if not v.startswith(("http://", "https://")):
            raise ValueError("Webhook URL must start with http:// or https://")
        if len(v) > 500:
            raise ValueError("Webhook URL must be less than 500 characters")
        return v
    
    @validator("events")
    def validate_events(cls, v):
        """Validate event types"""
        valid_events = {
            "invoice.success",
            "invoice.failed",
            "refund.success",
            "refund.failed",
            "purchase.success",
            "purchase.failed"
        }
        for event in v:
            if event not in valid_events:
                raise ValueError(f"Invalid event type: {event}. Valid events: {valid_events}")
        return v


class WebhookResponse(BaseModel):
    """Response containing webhook registration details"""
    webhook_id: str = Field(..., description="Webhook ID")
    webhook_url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Subscribed event types")
    is_active: bool = Field(..., description="Whether webhook is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True


class WebhookUpdateRequest(BaseModel):
    """Request to update a webhook"""
    webhook_url: Optional[str] = Field(None, description="New webhook URL")
    events: Optional[List[str]] = Field(None, description="New list of event types")
    is_active: Optional[bool] = Field(None, description="Activate or deactivate webhook")
    
    @validator("webhook_url")
    def validate_webhook_url(cls, v):
        """Validate webhook URL format"""
        if v is None:
            return v
        if not v.startswith(("http://", "https://")):
            raise ValueError("Webhook URL must start with http:// or https://")
        if len(v) > 500:
            raise ValueError("Webhook URL must be less than 500 characters")
        return v
    
    @validator("events")
    def validate_events(cls, v):
        """Validate event types"""
        if v is None:
            return v
        valid_events = {
            "invoice.success",
            "invoice.failed",
            "refund.success",
            "refund.failed",
            "purchase.success",
            "purchase.failed"
        }
        for event in v:
            if event not in valid_events:
                raise ValueError(f"Invalid event type: {event}. Valid events: {valid_events}")
        return v


class WebhookListResponse(BaseModel):
    """Response containing list of webhooks"""
    webhook_id: str = Field(..., description="Webhook ID")
    webhook_url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Subscribed event types")
    is_active: bool = Field(..., description="Whether webhook is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class WebhookDeleteResponse(BaseModel):
    """Response for webhook deletion"""
    webhook_id: str = Field(..., description="Deleted webhook ID")
    message: str = Field(..., description="Deletion confirmation message")
    deleted_at: datetime = Field(..., description="Deletion timestamp")

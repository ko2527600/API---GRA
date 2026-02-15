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

#!/usr/bin/env python
import sys
try:
    from fastapi import APIRouter, Depends, HTTPException, status
    print("FastAPI imports OK")
    
    from sqlalchemy.orm import Session
    from uuid import UUID
    print("SQLAlchemy imports OK")
    
    from app.database import get_db
    print("Database import OK")
    
    from app.middleware.auth_dependency import verify_auth
    print("Auth dependency import OK")
    
    from app.schemas.webhook import (
        WebhookRegisterRequest,
        WebhookResponse,
        WebhookUpdateRequest,
        WebhookListResponse,
        WebhookDeleteResponse
    )
    print("Webhook schemas import OK")
    
    from app.services.webhook_service import WebhookService
    print("Webhook service import OK")
    
    from app.logger import logger
    from datetime import datetime
    print("Logger and datetime import OK")
    
    router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
    print("Router created OK")
    print(f"Router type: {type(router)}")
    print(f"Router has routes: {len(router.routes)}")
    
    # Now try importing the module
    from app.api.endpoints import webhooks
    print(f"Webhooks module imported: {webhooks}")
    print(f"Has router: {hasattr(webhooks, 'router')}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

"""Authentication middleware for API Key + HMAC Signature verification"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, Callable, Tuple
import json
from datetime import datetime

from app.utils.hmac_signature import HMACSignatureManager
from app.services.business_service import BusinessService
from app.services.api_key_service import APIKeyService
from app.database import SessionLocal
from app.logger import get_logger

logger = get_logger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass


class AuthMiddleware:
    """Middleware for API Key + HMAC Signature authentication
    
    Validates:
    1. API Key exists and is active
    2. HMAC-SHA256 signature is valid
    3. Timestamp is within acceptable window (prevents replay attacks)
    4. Business account is active
    """
    
    # Required headers for authentication
    REQUIRED_HEADERS = {
        "X-API-Key": "API key identifier",
        "X-API-Signature": "HMAC-SHA256 signature",
        "X-API-Timestamp": "ISO format timestamp"
    }
    
    # Public endpoints that don't require authentication
    PUBLIC_ENDPOINTS = {
        "/api/v1/health",
        "/docs",
        "/openapi.json",
        "/redoc"
    }
    
    @staticmethod
    def is_public_endpoint(path: str) -> bool:
        """Check if endpoint is public (no auth required)"""
        return path in AuthMiddleware.PUBLIC_ENDPOINTS
    
    @staticmethod
    async def verify_authentication(request: Request, db: Session) -> Tuple[dict, str]:
        """
        Verify API Key and HMAC Signature.
        
        Args:
            request: FastAPI request object
            db: Database session
            
        Returns:
            Tuple[dict, str]: (business_data, api_key)
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # Check if endpoint is public
        if AuthMiddleware.is_public_endpoint(request.url.path):
            return {}, ""
        
        # Extract headers
        api_key = request.headers.get("X-API-Key")
        signature = request.headers.get("X-API-Signature")
        timestamp = request.headers.get("X-API-Timestamp")
        
        # Validate headers are present
        if not api_key:
            raise AuthenticationError("Missing X-API-Key header")
        if not signature:
            raise AuthenticationError("Missing X-API-Signature header")
        if not timestamp:
            raise AuthenticationError("Missing X-API-Timestamp header")
        
        # Verify timestamp is within acceptable window
        if not HMACSignatureManager.verify_timestamp(timestamp):
            raise AuthenticationError("Timestamp outside acceptable window (5 minutes)")
        
        # Get business by API key
        business = BusinessService.get_business_by_api_key(db, api_key)
        if not business:
            raise AuthenticationError("Invalid API key")
        
        # Check if business is active
        if business.status != "active":
            raise AuthenticationError("Business account is inactive")
        
        # Read request body for signature verification
        # Cache the body so it can be read again by the endpoint
        body = await request.body()
        
        # Verify signature using constant-time comparison
        if not HMACSignatureManager.verify_signature(
            api_secret=business.api_secret,
            message=HMACSignatureManager.generate_signature_message(
                method=request.method,
                path=request.url.path,
                timestamp=timestamp,
                body_hash=HMACSignatureManager.generate_body_hash(body)
            ),
            provided_signature=signature
        ):
            logger.warning(f"Invalid signature for API key: {api_key}")
            raise AuthenticationError("Invalid signature")
        
        logger.info(f"Authentication successful for business: {business.id}")
        
        return {
            "id": str(business.id),
            "name": business.name,
            "api_key": api_key,
            "status": business.status
        }, api_key
    
    @staticmethod
    def create_error_response(
        error_message: str,
        status_code: int = status.HTTP_401_UNAUTHORIZED
    ) -> JSONResponse:
        """
        Create standardized authentication error response.
        
        Args:
            error_message: Error message to return
            status_code: HTTP status code
            
        Returns:
            JSONResponse: Formatted error response
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "error_code": "AUTH_FAILED",
                "message": error_message,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
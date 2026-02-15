"""Request/Response logging middleware with sensitive data masking"""
import time
import json
from typing import Callable, Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, StreamingResponse
from app.logger import get_logger, get_audit_logger, SensitiveDataMasker
from app.database import SessionLocal
from app.services.audit_log_service import AuditLogService

logger = get_logger(__name__)
audit_logger = get_audit_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all HTTP requests and responses with sensitive data masking.
    
    Features:
    - Logs all API requests with method, path, headers, and body
    - Logs all API responses with status code and body
    - Masks sensitive data (API keys, secrets, TINs, etc)
    - Tracks response time
    - Extracts business_id from authentication context
    - Handles streaming responses
    """
    
    # Endpoints that should not be logged (to reduce noise)
    SKIP_LOGGING_PATHS = {
        "/health",
        "/api/v1/health",
        "/docs",
        "/openapi.json",
        "/redoc"
    }
    
    # Sensitive endpoints where we should not log full request/response bodies
    SENSITIVE_ENDPOINTS = {
        "/api/v1/invoices/submit",
        "/api/v1/refunds/submit",
        "/api/v1/purchases/submit",
        "/api/v1/items/register",
        "/api/v1/inventory/update",
        "/api/v1/tin/validate",
        "/api/v1/tags/register",
        "/api/v1/reports/z-report",
        "/api/v1/vsdc/health-check",
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and response with logging.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler
            
        Returns:
            Response: HTTP response
        """
        # Skip logging for certain endpoints
        if request.url.path in self.SKIP_LOGGING_PATHS:
            return await call_next(request)
        
        # Extract request information
        start_time = time.time()
        method = request.method
        path = request.url.path
        query_string = request.url.query
        headers = dict(request.headers)
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Extract business_id from authentication context if available
        business_id = self._extract_business_id(request)
        
        # Read request body
        request_body = await request.body()
        request_body_dict = self._parse_body(request_body, request.headers.get("content-type", ""))
        
        # Log request
        self._log_request(
            business_id=business_id,
            method=method,
            path=path,
            query_string=query_string,
            headers=headers,
            body=request_body_dict,
            ip_address=ip_address,
            user_agent=user_agent,
            is_sensitive=path in self.SENSITIVE_ENDPOINTS
        )
        
        # Create a new request with the body (since we consumed it)
        async def receive():
            return {"type": "http.request", "body": request_body}
        
        request._receive = receive
        
        # Call next middleware/handler
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            logger.error(
                f"Exception during request processing: {str(e)}",
                extra={
                    "business_id": business_id,
                    "method": method,
                    "path": path,
                    "ip_address": ip_address,
                }
            )
            raise
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Read response body
        response_body = b""
        if isinstance(response, StreamingResponse):
            # For streaming responses, we can't read the body
            response_body_dict = {"note": "streaming_response"}
        else:
            async for chunk in response.body_iterator:
                response_body += chunk
            response_body_dict = self._parse_body(response_body, response.headers.get("content-type", ""))
        
        # Log response
        self._log_response(
            business_id=business_id,
            method=method,
            path=path,
            status_code=response.status_code,
            response_time_ms=response_time_ms,
            body=response_body_dict,
            is_sensitive=path in self.SENSITIVE_ENDPOINTS
        )
        
        # Persist audit log to database if business_id is available
        if business_id:
            try:
                self._persist_audit_log(
                    business_id=business_id,
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    request_body=request_body_dict,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    is_sensitive=path in self.SENSITIVE_ENDPOINTS
                )
            except Exception as e:
                logger.error(
                    f"Failed to persist audit log: {str(e)}",
                    extra={
                        "business_id": business_id,
                        "path": path,
                        "error": str(e),
                    }
                )
        
        # Return response with body
        if isinstance(response, StreamingResponse):
            return response
        else:
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
    
    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """
        Extract client IP address from request.
        
        Handles X-Forwarded-For header for proxied requests.
        
        Args:
            request: FastAPI request object
            
        Returns:
            str: Client IP address
        """
        # Check for X-Forwarded-For header (proxied requests)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            return forwarded_for.split(",")[0].strip()
        
        # Fall back to client connection
        if request.client:
            return request.client.host
        
        return "unknown"
    
    @staticmethod
    def _extract_business_id(request: Request) -> Optional[str]:
        """
        Extract business_id from request context if available.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Optional[str]: Business ID if available
        """
        # Try to get from request state (set by auth middleware)
        if hasattr(request.state, "business_id"):
            return request.state.business_id
        
        # Try to get from X-Business-ID header (for testing)
        return request.headers.get("X-Business-ID")
    
    @staticmethod
    def _parse_body(body: bytes, content_type: str) -> dict:
        """
        Parse request/response body based on content type.
        
        Args:
            body: Raw body bytes
            content_type: Content-Type header value
            
        Returns:
            dict: Parsed body or error info
        """
        if not body:
            return {}
        
        try:
            if "application/json" in content_type:
                return json.loads(body.decode("utf-8"))
            elif "application/xml" in content_type:
                # For XML, just return a note (don't parse to avoid complexity)
                return {"format": "xml", "size": len(body)}
            else:
                return {"format": "unknown", "size": len(body)}
        except Exception as e:
            return {"error": f"Failed to parse body: {str(e)}", "size": len(body)}
    
    @staticmethod
    def _log_request(
        business_id: Optional[str],
        method: str,
        path: str,
        query_string: str,
        headers: dict,
        body: dict,
        ip_address: str,
        user_agent: str,
        is_sensitive: bool = False
    ):
        """
        Log API request with sensitive data masking.
        
        Args:
            business_id: Business identifier
            method: HTTP method
            path: Request path
            query_string: Query string
            headers: Request headers
            body: Request body (parsed)
            ip_address: Client IP address
            user_agent: Client user agent
            is_sensitive: Whether this is a sensitive endpoint
        """
        # Mask sensitive headers
        masked_headers = LoggingMiddleware._mask_headers(headers)
        
        # Mask request body
        masked_body = SensitiveDataMasker.mask_dict(body) if body else {}
        
        # For sensitive endpoints, don't log full body
        if is_sensitive and masked_body:
            masked_body = {"note": "sensitive_endpoint_body_omitted"}
        
        # Log via audit logger
        audit_logger.log_request(
            business_id=business_id or "unknown",
            endpoint=path,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            request_data={
                "query_string": query_string,
                "headers": masked_headers,
                "body": masked_body
            }
        )
    
    @staticmethod
    def _log_response(
        business_id: Optional[str],
        method: str,
        path: str,
        status_code: int,
        response_time_ms: float,
        body: dict,
        is_sensitive: bool = False
    ):
        """
        Log API response with sensitive data masking.
        
        Args:
            business_id: Business identifier
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            body: Response body (parsed)
            is_sensitive: Whether this is a sensitive endpoint
        """
        # Mask response body
        masked_body = SensitiveDataMasker.mask_dict(body) if body else {}
        
        # For sensitive endpoints, don't log full body
        if is_sensitive and masked_body:
            masked_body = {"note": "sensitive_endpoint_body_omitted"}
        
        # Log via audit logger
        audit_logger.log_response(
            business_id=business_id or "unknown",
            endpoint=path,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            response_data=masked_body
        )
    
    @staticmethod
    def _mask_headers(headers: dict) -> dict:
        """
        Mask sensitive headers.
        
        Args:
            headers: Request headers
            
        Returns:
            dict: Headers with sensitive data masked
        """
        masked = {}
        sensitive_header_keys = {
            "x-api-key",
            "x-api-signature",
            "authorization",
            "cookie",
            "x-api-secret"
        }
        
        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower in sensitive_header_keys:
                masked[key] = "***masked***"
            else:
                masked[key] = value
        
        return masked
    
    @staticmethod
    def _persist_audit_log(
        business_id: str,
        method: str,
        path: str,
        status_code: int,
        request_body: dict,
        ip_address: str,
        user_agent: str,
        is_sensitive: bool = False
    ):
        """
        Persist audit log to database.
        
        Args:
            business_id: Business identifier
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            request_body: Request body (parsed)
            ip_address: Client IP address
            user_agent: Client user agent
            is_sensitive: Whether this is a sensitive endpoint
        """
        try:
            from uuid import UUID
            
            db = SessionLocal()
            
            # Determine response status
            response_status = "SUCCESS" if 200 <= status_code < 400 else "FAILED"
            
            # Mask request body
            masked_body = SensitiveDataMasker.mask_dict(request_body) if request_body else {}
            
            # For sensitive endpoints, don't store full body
            if is_sensitive and masked_body:
                masked_body = {"note": "sensitive_endpoint_body_omitted"}
            
            # Create audit log
            AuditLogService.create_audit_log(
                db=db,
                business_id=UUID(business_id),
                action="API_REQUEST",
                endpoint=path,
                method=method,
                response_code=status_code,
                response_status=response_status,
                request_payload=masked_body,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            
            db.close()
        except Exception as e:
            logger.error(
                f"Failed to persist audit log: {str(e)}",
                extra={
                    "business_id": business_id,
                    "path": path,
                    "error": str(e),
                }
            )

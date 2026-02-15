"""Rate limiting middleware for API requests"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from typing import Dict, Tuple
import time
from app.logger import get_logger

logger = get_logger(__name__)


class RateLimitError(Exception):
    """Custom exception for rate limit errors"""
    pass


class RateLimitMiddleware:
    """Middleware for per-business rate limiting
    
    Implements token bucket algorithm for rate limiting:
    - 100 requests per minute per business
    - Tracks requests in memory (suitable for single-instance deployments)
    - For distributed deployments, use Redis backend
    
    Rate Limit Configuration:
    - Requests per minute: 100 (configurable)
    - Window: 60 seconds
    - Returns 429 Too Many Requests when exceeded
    - Includes Retry-After header
    """
    
    # Public endpoints that don't require rate limiting
    PUBLIC_ENDPOINTS = {
        "/api/v1/health",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc"
    }
    
    def __init__(
        self,
        requests_per_minute: int = 100,
        window_seconds: int = 60
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Number of requests allowed per minute
            window_seconds: Time window in seconds (default 60)
        """
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        # Store request history: {business_id: [(timestamp, count), ...]}
        self.request_history: Dict[str, list] = {}
    
    @staticmethod
    def is_public_endpoint(path: str) -> bool:
        """Check if endpoint is public (no rate limiting required)"""
        return path in RateLimitMiddleware.PUBLIC_ENDPOINTS
    
    def check_rate_limit(
        self,
        business_id: str,
        current_time: float = None
    ) -> Tuple[bool, int, int]:
        """
        Check if business has exceeded rate limit.
        
        Args:
            business_id: The business identifier
            current_time: Current time (for testing), defaults to time.time()
            
        Returns:
            Tuple[bool, int, int]: (allowed, requests_made, requests_remaining)
                - allowed: True if request is allowed
                - requests_made: Number of requests made in current window
                - requests_remaining: Number of requests remaining
        """
        if current_time is None:
            current_time = time.time()
        
        # Initialize business history if not exists
        if business_id not in self.request_history:
            self.request_history[business_id] = []
        
        # Get request history for this business
        history = self.request_history[business_id]
        
        # Remove old requests outside the window
        cutoff_time = current_time - self.window_seconds
        history[:] = [req_time for req_time in history if req_time > cutoff_time]
        
        # Count requests in current window
        requests_made = len(history)
        
        # Check if limit exceeded
        if requests_made >= self.requests_per_minute:
            logger.warning(
                f"Rate limit exceeded for business: {business_id} "
                f"({requests_made}/{self.requests_per_minute} requests)"
            )
            requests_remaining = max(0, self.requests_per_minute - requests_made)
            return False, requests_made, requests_remaining
        
        # Add current request to history
        history.append(current_time)
        requests_made += 1
        requests_remaining = max(0, self.requests_per_minute - requests_made)
        
        logger.debug(
            f"Rate limit check passed for business: {business_id} "
            f"({requests_made}/{self.requests_per_minute} requests)"
        )
        
        return True, requests_made, requests_remaining
    
    def get_retry_after(self, business_id: str, current_time: float = None) -> int:
        """
        Calculate seconds to wait before next request is allowed.
        
        Args:
            business_id: The business identifier
            current_time: Current time (for testing), defaults to time.time()
            
        Returns:
            int: Seconds to wait before retry
        """
        if current_time is None:
            current_time = time.time()
        
        if business_id not in self.request_history:
            return 0
        
        history = self.request_history[business_id]
        if not history:
            return 0
        
        # Find the oldest request in the window
        cutoff_time = current_time - self.window_seconds
        oldest_request = min(history)
        
        # Calculate when this oldest request will expire
        retry_after = int(oldest_request - cutoff_time) + 1
        return max(1, retry_after)
    
    def reset_business_limit(self, business_id: str) -> None:
        """
        Reset rate limit for a business (admin function).
        
        Args:
            business_id: The business identifier
        """
        if business_id in self.request_history:
            self.request_history[business_id] = []
            logger.info(f"Rate limit reset for business: {business_id}")
    
    def cleanup_old_entries(self, current_time: float = None) -> None:
        """
        Clean up old entries from memory (call periodically).
        
        Args:
            current_time: Current time (for testing), defaults to time.time()
        """
        if current_time is None:
            current_time = time.time()
        
        cutoff_time = current_time - self.window_seconds
        
        # Remove businesses with no recent requests
        businesses_to_remove = []
        for business_id, history in self.request_history.items():
            # Remove old requests
            history[:] = [req_time for req_time in history if req_time > cutoff_time]
            
            # Mark business for removal if no requests
            if not history:
                businesses_to_remove.append(business_id)
        
        # Remove empty entries
        for business_id in businesses_to_remove:
            del self.request_history[business_id]
        
        if businesses_to_remove:
            logger.debug(f"Cleaned up rate limit entries for {len(businesses_to_remove)} businesses")
    
    @staticmethod
    def create_rate_limit_error_response(
        retry_after: int,
        requests_limit: int,
        status_code: int = status.HTTP_429_TOO_MANY_REQUESTS
    ) -> JSONResponse:
        """
        Create standardized rate limit error response.
        
        Args:
            retry_after: Seconds to wait before retry
            requests_limit: Rate limit (requests per minute)
            status_code: HTTP status code
            
        Returns:
            JSONResponse: Formatted error response with Retry-After header
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit exceeded. Maximum {requests_limit} requests per minute allowed.",
                "retry_after": retry_after,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            headers={"Retry-After": str(retry_after)}
        )


# Global rate limiter instance
_rate_limiter: RateLimitMiddleware = None


def get_rate_limiter(
    requests_per_minute: int = 100,
    window_seconds: int = 60
) -> RateLimitMiddleware:
    """
    Get or create global rate limiter instance.
    
    Args:
        requests_per_minute: Number of requests allowed per minute
        window_seconds: Time window in seconds
        
    Returns:
        RateLimitMiddleware: Global rate limiter instance
    """
    global _rate_limiter
    
    if _rate_limiter is None:
        _rate_limiter = RateLimitMiddleware(
            requests_per_minute=requests_per_minute,
            window_seconds=window_seconds
        )
    
    return _rate_limiter

"""GRA HTTP Client with retry logic and exponential backoff"""
import asyncio
import httpx
import json
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import time

from app.config import settings
from app.logger import get_logger

logger = get_logger(__name__)


class ErrorType(Enum):
    """Classification of error types for retry logic"""
    TRANSIENT = "transient"  # Retry with exponential backoff
    PERMANENT = "permanent"  # Do not retry
    RATE_LIMIT = "rate_limit"  # Retry with backoff
    UNAVAILABLE = "unavailable"  # Retry with longer backoff


class GRAErrorClassifier:
    """Classifies GRA errors to determine retry strategy"""
    
    # Transient errors that should be retried
    TRANSIENT_ERROR_CODES = {
        "D06",  # Stamping engine is down
        "IS100",  # Internal error
        "A13",  # E-VAT unable to reach database
    }
    
    # HTTP status codes that indicate transient errors
    TRANSIENT_HTTP_CODES = {408, 429, 500, 502, 503, 504}
    
    # Permanent errors that should not be retried
    PERMANENT_ERROR_CODES = {
        "A01",  # Company credentials do not exist
        "B01",  # Incorrect client TIN PIN
        "B05",  # Client name missing
        "B051",  # Tax number format not accepted
        "B06",  # Client name different from previous
        "B061",  # Item code different from previous
        "B07",  # Code missing
        "B09",  # Description missing
        "B10",  # Quantity missing
        "B11",  # Quantity is negative
        "B12",  # Quantity not a number
        "B13",  # Tax rate not accepted
        "B15",  # Item count mismatch
        "B16",  # Total amount mismatch
        "B18",  # Total VAT mismatch
        "B19",  # Invoice reference missing
        "B20",  # Invoice reference already sent
        "B21",  # Negative sale price
        "B22",  # Zero total invoice not supported
        "B27",  # Tax rate different from previous
        "B28",  # Client tax number different
        "B29",  # Client tax number for another client
        "B31",  # Levy amount A discrepancy
        "B32",  # Levy amount B discrepancy
        "B33",  # Levy amount C discrepancy
        "B34",  # Levy amount D discrepancy
        "B35",  # Levy amount E discrepancy
        "B70",  # Wrong currency
        "A05",  # Missing original invoice number
        "A06",  # Invalid unit price
        "A07",  # Invalid discount
        "A08",  # Invalid tax code
        "A09",  # Invalid tax rate
        "A11",  # Item count not a number
        "T01",  # Invalid TIN number
        "T03",  # TIN number not found
        "T04",  # TIN stopped
        "T05",  # TIN protected
        "T06",  # Incorrect client TIN PIN
        "D01",  # Invoice already exists
    }
    
    @staticmethod
    def classify_error(
        status_code: int,
        response_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> ErrorType:
        """
        Classify an error to determine retry strategy
        
        Args:
            status_code: HTTP status code
            response_data: GRA response data (may contain error code)
            error_message: Error message
            
        Returns:
            ErrorType indicating retry strategy
        """
        # Check for rate limiting
        if status_code == 429:
            return ErrorType.RATE_LIMIT
        
        # Check for service unavailable
        if status_code == 503:
            return ErrorType.UNAVAILABLE
        
        # Check for transient HTTP errors
        if status_code in GRAErrorClassifier.TRANSIENT_HTTP_CODES:
            return ErrorType.TRANSIENT
        
        # Check for GRA error codes in response
        if response_data:
            error_code = response_data.get("error_code") or response_data.get("gra_response_code")
            
            if error_code in GRAErrorClassifier.TRANSIENT_ERROR_CODES:
                return ErrorType.TRANSIENT
            
            if error_code in GRAErrorClassifier.PERMANENT_ERROR_CODES:
                return ErrorType.PERMANENT
        
        # Default to permanent for unknown errors
        return ErrorType.PERMANENT


class RetryStrategy:
    """Defines retry strategy for different error types"""
    
    def __init__(
        self,
        max_retries: int = 5,
        backoff_base: int = 1,
        backoff_max: int = 3600,
    ):
        """
        Initialize retry strategy
        
        Args:
            max_retries: Maximum number of retry attempts
            backoff_base: Base backoff time in seconds
            backoff_max: Maximum backoff time in seconds
        """
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
    
    def get_backoff_time(self, attempt: int) -> int:
        """
        Calculate backoff time for exponential backoff
        
        Args:
            attempt: Attempt number (0-indexed)
            
        Returns:
            Backoff time in seconds
        """
        # Exponential backoff: base * 2^attempt
        backoff = self.backoff_base * (2 ** attempt)
        # Cap at maximum backoff
        return min(backoff, self.backoff_max)
    
    def should_retry(self, attempt: int) -> bool:
        """
        Check if should retry based on attempt number
        
        Args:
            attempt: Attempt number (0-indexed)
            
        Returns:
            True if should retry, False otherwise
        """
        return attempt < self.max_retries


class GRAHTTPClient:
    """HTTP client for GRA API with retry logic and exponential backoff"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """
        Initialize GRA HTTP client
        
        Args:
            base_url: GRA API base URL (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
            max_retries: Maximum retry attempts (defaults to settings)
        """
        self.base_url = base_url or settings.GRA_API_BASE_URL
        self.timeout = timeout or settings.GRA_API_TIMEOUT
        self.max_retries = max_retries or settings.GRA_API_RETRIES
        
        # Create retry strategies for different error types
        self.transient_strategy = RetryStrategy(
            max_retries=5,
            backoff_base=1,
            backoff_max=32,
        )
        
        self.unavailable_strategy = RetryStrategy(
            max_retries=10,
            backoff_base=5,
            backoff_max=2560,
        )
        
        self.rate_limit_strategy = RetryStrategy(
            max_retries=5,
            backoff_base=1,
            backoff_max=60,
        )
    
    async def submit_json(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Submit JSON request to GRA API with retry logic
        
        Args:
            endpoint: API endpoint (e.g., "/api/v1/invoices/submit")
            data: Request payload
            headers: Additional headers
            
        Returns:
            Response data
            
        Raises:
            GRAClientError: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        
        logger.info(
            f"Submitting JSON request to GRA: {endpoint}",
            extra={"url": url, "data_keys": list(data.keys())},
        )
        
        return await self._submit_with_retry(
            method="POST",
            url=url,
            json=data,
            headers=headers,
            content_type="application/json",
        )
    
    async def submit_xml(
        self,
        endpoint: str,
        data: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Submit XML request to GRA API with retry logic
        
        Args:
            endpoint: API endpoint
            data: XML request payload
            headers: Additional headers
            
        Returns:
            Response data
            
        Raises:
            GRAClientError: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        
        logger.info(
            f"Submitting XML request to GRA: {endpoint}",
            extra={"url": url},
        )
        
        return await self._submit_with_retry(
            method="POST",
            url=url,
            content=data,
            headers=headers,
            content_type="application/xml",
        )
    
    async def get_status(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Get status from GRA API with retry logic
        
        Args:
            endpoint: API endpoint
            headers: Additional headers
            
        Returns:
            Response data
            
        Raises:
            GRAClientError: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"
        
        logger.info(
            f"Getting status from GRA: {endpoint}",
            extra={"url": url},
        )
        
        return await self._submit_with_retry(
            method="GET",
            url=url,
            headers=headers,
        )
    
    async def _submit_with_retry(
        self,
        method: str,
        url: str,
        json: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit request with retry logic and exponential backoff
        
        Args:
            method: HTTP method (GET, POST, etc)
            url: Full URL
            json: JSON payload
            content: String content (for XML)
            headers: Request headers
            content_type: Content-Type header value
            
        Returns:
            Response data
            
        Raises:
            GRAClientError: If request fails after retries
        """
        attempt = 0
        last_error = None
        
        while True:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    # Prepare headers
                    request_headers = headers or {}
                    if content_type:
                        request_headers["Content-Type"] = content_type
                    
                    # Make request
                    if method == "GET":
                        response = await client.get(url, headers=request_headers)
                    elif method == "POST":
                        if json is not None:
                            response = await client.post(
                                url,
                                json=json,
                                headers=request_headers,
                            )
                        else:
                            response = await client.post(
                                url,
                                content=content,
                                headers=request_headers,
                            )
                    else:
                        raise GRAClientError(f"Unsupported HTTP method: {method}")
                    
                    # Log response
                    logger.info(
                        f"GRA API response: {response.status_code}",
                        extra={
                            "method": method,
                            "url": url,
                            "status_code": response.status_code,
                        },
                    )
                    
                    # Parse response
                    try:
                        response_data = response.json()
                    except ValueError:
                        response_data = {"raw_response": response.text}
                    
                    # Check for success (only if status is 2xx and no error in response)
                    if response.status_code in [200, 201, 202]:
                        # Check if response contains error code (GRA may return 200 with error)
                        error_code = response_data.get("error_code") or response_data.get("gra_response_code")
                        if not error_code:
                            logger.info(
                                f"GRA API request successful",
                                extra={
                                    "method": method,
                                    "url": url,
                                    "status_code": response.status_code,
                                },
                            )
                            return response_data
                    
                    # Classify error
                    error_type = GRAErrorClassifier.classify_error(
                        response.status_code,
                        response_data,
                    )
                    
                    # Determine retry strategy
                    if error_type == ErrorType.UNAVAILABLE:
                        strategy = self.unavailable_strategy
                    elif error_type == ErrorType.RATE_LIMIT:
                        strategy = self.rate_limit_strategy
                    else:
                        strategy = self.transient_strategy
                    
                    # Check if should retry
                    if error_type == ErrorType.PERMANENT or not strategy.should_retry(attempt):
                        logger.error(
                            f"GRA API request failed (no retry): {response.status_code}",
                            extra={
                                "method": method,
                                "url": url,
                                "status_code": response.status_code,
                                "error_type": error_type.value,
                                "response": response_data,
                            },
                        )
                        raise GRAClientError(
                            f"GRA API request failed: {response.status_code}",
                            status_code=response.status_code,
                            response_data=response_data,
                            error_type=error_type,
                        )
                    
                    # Calculate backoff
                    backoff_time = strategy.get_backoff_time(attempt)
                    
                    logger.warning(
                        f"GRA API request failed, retrying in {backoff_time}s (attempt {attempt + 1}/{strategy.max_retries})",
                        extra={
                            "method": method,
                            "url": url,
                            "status_code": response.status_code,
                            "error_type": error_type.value,
                            "attempt": attempt + 1,
                            "backoff_time": backoff_time,
                        },
                    )
                    
                    # Wait before retry
                    await asyncio.sleep(backoff_time)
                    attempt += 1
                    last_error = response_data
            
            except httpx.TimeoutException as e:
                logger.warning(
                    f"GRA API request timeout (attempt {attempt + 1})",
                    extra={
                        "method": method,
                        "url": url,
                        "attempt": attempt + 1,
                        "error": str(e),
                    },
                )
                
                # Treat timeout as transient error
                if not self.transient_strategy.should_retry(attempt):
                    logger.error(
                        f"GRA API request timeout (max retries exceeded)",
                        extra={
                            "method": method,
                            "url": url,
                            "attempt": attempt + 1,
                        },
                    )
                    raise GRAClientError(
                        f"GRA API request timeout after {attempt + 1} attempts",
                        error_type=ErrorType.TRANSIENT,
                    )
                
                backoff_time = self.transient_strategy.get_backoff_time(attempt)
                logger.info(
                    f"Retrying after timeout in {backoff_time}s",
                    extra={"backoff_time": backoff_time},
                )
                await asyncio.sleep(backoff_time)
                attempt += 1
            
            except httpx.NetworkError as e:
                logger.warning(
                    f"GRA API network error (attempt {attempt + 1}): {str(e)}",
                    extra={
                        "method": method,
                        "url": url,
                        "attempt": attempt + 1,
                        "error": str(e),
                    },
                )
                
                # Treat network error as transient error
                if not self.transient_strategy.should_retry(attempt):
                    logger.error(
                        f"GRA API network error (max retries exceeded)",
                        extra={
                            "method": method,
                            "url": url,
                            "attempt": attempt + 1,
                        },
                    )
                    raise GRAClientError(
                        f"GRA API network error after {attempt + 1} attempts: {str(e)}",
                        error_type=ErrorType.TRANSIENT,
                    )
                
                backoff_time = self.transient_strategy.get_backoff_time(attempt)
                logger.info(
                    f"Retrying after network error in {backoff_time}s",
                    extra={"backoff_time": backoff_time},
                )
                await asyncio.sleep(backoff_time)
                attempt += 1


class GRAClientError(Exception):
    """Exception raised by GRA HTTP client"""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error_type: Optional[ErrorType] = None,
    ):
        """
        Initialize GRA client error
        
        Args:
            message: Error message
            status_code: HTTP status code
            response_data: GRA response data
            error_type: Type of error
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        self.error_type = error_type or ErrorType.PERMANENT
    
    def __str__(self) -> str:
        """String representation of error"""
        if self.status_code:
            return f"{self.message} (HTTP {self.status_code})"
        return self.message
    
    def is_retryable(self) -> bool:
        """Check if error is retryable"""
        return self.error_type in [
            ErrorType.TRANSIENT,
            ErrorType.RATE_LIMIT,
            ErrorType.UNAVAILABLE,
        ]


# Create singleton instance
_gra_client: Optional[GRAHTTPClient] = None


def get_gra_client() -> GRAHTTPClient:
    """Get or create GRA HTTP client singleton"""
    global _gra_client
    if _gra_client is None:
        _gra_client = GRAHTTPClient()
    return _gra_client

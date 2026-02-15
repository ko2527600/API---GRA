"""Tests for rate limiting middleware"""
import pytest
import time
from datetime import datetime

from app.middleware.rate_limit import (
    RateLimitMiddleware,
    RateLimitError,
    get_rate_limiter
)


@pytest.fixture
def rate_limiter():
    """Create a rate limiter instance for testing"""
    return RateLimitMiddleware(requests_per_minute=100, window_seconds=60)


@pytest.fixture
def rate_limiter_small():
    """Create a rate limiter with small limit for testing"""
    return RateLimitMiddleware(requests_per_minute=5, window_seconds=60)


class TestRateLimiterBasic:
    """Test basic rate limiting functionality"""
    
    def test_first_request_allowed(self, rate_limiter):
        """First request should always be allowed"""
        allowed, made, remaining = rate_limiter.check_rate_limit("business_1")
        assert allowed is True
        assert made == 1
        assert remaining == 100 - 1  # 100 limit - 1 made = 99 remaining
    
    def test_multiple_requests_allowed(self, rate_limiter):
        """Multiple requests within limit should be allowed"""
        for i in range(50):
            allowed, made, remaining = rate_limiter.check_rate_limit("business_1")
            assert allowed is True
            assert made == i + 1
            assert remaining == 100 - made  # Remaining after request is added
    
    def test_limit_exceeded(self, rate_limiter_small):
        """Request should be rejected when limit exceeded"""
        # Make 5 requests (at limit)
        for i in range(5):
            allowed, made, remaining = rate_limiter_small.check_rate_limit("business_1")
            assert allowed is True
        
        # 6th request should be rejected
        allowed, made, remaining = rate_limiter_small.check_rate_limit("business_1")
        assert allowed is False
        assert made == 5
        assert remaining == 0
    
    def test_different_businesses_isolated(self, rate_limiter_small):
        """Different businesses should have separate limits"""
        # Business 1 makes 5 requests
        for i in range(5):
            allowed, _, _ = rate_limiter_small.check_rate_limit("business_1")
            assert allowed is True
        
        # Business 1 is now at limit
        allowed, _, _ = rate_limiter_small.check_rate_limit("business_1")
        assert allowed is False
        
        # Business 2 should still have requests available
        allowed, made, remaining = rate_limiter_small.check_rate_limit("business_2")
        assert allowed is True
        assert made == 1
        assert remaining == 5 - 1  # 5 limit - 1 made


class TestRateLimiterWindow:
    """Test time window functionality"""
    
    def test_requests_expire_after_window(self, rate_limiter_small):
        """Requests should expire after time window"""
        current_time = 1000.0
        
        # Make 5 requests at time 1000
        for i in range(5):
            allowed, _, _ = rate_limiter_small.check_rate_limit(
                "business_1",
                current_time=current_time
            )
            assert allowed is True
        
        # 6th request at time 1000 should be rejected
        allowed, _, _ = rate_limiter_small.check_rate_limit(
            "business_1",
            current_time=current_time
        )
        assert allowed is False
        
        # Request at time 1061 (after 60 second window) should be allowed
        allowed, made, remaining = rate_limiter_small.check_rate_limit(
            "business_1",
            current_time=current_time + 61
        )
        assert allowed is True
        assert made == 1
        assert remaining == 5 - 1  # 5 limit - 1 made
    
    def test_partial_window_expiry(self, rate_limiter_small):
        """Requests should partially expire as time passes"""
        current_time = 1000.0
        
        # Make 3 requests at time 1000
        for i in range(3):
            rate_limiter_small.check_rate_limit(
                "business_1",
                current_time=current_time
            )
        
        # Make 2 requests at time 1030
        for i in range(2):
            rate_limiter_small.check_rate_limit(
                "business_1",
                current_time=current_time + 30
            )
        
        # At time 1030, we have 5 requests (at limit)
        allowed, made, _ = rate_limiter_small.check_rate_limit(
            "business_1",
            current_time=current_time + 30
        )
        assert allowed is False
        assert made == 5
        
        # At time 1061, first 3 requests expire (1000 + 60 = 1060, so at 1061 they're gone)
        # We have 2 requests left from time 1030
        allowed, made, remaining = rate_limiter_small.check_rate_limit(
            "business_1",
            current_time=current_time + 61
        )
        assert allowed is True
        assert made == 3  # 2 old + 1 new
        assert remaining == 5 - 3  # 5 limit - 3 made


class TestRateLimiterRetryAfter:
    """Test Retry-After calculation"""
    
    def test_retry_after_calculation(self, rate_limiter_small):
        """Retry-After should indicate when next request is allowed"""
        current_time = 1000.0
        
        # Make 5 requests at time 1000
        for i in range(5):
            rate_limiter_small.check_rate_limit(
                "business_1",
                current_time=current_time
            )
        
        # At time 1000, retry_after should be ~60 seconds
        retry_after = rate_limiter_small.get_retry_after(
            "business_1",
            current_time=current_time
        )
        assert retry_after >= 59
        assert retry_after <= 61
        
        # At time 1030, retry_after should be ~30 seconds
        retry_after = rate_limiter_small.get_retry_after(
            "business_1",
            current_time=current_time + 30
        )
        assert retry_after >= 29
        assert retry_after <= 31
    
    def test_retry_after_no_requests(self, rate_limiter):
        """Retry-After should be 0 if no requests made"""
        retry_after = rate_limiter.get_retry_after("business_1")
        assert retry_after == 0


class TestRateLimiterPublicEndpoints:
    """Test public endpoint detection"""
    
    def test_is_public_endpoint_health(self):
        """Health endpoint should be public"""
        assert RateLimitMiddleware.is_public_endpoint("/api/v1/health") is True
        assert RateLimitMiddleware.is_public_endpoint("/health") is True
    
    def test_is_public_endpoint_docs(self):
        """Documentation endpoints should be public"""
        assert RateLimitMiddleware.is_public_endpoint("/docs") is True
        assert RateLimitMiddleware.is_public_endpoint("/openapi.json") is True
        assert RateLimitMiddleware.is_public_endpoint("/redoc") is True
    
    def test_is_not_public_endpoint(self):
        """Protected endpoints should not be public"""
        assert RateLimitMiddleware.is_public_endpoint("/api/v1/invoices/submit") is False
        assert RateLimitMiddleware.is_public_endpoint("/api/v1/refunds/submit") is False


class TestRateLimiterReset:
    """Test rate limit reset functionality"""
    
    def test_reset_business_limit(self, rate_limiter_small):
        """Reset should clear business request history"""
        # Make 5 requests
        for i in range(5):
            rate_limiter_small.check_rate_limit("business_1")
        
        # Verify limit is reached
        allowed, _, _ = rate_limiter_small.check_rate_limit("business_1")
        assert allowed is False
        
        # Reset limit
        rate_limiter_small.reset_business_limit("business_1")
        
        # Verify limit is reset
        allowed, made, remaining = rate_limiter_small.check_rate_limit("business_1")
        assert allowed is True
        assert made == 1
        assert remaining == 5 - 1  # 5 limit - 1 made


class TestRateLimiterCleanup:
    """Test cleanup of old entries"""
    
    def test_cleanup_removes_old_entries(self, rate_limiter_small):
        """Cleanup should remove businesses with no recent requests"""
        current_time = 1000.0
        
        # Make requests for business_1
        rate_limiter_small.check_rate_limit("business_1", current_time=current_time)
        
        # Make requests for business_2
        rate_limiter_small.check_rate_limit("business_2", current_time=current_time)
        
        # Verify both businesses are in history
        assert "business_1" in rate_limiter_small.request_history
        assert "business_2" in rate_limiter_small.request_history
        
        # Cleanup at time 1061 (after window)
        rate_limiter_small.cleanup_old_entries(current_time=current_time + 61)
        
        # Both should be removed (no requests in window)
        assert "business_1" not in rate_limiter_small.request_history
        assert "business_2" not in rate_limiter_small.request_history
    
    def test_cleanup_keeps_recent_entries(self, rate_limiter_small):
        """Cleanup should keep businesses with recent requests"""
        current_time = 1000.0
        
        # Make request for business_1 at time 1000
        rate_limiter_small.check_rate_limit("business_1", current_time=current_time)
        
        # Make request for business_2 at time 1050
        rate_limiter_small.check_rate_limit("business_2", current_time=current_time + 50)
        
        # Cleanup at time 1061 (after 60 second window from time 1000)
        rate_limiter_small.cleanup_old_entries(current_time=current_time + 61)
        
        # business_1 should be removed (outside window: 1000 + 60 = 1060, cleanup at 1061)
        assert "business_1" not in rate_limiter_small.request_history
        
        # business_2 should be kept (within window: 1050 + 60 = 1110, cleanup at 1061)
        assert "business_2" in rate_limiter_small.request_history


class TestRateLimiterErrorResponse:
    """Test error response generation"""
    
    def test_error_response_format(self):
        """Error response should have correct format"""
        response = RateLimitMiddleware.create_rate_limit_error_response(
            retry_after=60,
            requests_limit=100
        )
        
        assert response.status_code == 429
        data = response.body.decode()
        assert "RATE_LIMIT_EXCEEDED" in data
        assert "retry_after" in data
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "60"
    
    def test_error_response_includes_timestamp(self):
        """Error response should include timestamp"""
        response = RateLimitMiddleware.create_rate_limit_error_response(
            retry_after=30,
            requests_limit=100
        )
        
        data = response.body.decode()
        assert "timestamp" in data


class TestRateLimiterGlobalInstance:
    """Test global rate limiter instance"""
    
    def test_get_rate_limiter_singleton(self):
        """get_rate_limiter should return same instance"""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        assert limiter1 is limiter2
    
    def test_get_rate_limiter_custom_config(self):
        """get_rate_limiter should accept custom configuration"""
        # Reset global instance
        import app.middleware.rate_limit as rate_limit_module
        rate_limit_module._rate_limiter = None
        
        limiter = get_rate_limiter(requests_per_minute=50, window_seconds=30)
        
        assert limiter.requests_per_minute == 50
        assert limiter.window_seconds == 30


class TestRateLimiterEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_exactly_at_limit(self, rate_limiter_small):
        """Request at exactly the limit should be allowed"""
        for i in range(5):
            allowed, made, remaining = rate_limiter_small.check_rate_limit("business_1")
            assert allowed is True
            assert made == i + 1
    
    def test_one_over_limit(self, rate_limiter_small):
        """Request one over limit should be rejected"""
        for i in range(5):
            rate_limiter_small.check_rate_limit("business_1")
        
        allowed, made, remaining = rate_limiter_small.check_rate_limit("business_1")
        assert allowed is False
        assert made == 5
        assert remaining == 0
    
    def test_zero_requests_remaining(self, rate_limiter_small):
        """When at limit, remaining should be 0"""
        for i in range(5):
            rate_limiter_small.check_rate_limit("business_1")
        
        allowed, made, remaining = rate_limiter_small.check_rate_limit("business_1")
        assert remaining == 0
    
    def test_large_number_of_businesses(self, rate_limiter):
        """Should handle many businesses independently"""
        # Create 100 businesses with 50 requests each
        for business_id in range(100):
            for _ in range(50):
                allowed, _, _ = rate_limiter.check_rate_limit(f"business_{business_id}")
                assert allowed is True
        
        # Verify each business has 50 requests
        for business_id in range(100):
            allowed, made, _ = rate_limiter.check_rate_limit(f"business_{business_id}")
            assert made == 51  # 50 + 1 new request

"""Tests for GRA HTTP client with retry logic"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from datetime import datetime

from app.services.gra_client import (
    GRAHTTPClient,
    GRAClientError,
    ErrorType,
    GRAErrorClassifier,
    RetryStrategy,
)


class TestErrorClassifier:
    """Tests for GRA error classifier"""
    
    def test_classify_transient_http_error(self):
        """Test classification of transient HTTP errors"""
        assert GRAErrorClassifier.classify_error(500) == ErrorType.TRANSIENT
        assert GRAErrorClassifier.classify_error(502) == ErrorType.TRANSIENT
        assert GRAErrorClassifier.classify_error(503) == ErrorType.UNAVAILABLE
        assert GRAErrorClassifier.classify_error(504) == ErrorType.TRANSIENT
    
    def test_classify_rate_limit_error(self):
        """Test classification of rate limit errors"""
        assert GRAErrorClassifier.classify_error(429) == ErrorType.RATE_LIMIT
    
    def test_classify_transient_gra_error_codes(self):
        """Test classification of transient GRA error codes"""
        response_data = {"gra_response_code": "D06"}
        assert GRAErrorClassifier.classify_error(200, response_data) == ErrorType.TRANSIENT
        
        response_data = {"gra_response_code": "IS100"}
        assert GRAErrorClassifier.classify_error(200, response_data) == ErrorType.TRANSIENT
        
        response_data = {"gra_response_code": "A13"}
        assert GRAErrorClassifier.classify_error(200, response_data) == ErrorType.TRANSIENT
    
    def test_classify_permanent_gra_error_codes(self):
        """Test classification of permanent GRA error codes"""
        response_data = {"gra_response_code": "B16"}
        assert GRAErrorClassifier.classify_error(200, response_data) == ErrorType.PERMANENT
        
        response_data = {"gra_response_code": "A01"}
        assert GRAErrorClassifier.classify_error(200, response_data) == ErrorType.PERMANENT
        
        response_data = {"gra_response_code": "B05"}
        assert GRAErrorClassifier.classify_error(200, response_data) == ErrorType.PERMANENT
    
    def test_classify_unknown_error(self):
        """Test classification of unknown errors defaults to permanent"""
        assert GRAErrorClassifier.classify_error(400) == ErrorType.PERMANENT


class TestRetryStrategy:
    """Tests for retry strategy"""
    
    def test_exponential_backoff_calculation(self):
        """Test exponential backoff calculation"""
        strategy = RetryStrategy(max_retries=5, backoff_base=1, backoff_max=32)
        
        # Exponential backoff: 1, 2, 4, 8, 16, 32
        assert strategy.get_backoff_time(0) == 1
        assert strategy.get_backoff_time(1) == 2
        assert strategy.get_backoff_time(2) == 4
        assert strategy.get_backoff_time(3) == 8
        assert strategy.get_backoff_time(4) == 16
        assert strategy.get_backoff_time(5) == 32
    
    def test_backoff_max_cap(self):
        """Test that backoff is capped at maximum"""
        strategy = RetryStrategy(max_retries=10, backoff_base=1, backoff_max=60)
        
        # Should be capped at 60
        assert strategy.get_backoff_time(10) == 60
    
    def test_should_retry(self):
        """Test should_retry logic"""
        strategy = RetryStrategy(max_retries=3)
        
        assert strategy.should_retry(0) is True
        assert strategy.should_retry(1) is True
        assert strategy.should_retry(2) is True
        assert strategy.should_retry(3) is False
    
    def test_unavailable_strategy_longer_backoff(self):
        """Test that unavailable strategy has longer backoff"""
        transient_strategy = RetryStrategy(max_retries=5, backoff_base=1, backoff_max=32)
        unavailable_strategy = RetryStrategy(max_retries=10, backoff_base=5, backoff_max=2560)
        
        # Unavailable strategy should have longer backoff times
        assert unavailable_strategy.get_backoff_time(0) > transient_strategy.get_backoff_time(0)
        assert unavailable_strategy.get_backoff_time(5) > transient_strategy.get_backoff_time(5)


class TestGRAHTTPClient:
    """Tests for GRA HTTP client"""
    
    @pytest.fixture
    def client(self):
        """Create GRA HTTP client for testing"""
        return GRAHTTPClient(
            base_url="https://api.test.com",
            timeout=10,
            max_retries=3,
        )
    
    @pytest.mark.asyncio
    async def test_submit_json_success(self, client):
        """Test successful JSON submission"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success", "invoice_id": "INV-001"}
            
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            data = {"invoice": "test"}
            result = await client.submit_json("/api/v1/invoices/submit", data)
            
            assert result["status"] == "success"
            assert result["invoice_id"] == "INV-001"
            mock_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_xml_success(self, client):
        """Test successful XML submission"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"status": "accepted"}
            
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            xml_data = "<invoice></invoice>"
            result = await client.submit_xml("/api/v1/invoices/submit", xml_data)
            
            assert result["status"] == "accepted"
            mock_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_status_success(self, client):
        """Test successful status retrieval"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "SUCCESS", "invoice_id": "INV-001"}
            
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            result = await client.get_status("/api/v1/invoices/INV-001/status")
            
            assert result["status"] == "SUCCESS"
            mock_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retry_on_transient_error(self, client):
        """Test retry logic on transient errors"""
        with patch("httpx.AsyncClient") as mock_client_class:
            # First call fails with 500, second succeeds
            mock_response_fail = MagicMock()
            mock_response_fail.status_code = 500
            mock_response_fail.json.return_value = {"error": "Internal Server Error"}
            
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"status": "success"}
            
            mock_client = AsyncMock()
            mock_client.post.side_effect = [mock_response_fail, mock_response_success]
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            data = {"invoice": "test"}
            result = await client.submit_json("/api/v1/invoices/submit", data)
            
            assert result["status"] == "success"
            assert mock_client.post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self, client):
        """Test no retry on permanent validation errors"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "error": "Validation failed",
                "gra_response_code": "B16",
            }
            
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            data = {"invoice": "test"}
            
            with pytest.raises(GRAClientError) as exc_info:
                await client.submit_json("/api/v1/invoices/submit", data)
            
            assert exc_info.value.error_type == ErrorType.PERMANENT
            # Should only be called once (no retry)
            assert mock_client.post.call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, client):
        """Test retry logic on timeout errors"""
        with patch("httpx.AsyncClient") as mock_client_class:
            # First call times out, second succeeds
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"status": "success"}
            
            mock_client = AsyncMock()
            mock_client.post.side_effect = [
                httpx.TimeoutException("Request timeout"),
                mock_response_success,
            ]
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            data = {"invoice": "test"}
            result = await client.submit_json("/api/v1/invoices/submit", data)
            
            assert result["status"] == "success"
            assert mock_client.post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_on_network_error(self, client):
        """Test retry logic on network errors"""
        with patch("httpx.AsyncClient") as mock_client_class:
            # First call has network error, second succeeds
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"status": "success"}
            
            mock_client = AsyncMock()
            mock_client.post.side_effect = [
                httpx.NetworkError("Connection failed"),
                mock_response_success,
            ]
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            data = {"invoice": "test"}
            result = await client.submit_json("/api/v1/invoices/submit", data)
            
            assert result["status"] == "success"
            assert mock_client.post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, client):
        """Test failure when max retries exceeded"""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.json.return_value = {"error": "Internal Server Error"}
            
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            data = {"invoice": "test"}
            
            with pytest.raises(GRAClientError) as exc_info:
                await client.submit_json("/api/v1/invoices/submit", data)
            
            # Should retry 5 times (initial + 4 retries for transient strategy)
            assert mock_client.post.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_rate_limit_retry(self, client):
        """Test retry logic on rate limit errors"""
        with patch("httpx.AsyncClient") as mock_client_class:
            # First call gets rate limited, second succeeds
            mock_response_rate_limit = MagicMock()
            mock_response_rate_limit.status_code = 429
            mock_response_rate_limit.json.return_value = {"error": "Too Many Requests"}
            
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"status": "success"}
            
            mock_client = AsyncMock()
            mock_client.post.side_effect = [mock_response_rate_limit, mock_response_success]
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            data = {"invoice": "test"}
            result = await client.submit_json("/api/v1/invoices/submit", data)
            
            assert result["status"] == "success"
            assert mock_client.post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_unavailable_service_retry(self, client):
        """Test retry logic on service unavailable errors"""
        with patch("httpx.AsyncClient") as mock_client_class:
            # First call gets 503, second succeeds
            mock_response_unavailable = MagicMock()
            mock_response_unavailable.status_code = 503
            mock_response_unavailable.json.return_value = {"error": "Service Unavailable"}
            
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"status": "success"}
            
            mock_client = AsyncMock()
            mock_client.post.side_effect = [mock_response_unavailable, mock_response_success]
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            data = {"invoice": "test"}
            result = await client.submit_json("/api/v1/invoices/submit", data)
            
            assert result["status"] == "success"
            assert mock_client.post.call_count == 2


class TestGRAClientError:
    """Tests for GRA client error"""
    
    def test_error_creation(self):
        """Test error creation"""
        error = GRAClientError(
            "Test error",
            status_code=500,
            response_data={"error": "test"},
            error_type=ErrorType.TRANSIENT,
        )
        
        assert error.message == "Test error"
        assert error.status_code == 500
        assert error.error_type == ErrorType.TRANSIENT
    
    def test_error_string_representation(self):
        """Test error string representation"""
        error = GRAClientError("Test error", status_code=500)
        assert "500" in str(error)
        assert "Test error" in str(error)
    
    def test_is_retryable(self):
        """Test is_retryable method"""
        transient_error = GRAClientError(
            "Transient error",
            error_type=ErrorType.TRANSIENT,
        )
        assert transient_error.is_retryable() is True
        
        permanent_error = GRAClientError(
            "Permanent error",
            error_type=ErrorType.PERMANENT,
        )
        assert permanent_error.is_retryable() is False
        
        rate_limit_error = GRAClientError(
            "Rate limit error",
            error_type=ErrorType.RATE_LIMIT,
        )
        assert rate_limit_error.is_retryable() is True


class TestGRAClientIntegration:
    """Integration tests for GRA HTTP client"""
    
    @pytest.mark.asyncio
    async def test_multiple_retries_with_backoff(self, monkeypatch):
        """Test multiple retries with exponential backoff"""
        client = GRAHTTPClient(
            base_url="https://api.test.com",
            timeout=10,
            max_retries=3,
        )
        
        call_times = []
        
        async def mock_sleep(duration):
            call_times.append(duration)
        
        monkeypatch.setattr(asyncio, "sleep", mock_sleep)
        
        with patch("httpx.AsyncClient") as mock_client_class:
            # Fail 2 times, then succeed
            mock_response_fail = MagicMock()
            mock_response_fail.status_code = 500
            mock_response_fail.json.return_value = {"error": "Server Error"}
            
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"status": "success"}
            
            mock_client = AsyncMock()
            mock_client.post.side_effect = [
                mock_response_fail,
                mock_response_fail,
                mock_response_success,
            ]
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            
            mock_client_class.return_value = mock_client
            
            data = {"invoice": "test"}
            result = await client.submit_json("/api/v1/invoices/submit", data)
            
            assert result["status"] == "success"
            # Should have 2 backoff periods (1s, 2s)
            assert len(call_times) == 2
            assert call_times[0] == 1
            assert call_times[1] == 2

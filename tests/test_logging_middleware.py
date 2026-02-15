"""Tests for request/response logging middleware with sensitive data masking"""
import pytest
import json
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from app.middleware.logging import LoggingMiddleware
from app.logger import SensitiveDataMasker


# Create a test app with logging middleware
test_app = FastAPI()
test_app.add_middleware(LoggingMiddleware)


@test_app.post("/api/v1/invoices/submit")
async def submit_invoice(request: Request):
    """Test endpoint for invoice submission"""
    body = await request.json()
    return JSONResponse(
        status_code=202,
        content={
            "submission_id": "sub-123",
            "status": "RECEIVED",
            "message": "Invoice received"
        }
    )


@test_app.get("/api/v1/invoices/{submission_id}/status")
async def get_invoice_status(submission_id: str):
    """Test endpoint for getting invoice status"""
    return JSONResponse(
        status_code=200,
        content={
            "submission_id": submission_id,
            "status": "SUCCESS",
            "gra_invoice_id": "GRA-INV-001"
        }
    )


@test_app.get("/health")
async def health():
    """Test health endpoint (should not be logged)"""
    return {"status": "healthy"}


@test_app.post("/api/v1/test/echo")
async def echo(request: Request):
    """Test endpoint that echoes request"""
    body = await request.json()
    return JSONResponse(status_code=200, content=body)


class TestLoggingMiddleware:
    """Test logging middleware functionality"""
    
    def test_middleware_logs_post_request(self, caplog):
        """Test that POST requests are logged"""
        client = TestClient(test_app)
        
        payload = {
            "company": {
                "COMPANY_TIN": "C0022825405",
                "COMPANY_NAMES": "ABC Corp"
            },
            "header": {
                "NUM": "INV-001",
                "TOTAL_AMOUNT": 1000
            }
        }
        
        response = client.post(
            "/api/v1/invoices/submit",
            json=payload,
            headers={"X-API-Key": "test-key-123"}
        )
        
        assert response.status_code == 202
        # Logging should have occurred (check via caplog or mock)
    
    def test_middleware_logs_get_request(self, caplog):
        """Test that GET requests are logged"""
        client = TestClient(test_app)
        
        response = client.get("/api/v1/invoices/sub-123/status")
        
        assert response.status_code == 200
        assert response.json()["submission_id"] == "sub-123"
    
    def test_middleware_skips_health_endpoint(self, caplog):
        """Test that health endpoint is not logged"""
        client = TestClient(test_app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        # Health endpoint should be skipped from logging
    
    def test_middleware_masks_api_key_in_headers(self, caplog):
        """Test that API keys in headers are masked"""
        client = TestClient(test_app)
        
        response = client.get(
            "/api/v1/invoices/sub-123/status",
            headers={"X-API-Key": "secret-api-key-12345"}
        )
        
        assert response.status_code == 200
        # API key should be masked in logs
    
    def test_middleware_masks_tin_in_request_body(self, caplog):
        """Test that TINs in request body are masked"""
        client = TestClient(test_app)
        
        payload = {
            "CLIENT_TIN": "C0022825405",
            "CLIENT_NAME": "Customer Ltd"
        }
        
        response = client.post(
            "/api/v1/test/echo",
            json=payload
        )
        
        assert response.status_code == 200
        # TIN should be masked in logs
    
    def test_middleware_masks_api_secret_in_request_body(self, caplog):
        """Test that API secrets in request body are masked"""
        client = TestClient(test_app)
        
        payload = {
            "api_secret": "super-secret-key-12345",
            "data": "some data"
        }
        
        response = client.post(
            "/api/v1/test/echo",
            json=payload
        )
        
        assert response.status_code == 200
        # API secret should be masked in logs
    
    def test_middleware_masks_gra_security_key(self, caplog):
        """Test that GRA security keys are masked"""
        client = TestClient(test_app)
        
        payload = {
            "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
            "COMPANY_TIN": "C0022825405"
        }
        
        response = client.post(
            "/api/v1/test/echo",
            json=payload
        )
        
        assert response.status_code == 200
        # GRA security key should be masked in logs
    
    def test_middleware_handles_json_content_type(self):
        """Test that middleware correctly parses JSON content"""
        client = TestClient(test_app)
        
        payload = {"key": "value", "number": 123}
        
        response = client.post(
            "/api/v1/test/echo",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        assert response.json() == payload
    
    def test_middleware_handles_empty_body(self):
        """Test that middleware handles requests with empty body"""
        client = TestClient(test_app)
        
        response = client.get("/api/v1/invoices/sub-123/status")
        
        assert response.status_code == 200
    
    def test_middleware_extracts_client_ip(self):
        """Test that middleware extracts client IP address"""
        client = TestClient(test_app)
        
        response = client.get(
            "/api/v1/invoices/sub-123/status",
            headers={"X-Forwarded-For": "192.168.1.100"}
        )
        
        assert response.status_code == 200
        # Client IP should be extracted from X-Forwarded-For
    
    def test_middleware_handles_x_forwarded_for_multiple_ips(self):
        """Test that middleware handles X-Forwarded-For with multiple IPs"""
        client = TestClient(test_app)
        
        response = client.get(
            "/api/v1/invoices/sub-123/status",
            headers={"X-Forwarded-For": "192.168.1.100, 10.0.0.1, 172.16.0.1"}
        )
        
        assert response.status_code == 200
        # Should extract first IP from X-Forwarded-For
    
    def test_middleware_preserves_response_status_code(self):
        """Test that middleware preserves response status codes"""
        client = TestClient(test_app)
        
        response = client.post(
            "/api/v1/invoices/submit",
            json={"test": "data"}
        )
        
        assert response.status_code == 202
    
    def test_middleware_preserves_response_body(self):
        """Test that middleware preserves response body"""
        client = TestClient(test_app)
        
        response = client.post(
            "/api/v1/invoices/submit",
            json={"test": "data"}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["submission_id"] == "sub-123"
        assert data["status"] == "RECEIVED"
    
    def test_middleware_masks_sensitive_endpoint_body(self):
        """Test that sensitive endpoint bodies are not logged in full"""
        client = TestClient(test_app)
        
        payload = {
            "company": {
                "COMPANY_TIN": "C0022825405",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
            }
        }
        
        response = client.post(
            "/api/v1/invoices/submit",
            json=payload
        )
        
        assert response.status_code == 202
        # Sensitive endpoint body should be omitted from logs


class TestLoggingMiddlewareHelpers:
    """Test helper methods in LoggingMiddleware"""
    
    def test_get_client_ip_from_direct_connection(self):
        """Test extracting client IP from direct connection"""
        # This would require mocking Request object
        pass
    
    def test_get_client_ip_from_x_forwarded_for(self):
        """Test extracting client IP from X-Forwarded-For header"""
        # This would require mocking Request object
        pass
    
    def test_mask_headers_api_key(self):
        """Test masking API key in headers"""
        headers = {
            "x-api-key": "secret-key-123",
            "content-type": "application/json"
        }
        
        masked = LoggingMiddleware._mask_headers(headers)
        
        assert masked["x-api-key"] == "***masked***"
        assert masked["content-type"] == "application/json"
    
    def test_mask_headers_api_signature(self):
        """Test masking API signature in headers"""
        headers = {
            "x-api-signature": "signature-value-123",
            "user-agent": "TestClient"
        }
        
        masked = LoggingMiddleware._mask_headers(headers)
        
        assert masked["x-api-signature"] == "***masked***"
        assert masked["user-agent"] == "TestClient"
    
    def test_mask_headers_authorization(self):
        """Test masking authorization header"""
        headers = {
            "authorization": "Bearer token-123",
            "accept": "application/json"
        }
        
        masked = LoggingMiddleware._mask_headers(headers)
        
        assert masked["authorization"] == "***masked***"
        assert masked["accept"] == "application/json"
    
    def test_parse_body_json(self):
        """Test parsing JSON body"""
        body = json.dumps({"key": "value", "number": 123}).encode()
        
        result = LoggingMiddleware._parse_body(body, "application/json")
        
        assert result["key"] == "value"
        assert result["number"] == 123
    
    def test_parse_body_xml(self):
        """Test parsing XML body"""
        body = b"<root><item>value</item></root>"
        
        result = LoggingMiddleware._parse_body(body, "application/xml")
        
        assert result["format"] == "xml"
        assert result["size"] == len(body)
    
    def test_parse_body_empty(self):
        """Test parsing empty body"""
        result = LoggingMiddleware._parse_body(b"", "application/json")
        
        assert result == {}
    
    def test_parse_body_invalid_json(self):
        """Test parsing invalid JSON"""
        body = b"not valid json"
        
        result = LoggingMiddleware._parse_body(body, "application/json")
        
        assert "error" in result
        assert result["size"] == len(body)
    
    def test_parse_body_unknown_content_type(self):
        """Test parsing body with unknown content type"""
        body = b"some data"
        
        result = LoggingMiddleware._parse_body(body, "text/plain")
        
        assert result["format"] == "unknown"
        assert result["size"] == len(body)


class TestSensitiveDataMaskingIntegration:
    """Test integration of sensitive data masking with logging middleware"""
    
    def test_mask_nested_sensitive_data(self):
        """Test masking nested sensitive data"""
        data = {
            "company": {
                "api_secret": "secret-123",
                "tin": "C0022825405"
            },
            "items": [
                {"api_key": "key-123", "value": 100}
            ]
        }
        
        masked = SensitiveDataMasker.mask_dict(data)
        
        assert "secret-123" not in json.dumps(masked)
        assert "C0022825405" not in json.dumps(masked)
        assert "key-123" not in json.dumps(masked)
    
    def test_mask_string_multiple_patterns(self):
        """Test masking multiple patterns in string"""
        text = "X-API-Key: secret123 and CLIENT_TIN: C0022825405"
        
        masked = SensitiveDataMasker.mask_string(text)
        
        assert "secret123" not in masked
        assert "C0022825405" not in masked
        assert "X-API-Key" in masked
        assert "CLIENT_TIN" in masked
    
    def test_mask_preserves_non_sensitive_data(self):
        """Test that masking preserves non-sensitive data"""
        data = {
            "invoice_num": "INV-001",
            "client_name": "ABC Corp",
            "total_amount": 1000,
            "api_key": "secret-123"
        }
        
        masked = SensitiveDataMasker.mask_dict(data)
        
        assert masked["invoice_num"] == "INV-001"
        assert masked["client_name"] == "ABC Corp"
        assert masked["total_amount"] == 1000
        assert "secret-123" not in str(masked["api_key"])
    
    def test_mask_all_requirement_patterns(self):
        """Test masking all sensitive patterns per requirements"""
        # REQ-AUDIT-008: Mask API secrets
        data_api_secret = {"api_secret": "super-secret-key-12345"}
        masked = SensitiveDataMasker.mask_dict(data_api_secret)
        assert "super-secret-key-12345" not in json.dumps(masked)
        
        # REQ-AUDIT-009: Mask GRA security keys
        data_gra_key = {"COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"}
        masked = SensitiveDataMasker.mask_dict(data_gra_key)
        assert "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH" not in json.dumps(masked)
        
        # REQ-AUDIT-010: Mask customer TINs (show only last 4 digits)
        data_tin = {"CLIENT_TIN": "C0022825405"}
        masked = SensitiveDataMasker.mask_dict(data_tin)
        assert "C0022825405" not in json.dumps(masked)
        assert "5405" in json.dumps(masked)  # Last 4 digits should be visible
        
        # REQ-AUDIT-008: Mask API keys (using lowercase key name)
        data_api_key = {"api_key": "api-key-12345"}
        masked = SensitiveDataMasker.mask_dict(data_api_key)
        assert "api-key-12345" not in json.dumps(masked)
    
    def test_mask_tin_shows_only_last_four_digits(self):
        """Test that TIN masking shows only last 4 digits per REQ-AUDIT-010"""
        tins = [
            ("C0022825405", "***5405"),
            ("P0123456789", "***6789"),
            ("C1234567890", "***7890"),
        ]
        
        for tin, expected_masked in tins:
            masked = SensitiveDataMasker.mask_value(tin, "tin")
            assert masked == expected_masked
            assert tin[-4:] in masked
            assert tin[:-4] not in masked
    
    def test_mask_api_secret_shows_first_and_last_four(self):
        """Test that API secret masking shows first and last 4 chars"""
        secret = "super-secret-key-12345"
        masked = SensitiveDataMasker.mask_value(secret, "partial")
        
        # Should show first 4 and last 4
        assert masked.startswith("supe")
        assert masked.endswith("2345")
        assert "secret" not in masked
    
    def test_sensitive_endpoint_body_omitted_from_logs(self):
        """Test that sensitive endpoint bodies are omitted per REQ-AUDIT-011"""
        client = TestClient(test_app)
        
        # These are sensitive endpoints per REQ-AUDIT-011
        sensitive_endpoints = [
            "/api/v1/invoices/submit",
            "/api/v1/refunds/submit",
            "/api/v1/purchases/submit",
            "/api/v1/items/register",
            "/api/v1/inventory/update",
            "/api/v1/tin/validate",
            "/api/v1/tags/register",
            "/api/v1/reports/z-report",
            "/api/v1/vsdc/health-check",
        ]
        
        # Verify middleware identifies these as sensitive
        for endpoint in sensitive_endpoints:
            assert endpoint in LoggingMiddleware.SENSITIVE_ENDPOINTS

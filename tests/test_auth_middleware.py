"""Tests for authentication middleware"""
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from app.middleware.auth import AuthMiddleware, AuthenticationError
from app.utils.hmac_signature import HMACSignatureManager
from app.services.business_service import BusinessService
from app.services.api_key_service import APIKeyService
from app.database import SessionLocal


@pytest.fixture
def app():
    """Create a test FastAPI app"""
    app = FastAPI()
    
    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}
    
    @app.post("/api/v1/test")
    async def test_endpoint(request: Request):
        return {"message": "success"}
    
    return app


@pytest.fixture
def client(app):
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def db():
    """Create a database session for testing"""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_business(db):
    """Create a test business"""
    business, api_secret = BusinessService.create_business(
        db=db,
        business_name="Test Business",
        gra_tin="C00XXXXXXXX",
        gra_company_name="TEST COMPANY",
        gra_security_key="TESTSECURITYKEY123456789012345"
    )
    return business, api_secret


class TestAuthMiddlewarePublicEndpoints:
    """Test public endpoint access"""
    
    def test_health_endpoint_no_auth(self, client):
        """Health endpoint should not require authentication"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestAuthMiddlewareHeaders:
    """Test header validation"""
    
    def test_missing_api_key_header(self, client, test_business):
        """Should fail if X-API-Key header is missing"""
        business, api_secret = test_business
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        response = client.post(
            "/api/v1/test",
            headers={
                "X-API-Signature": "test",
                "X-API-Timestamp": timestamp
            }
        )
        assert response.status_code == 401
        assert response.json()["error_code"] == "AUTH_FAILED"
    
    def test_missing_signature_header(self, client, test_business):
        """Should fail if X-API-Signature header is missing"""
        business, api_secret = test_business
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        response = client.post(
            "/api/v1/test",
            headers={
                "X-API-Key": business.api_key,
                "X-API-Timestamp": timestamp
            }
        )
        assert response.status_code == 401
        assert response.json()["error_code"] == "AUTH_FAILED"
    
    def test_missing_timestamp_header(self, client, test_business):
        """Should fail if X-API-Timestamp header is missing"""
        business, api_secret = test_business
        
        response = client.post(
            "/api/v1/test",
            headers={
                "X-API-Key": business.api_key,
                "X-API-Signature": "test"
            }
        )
        assert response.status_code == 401
        assert response.json()["error_code"] == "AUTH_FAILED"


class TestAuthMiddlewareSignature:
    """Test signature verification"""
    
    def test_valid_signature(self, client, test_business):
        """Should accept valid signature"""
        business, api_secret = test_business
        timestamp = datetime.utcnow().isoformat() + "Z"
        body = json.dumps({"test": "data"}).encode()
        
        # Generate valid signature
        body_hash = HMACSignatureManager.generate_body_hash(body)
        message = HMACSignatureManager.generate_signature_message(
            method="POST",
            path="/api/v1/test",
            timestamp=timestamp,
            body_hash=body_hash
        )
        signature = HMACSignatureManager.generate_signature(api_secret, message)
        
        response = client.post(
            "/api/v1/test",
            json={"test": "data"},
            headers={
                "X-API-Key": business.api_key,
                "X-API-Signature": signature,
                "X-API-Timestamp": timestamp
            }
        )
        assert response.status_code == 200
    
    def test_invalid_signature(self, client, test_business):
        """Should reject invalid signature"""
        business, api_secret = test_business
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        response = client.post(
            "/api/v1/test",
            json={"test": "data"},
            headers={
                "X-API-Key": business.api_key,
                "X-API-Signature": "invalid_signature",
                "X-API-Timestamp": timestamp
            }
        )
        assert response.status_code == 401
        assert response.json()["error_code"] == "AUTH_FAILED"


class TestAuthMiddlewareTimestamp:
    """Test timestamp validation"""
    
    def test_timestamp_too_old(self, client, test_business):
        """Should reject timestamp older than 5 minutes"""
        business, api_secret = test_business
        # Create timestamp 6 minutes in the past
        old_timestamp = (datetime.utcnow() - timedelta(minutes=6)).isoformat() + "Z"
        
        response = client.post(
            "/api/v1/test",
            json={"test": "data"},
            headers={
                "X-API-Key": business.api_key,
                "X-API-Signature": "test",
                "X-API-Timestamp": old_timestamp
            }
        )
        assert response.status_code == 401
        assert "Timestamp outside acceptable window" in response.json()["message"]
    
    def test_timestamp_in_future(self, client, test_business):
        """Should reject timestamp in the future"""
        business, api_secret = test_business
        # Create timestamp 1 minute in the future
        future_timestamp = (datetime.utcnow() + timedelta(minutes=1)).isoformat() + "Z"
        
        response = client.post(
            "/api/v1/test",
            json={"test": "data"},
            headers={
                "X-API-Key": business.api_key,
                "X-API-Signature": "test",
                "X-API-Timestamp": future_timestamp
            }
        )
        assert response.status_code == 401
        assert "Timestamp outside acceptable window" in response.json()["message"]


class TestAuthMiddlewareBusinessStatus:
    """Test business status validation"""
    
    def test_inactive_business(self, db, client, test_business):
        """Should reject requests from inactive businesses"""
        business, api_secret = test_business
        
        # Deactivate business
        BusinessService.deactivate_business(db, business.id)
        
        timestamp = datetime.utcnow().isoformat() + "Z"
        body = json.dumps({"test": "data"}).encode()
        
        # Generate valid signature
        body_hash = HMACSignatureManager.generate_body_hash(body)
        message = HMACSignatureManager.generate_signature_message(
            method="POST",
            path="/api/v1/test",
            timestamp=timestamp,
            body_hash=body_hash
        )
        signature = HMACSignatureManager.generate_signature(api_secret, message)
        
        response = client.post(
            "/api/v1/test",
            json={"test": "data"},
            headers={
                "X-API-Key": business.api_key,
                "X-API-Signature": signature,
                "X-API-Timestamp": timestamp
            }
        )
        assert response.status_code == 401
        assert "inactive" in response.json()["message"].lower()


class TestAuthMiddlewareInvalidApiKey:
    """Test invalid API key handling"""
    
    def test_nonexistent_api_key(self, client):
        """Should reject nonexistent API key"""
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        response = client.post(
            "/api/v1/test",
            json={"test": "data"},
            headers={
                "X-API-Key": "nonexistent_key",
                "X-API-Signature": "test",
                "X-API-Timestamp": timestamp
            }
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["message"]


class TestAuthMiddlewareErrorResponse:
    """Test error response format"""
    
    def test_error_response_format(self, client):
        """Error response should have correct format"""
        response = client.post(
            "/api/v1/test",
            json={"test": "data"},
            headers={
                "X-API-Key": "invalid",
                "X-API-Signature": "test",
                "X-API-Timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "error_code" in data
        assert "message" in data
        assert "timestamp" in data
        assert data["error_code"] == "AUTH_FAILED"

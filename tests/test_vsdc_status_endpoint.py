"""Tests for VSDC status retrieval endpoint"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import uuid4
import secrets

from app.main import app
from app.database import get_db
from app.models.models import Business, VSDCHealthCheck


client = TestClient(app)


@pytest.fixture
def test_business(db_session):
    """Create a test business with unique API key"""
    business = Business(
        id=uuid4(),
        name="Test Business",
        api_key=f"test-vsdc-status-key-{secrets.token_hex(8)}",
        api_secret=f"test-vsdc-status-secret-{secrets.token_hex(8)}",
        gra_tin="C00XXXXXXXX",
        gra_company_name="Test Company",
        gra_security_key="test-security-key"
    )
    db_session.add(business)
    db_session.commit()
    db_session.refresh(business)
    return business


@pytest.fixture
def override_get_db(db_session):
    """Override get_db dependency"""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


class TestVSDCStatusRetrievalEndpoint:
    """Test suite for GET /api/v1/vsdc/status endpoint"""
    
    def test_get_vsdc_status_successful_retrieval(self, db_session, test_business, override_get_db):
        """
        Test successful VSDC status retrieval
        
        **Validates: Requirements REQ-HEALTH-004, REQ-HEALTH-005, REQ-HEALTH-006**
        
        Acceptance Criteria:
        - Endpoint returns 200 OK with cached status
        - Returns last check timestamp
        - Returns uptime percentage
        """
        # Create a cached health check
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        health_check = VSDCHealthCheck(
            business_id=test_business.id,
            status="UP",
            sdc_id="SDC-12345",
            gra_response_code=None,
            expires_at=expires_at
        )
        db_session.add(health_check)
        db_session.commit()
        
        # Make request
        response = client.get(
            "/api/v1/vsdc/status",
            headers={"X-API-Key": test_business.api_key}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UP"
        assert data["sdc_id"] == "SDC-12345"
        assert data["uptime_percentage"] == 100.0
        assert data["is_cached"] is True
        assert "last_checked_at" in data
    
    def test_get_vsdc_status_no_cached_status(self, db_session, test_business, override_get_db):
        """
        Test handling when no cached status exists
        
        **Validates: Requirements REQ-HEALTH-004, REQ-HEALTH-006**
        
        Acceptance Criteria:
        - Handles no cached status with appropriate response (404)
        """
        # Make request without any health check data
        response = client.get(
            "/api/v1/vsdc/status",
            headers={"X-API-Key": test_business.api_key}
        )
        
        # Verify 404 response
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "No VSDC health check data available" in data["detail"]
    
    def test_get_vsdc_status_down_status(self, db_session, test_business, override_get_db):
        """
        Test VSDC status retrieval when status is DOWN
        
        **Validates: Requirements REQ-HEALTH-005**
        
        Acceptance Criteria:
        - Returns uptime percentage of 0% for DOWN status
        """
        # Create a DOWN health check
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        health_check = VSDCHealthCheck(
            business_id=test_business.id,
            status="DOWN",
            sdc_id=None,
            gra_response_code="D06",
            expires_at=expires_at
        )
        db_session.add(health_check)
        db_session.commit()
        
        # Make request
        response = client.get(
            "/api/v1/vsdc/status",
            headers={"X-API-Key": test_business.api_key}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DOWN"
        assert data["uptime_percentage"] == 0.0
    
    def test_get_vsdc_status_degraded_status(self, db_session, test_business, override_get_db):
        """
        Test VSDC status retrieval when status is DEGRADED
        
        **Validates: Requirements REQ-HEALTH-005**
        
        Acceptance Criteria:
        - Returns uptime percentage of 50% for DEGRADED status
        """
        # Create a DEGRADED health check
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        health_check = VSDCHealthCheck(
            business_id=test_business.id,
            status="DEGRADED",
            sdc_id="SDC-12345",
            gra_response_code=None,
            expires_at=expires_at
        )
        db_session.add(health_check)
        db_session.commit()
        
        # Make request
        response = client.get(
            "/api/v1/vsdc/status",
            headers={"X-API-Key": test_business.api_key}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DEGRADED"
        assert data["uptime_percentage"] == 50.0
    
    def test_get_vsdc_status_expired_cache(self, db_session, test_business, override_get_db):
        """
        Test VSDC status retrieval with expired cache
        
        **Validates: Requirements REQ-HEALTH-004, REQ-HEALTH-005**
        
        Acceptance Criteria:
        - Returns is_cached=False when cache is expired
        """
        # Create an expired health check
        expires_at = datetime.utcnow() - timedelta(minutes=1)  # Expired
        health_check = VSDCHealthCheck(
            business_id=test_business.id,
            status="UP",
            sdc_id="SDC-12345",
            gra_response_code=None,
            expires_at=expires_at
        )
        db_session.add(health_check)
        db_session.commit()
        
        # Make request
        response = client.get(
            "/api/v1/vsdc/status",
            headers={"X-API-Key": test_business.api_key}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UP"
        assert data["is_cached"] is False  # Cache expired
    
    def test_get_vsdc_status_invalid_api_key(self, db_session, override_get_db):
        """
        Test VSDC status retrieval with invalid API key
        
        **Validates: Requirements REQ-HEALTH-004**
        
        Acceptance Criteria:
        - Returns 401 Unauthorized for invalid API key
        """
        # Make request with invalid API key
        response = client.get(
            "/api/v1/vsdc/status",
            headers={"X-API-Key": "invalid-api-key"}
        )
        
        # Verify 401 response
        assert response.status_code == 401
    
    def test_get_vsdc_status_missing_api_key(self, db_session, override_get_db):
        """
        Test VSDC status retrieval without API key
        
        **Validates: Requirements REQ-HEALTH-004**
        
        Acceptance Criteria:
        - Returns error when API key is missing
        """
        # Make request without API key
        response = client.get("/api/v1/vsdc/status")
        
        # Verify error response (422 for missing required parameter)
        assert response.status_code in [403, 422]
    
    def test_get_vsdc_status_latest_check_retrieved(self, db_session, test_business, override_get_db):
        """
        Test that latest health check is retrieved when multiple exist
        
        **Validates: Requirements REQ-HEALTH-004, REQ-HEALTH-005**
        
        Acceptance Criteria:
        - Returns the most recent health check
        """
        # Create multiple health checks
        expires_at_1 = datetime.utcnow() + timedelta(minutes=5)
        health_check_1 = VSDCHealthCheck(
            business_id=test_business.id,
            status="DOWN",
            sdc_id=None,
            gra_response_code="D06",
            expires_at=expires_at_1,
            checked_at=datetime.utcnow() - timedelta(minutes=10)
        )
        db_session.add(health_check_1)
        db_session.commit()
        
        # Create a newer health check
        expires_at_2 = datetime.utcnow() + timedelta(minutes=5)
        health_check_2 = VSDCHealthCheck(
            business_id=test_business.id,
            status="UP",
            sdc_id="SDC-99999",
            gra_response_code=None,
            expires_at=expires_at_2,
            checked_at=datetime.utcnow()
        )
        db_session.add(health_check_2)
        db_session.commit()
        
        # Make request
        response = client.get(
            "/api/v1/vsdc/status",
            headers={"X-API-Key": test_business.api_key}
        )
        
        # Verify latest check is returned
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UP"  # Latest status
        assert data["sdc_id"] == "SDC-99999"  # Latest SDC ID
    
    def test_get_vsdc_status_response_schema(self, db_session, test_business, override_get_db):
        """
        Test that response schema matches expected format
        
        **Validates: Requirements REQ-HEALTH-004, REQ-HEALTH-005, REQ-HEALTH-006**
        
        Acceptance Criteria:
        - Response includes all required fields
        """
        # Create a health check
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        health_check = VSDCHealthCheck(
            business_id=test_business.id,
            status="UP",
            sdc_id="SDC-12345",
            gra_response_code=None,
            expires_at=expires_at
        )
        db_session.add(health_check)
        db_session.commit()
        
        # Make request
        response = client.get(
            "/api/v1/vsdc/status",
            headers={"X-API-Key": test_business.api_key}
        )
        
        # Verify response schema
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        assert "status" in data
        assert "sdc_id" in data
        assert "last_checked_at" in data
        assert "uptime_percentage" in data
        assert "is_cached" in data
        
        # Verify field types
        assert isinstance(data["status"], str)
        assert isinstance(data["uptime_percentage"], (int, float))
        assert isinstance(data["is_cached"], bool)
    
    def test_get_vsdc_status_multi_tenant_isolation(self, db_session, override_get_db):
        """
        Test that businesses can only access their own VSDC status
        
        **Validates: Requirements REQ-HEALTH-004**
        
        Acceptance Criteria:
        - Business A cannot access Business B's VSDC status
        """
        # Create two businesses with unique API keys
        business_a = Business(
            id=uuid4(),
            name="Business A",
            api_key=f"business-a-key-{secrets.token_hex(8)}",
            api_secret=f"business-a-secret-{secrets.token_hex(8)}",
            gra_tin="C00XXXXXXXX",
            gra_company_name="Business A",
            gra_security_key="key-a"
        )
        business_b = Business(
            id=uuid4(),
            name="Business B",
            api_key=f"business-b-key-{secrets.token_hex(8)}",
            api_secret=f"business-b-secret-{secrets.token_hex(8)}",
            gra_tin="C00YYYYYYYY",
            gra_company_name="Business B",
            gra_security_key="key-b"
        )
        db_session.add(business_a)
        db_session.add(business_b)
        db_session.commit()
        
        # Create health check for Business B
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        health_check_b = VSDCHealthCheck(
            business_id=business_b.id,
            status="UP",
            sdc_id="SDC-B",
            gra_response_code=None,
            expires_at=expires_at
        )
        db_session.add(health_check_b)
        db_session.commit()
        
        # Business A tries to get status (should get 404 - no data for A)
        response = client.get(
            "/api/v1/vsdc/status",
            headers={"X-API-Key": business_a.api_key}
        )
        
        # Should return 404 since Business A has no health check
        assert response.status_code == 404
        
        # Business B gets their own status (should succeed)
        response = client.get(
            "/api/v1/vsdc/status",
            headers={"X-API-Key": business_b.api_key}
        )
        
        # Should return 200 with Business B's data
        assert response.status_code == 200
        data = response.json()
        assert data["sdc_id"] == "SDC-B"

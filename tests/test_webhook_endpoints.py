"""Tests for webhook management endpoints"""
import pytest
from uuid import uuid4
from datetime import datetime

from app.models.models import Business, Webhook
from tests.conftest import create_test_business, create_test_api_key


@pytest.fixture
def test_business(db_session):
    """Create a test business"""
    return create_test_business(db_session)


@pytest.fixture
def test_api_key(db_session, test_business):
    """Create a test API key"""
    return create_test_api_key(db_session, test_business.id)


@pytest.fixture
def auth_headers(test_api_key):
    """Generate authentication headers"""
    from app.utils.hmac_signature import HMACSignatureManager
    from datetime import datetime
    
    api_key = test_api_key.api_key
    api_secret = test_api_key.api_secret
    
    # For GET requests, use empty body
    timestamp = datetime.utcnow().isoformat() + "Z"
    signature = HMACSignatureManager.generate_signature(api_secret, "")
    
    return {
        "X-API-Key": api_key,
        "X-API-Signature": signature,
        "X-API-Timestamp": timestamp
    }


class TestWebhookRegistration:
    """Tests for webhook registration endpoint"""
    
    def test_register_webhook_success(self, auth_headers, db_session, test_business, client_with_db):
        """Test successful webhook registration"""
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invoice.success", "invoice.failed"]
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["webhook_url"] == payload["webhook_url"]
        assert data["events"] == payload["events"]
        assert data["is_active"] is True
        assert "webhook_id" in data
        assert "created_at" in data
        
        # Verify webhook was stored in database
        webhook = db_session.query(Webhook).filter(
            Webhook.id == data["webhook_id"]
        ).first()
        assert webhook is not None
        assert webhook.business_id == test_business.id
    
    def test_register_webhook_multiple_events(self, auth_headers, db_session, test_business, client_with_db):
        """Test webhook registration with multiple event types"""
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invoice.success", "invoice.failed", "refund.success", "purchase.failed"]
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data["events"]) == 4
        assert all(event in data["events"] for event in payload["events"])
    
    def test_register_webhook_invalid_url(self, auth_headers, client_with_db):
        """Test webhook registration with invalid URL"""
        payload = {
            "webhook_url": "not-a-valid-url",
            "events": ["invoice.success"]
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "http" in response.json()["detail"].lower()
    
    def test_register_webhook_invalid_event(self, auth_headers, client_with_db):
        """Test webhook registration with invalid event type"""
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invalid.event"]
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    def test_register_webhook_missing_events(self, auth_headers, client_with_db):
        """Test webhook registration without events"""
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": []
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400
    
    def test_register_webhook_missing_url(self, auth_headers, client_with_db):
        """Test webhook registration without URL"""
        payload = {
            "events": ["invoice.success"]
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_register_webhook_url_too_long(self, auth_headers, client_with_db):
        """Test webhook registration with URL exceeding max length"""
        long_url = "https://example.com/" + "a" * 500
        payload = {
            "webhook_url": long_url,
            "events": ["invoice.success"]
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "500" in response.json()["detail"]


class TestWebhookListing:
    """Tests for webhook listing endpoint"""
    
    def test_list_webhooks_empty(self, auth_headers, client_with_db):
        """Test listing webhooks when none exist"""
        response = client_with_db.get(
            "/api/v1/webhooks",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_list_webhooks_multiple(self, auth_headers, db_session, test_business, client_with_db):
        """Test listing multiple webhooks"""
        # Register multiple webhooks
        for i in range(3):
            payload = {
                "webhook_url": f"https://example.com/webhook{i}",
                "events": ["invoice.success"]
            }
            response = client_with_db.post(
                "/api/v1/webhooks/register",
                json=payload,
                headers=auth_headers
            )
            assert response.status_code == 201
        
        # List webhooks
        response = client_with_db.get(
            "/api/v1/webhooks",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("webhook_id" in w for w in data)
        assert all("webhook_url" in w for w in data)
        assert all("events" in w for w in data)
        assert all("is_active" in w for w in data)
    
    def test_list_webhooks_multi_tenant_isolation(self, db_session, client_with_db):
        """Test that webhooks are isolated per business"""
        # Create two businesses
        business1 = create_test_business(db_session, name="Business 1")
        business2 = create_test_business(db_session, name="Business 2")
        
        # Create API keys for both
        key1 = create_test_api_key(db_session, business1.id)
        key2 = create_test_api_key(db_session, business2.id)
        
        # Register webhook for business 1
        from app.utils.hmac_signature import HMACSignatureManager
        
        payload = {
            "webhook_url": "https://example.com/webhook1",
            "events": ["invoice.success"]
        }
        
        signature1 = HMACSignatureManager.generate_signature(key1.api_secret, "")
        headers1 = {
            "X-API-Key": key1.api_key,
            "X-API-Signature": signature1
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers1
        )
        assert response.status_code == 201
        
        # List webhooks for business 2 (should be empty)
        signature2 = HMACSignatureManager.generate_signature(key2.api_secret, "")
        headers2 = {
            "X-API-Key": key2.api_key,
            "X-API-Signature": signature2
        }
        
        response = client_with_db.get(
            "/api/v1/webhooks",
            headers=headers2
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0


class TestWebhookRetrieval:
    """Tests for getting individual webhook details"""
    
    def test_get_webhook_success(self, auth_headers, db_session, test_business, client_with_db):
        """Test retrieving webhook details"""
        # Register a webhook
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invoice.success", "refund.failed"]
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=auth_headers
        )
        webhook_id = response.json()["webhook_id"]
        
        # Get webhook details
        response = client_with_db.get(
            f"/api/v1/webhooks/{webhook_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["webhook_id"] == webhook_id
        assert data["webhook_url"] == payload["webhook_url"]
        assert data["events"] == payload["events"]
    
    def test_get_webhook_not_found(self, auth_headers, client_with_db):
        """Test retrieving non-existent webhook"""
        fake_id = str(uuid4())
        
        response = client_with_db.get(
            f"/api/v1/webhooks/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_webhook_multi_tenant_isolation(self, db_session, client_with_db):
        """Test that webhooks cannot be accessed by other businesses"""
        # Create two businesses
        business1 = create_test_business(db_session, name="Business 1")
        business2 = create_test_business(db_session, name="Business 2")
        
        # Create API keys
        key1 = create_test_api_key(db_session, business1.id)
        key2 = create_test_api_key(db_session, business2.id)
        
        from app.utils.hmac_signature import HMACSignatureManager
        
        # Register webhook for business 1
        payload = {
            "webhook_url": "https://example.com/webhook1",
            "events": ["invoice.success"]
        }
        
        signature1 = HMACSignatureManager.generate_signature(key1.api_secret, "")
        headers1 = {
            "X-API-Key": key1.api_key,
            "X-API-Signature": signature1
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers1
        )
        webhook_id = response.json()["webhook_id"]
        
        # Try to access with business 2's credentials
        signature2 = HMACSignatureManager.generate_signature(key2.api_secret, "")
        headers2 = {
            "X-API-Key": key2.api_key,
            "X-API-Signature": signature2
        }
        
        response = client_with_db.get(
            f"/api/v1/webhooks/{webhook_id}",
            headers=headers2
        )
        
        assert response.status_code == 404


class TestWebhookUpdate:
    """Tests for webhook update endpoint"""
    
    def test_update_webhook_url(self, auth_headers, db_session, test_business, client_with_db):
        """Test updating webhook URL"""
        # Register a webhook
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invoice.success"]
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=auth_headers
        )
        webhook_id = response.json()["webhook_id"]
        
        # Update webhook URL
        update_payload = {
            "webhook_url": "https://newexample.com/webhooks"
        }
        
        response = client_with_db.put(
            f"/api/v1/webhooks/{webhook_id}",
            json=update_payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["webhook_url"] == update_payload["webhook_url"]
    
    def test_update_webhook_events(self, auth_headers, db_session, test_business, client_with_db):
        """Test updating webhook events"""
        # Register a webhook
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invoice.success"]
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=auth_headers
        )
        webhook_id = response.json()["webhook_id"]
        
        # Update events
        update_payload = {
            "events": ["invoice.success", "invoice.failed", "refund.success"]
        }
        
        response = client_with_db.put(
            f"/api/v1/webhooks/{webhook_id}",
            json=update_payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 3
        assert all(e in data["events"] for e in update_payload["events"])
    
    def test_update_webhook_active_status(self, auth_headers, db_session, test_business, client_with_db):
        """Test updating webhook active status"""
        # Register a webhook
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invoice.success"]
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=auth_headers
        )
        webhook_id = response.json()["webhook_id"]
        
        # Deactivate webhook
        update_payload = {
            "is_active": False
        }
        
        response = client_with_db.put(
            f"/api/v1/webhooks/{webhook_id}",
            json=update_payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
    
    def test_update_webhook_not_found(self, auth_headers, client_with_db):
        """Test updating non-existent webhook"""
        fake_id = str(uuid4())
        
        update_payload = {
            "webhook_url": "https://newexample.com/webhooks"
        }
        
        response = client_with_db.put(
            f"/api/v1/webhooks/{fake_id}",
            json=update_payload,
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestWebhookDeletion:
    """Tests for webhook deletion endpoint"""
    
    def test_delete_webhook_success(self, auth_headers, db_session, test_business, client_with_db):
        """Test successful webhook deletion"""
        # Register a webhook
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invoice.success"]
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=auth_headers
        )
        webhook_id = response.json()["webhook_id"]
        
        # Delete webhook
        response = client_with_db.delete(
            f"/api/v1/webhooks/{webhook_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["webhook_id"] == webhook_id
        assert "successfully deleted" in data["message"].lower()
        
        # Verify webhook was deleted
        webhook = db_session.query(Webhook).filter(
            Webhook.id == webhook_id
        ).first()
        assert webhook is None
    
    def test_delete_webhook_not_found(self, auth_headers, client_with_db):
        """Test deleting non-existent webhook"""
        fake_id = str(uuid4())
        
        response = client_with_db.delete(
            f"/api/v1/webhooks/{fake_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_delete_webhook_multi_tenant_isolation(self, db_session, client_with_db):
        """Test that webhooks cannot be deleted by other businesses"""
        # Create two businesses
        business1 = create_test_business(db_session, name="Business 1")
        business2 = create_test_business(db_session, name="Business 2")
        
        # Create API keys
        key1 = create_test_api_key(db_session, business1.id)
        key2 = create_test_api_key(db_session, business2.id)
        
        from app.utils.hmac_signature import HMACSignatureManager
        
        # Register webhook for business 1
        payload = {
            "webhook_url": "https://example.com/webhook1",
            "events": ["invoice.success"]
        }
        
        signature1 = HMACSignatureManager.generate_signature(key1.api_secret, "")
        headers1 = {
            "X-API-Key": key1.api_key,
            "X-API-Signature": signature1
        }
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers1
        )
        webhook_id = response.json()["webhook_id"]
        
        # Try to delete with business 2's credentials
        signature2 = HMACSignatureManager.generate_signature(key2.api_secret, "")
        headers2 = {
            "X-API-Key": key2.api_key,
            "X-API-Signature": signature2
        }
        
        response = client_with_db.delete(
            f"/api/v1/webhooks/{webhook_id}",
            headers=headers2
        )
        
        assert response.status_code == 404
        
        # Verify webhook still exists for business 1
        webhook = db_session.query(Webhook).filter(
            Webhook.id == webhook_id
        ).first()
        assert webhook is not None

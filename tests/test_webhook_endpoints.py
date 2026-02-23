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


def generate_auth_headers(api_key, api_secret, method="POST", path="/api/v1/webhooks/register", body=None):
    """Generate authentication headers for a request"""
    from app.utils.hmac_signature import HMACSignatureManager
    from datetime import datetime
    import json
    
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    if body is None:
        body = b""
    elif isinstance(body, dict):
        body = json.dumps(body).encode()
    elif isinstance(body, str):
        body = body.encode()
    
    body_hash = HMACSignatureManager.generate_body_hash(body)
    message = HMACSignatureManager.generate_signature_message(
        method=method,
        path=path,
        timestamp=timestamp,
        body_hash=body_hash
    )
    signature = HMACSignatureManager.generate_signature(api_secret, message)
    
    return {
        "X-API-Key": api_key,
        "X-API-Signature": signature,
        "X-API-Timestamp": timestamp
    }


@pytest.fixture
def auth_headers(test_api_key):
    """Generate authentication headers"""
    return generate_auth_headers(test_api_key.api_key, test_api_key.api_secret)


class TestWebhookRegistration:
    """Tests for webhook registration endpoint"""
    
    def test_register_webhook_success(self, test_api_key, db_session, test_business, client_with_db):
        """Test successful webhook registration"""
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invoice.success", "invoice.failed"]
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="POST",
            path="/api/v1/webhooks/register",
            body=payload
        )
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers
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
    
    def test_register_webhook_multiple_events(self, test_api_key, db_session, test_business, client_with_db):
        """Test webhook registration with multiple event types"""
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invoice.success", "invoice.failed", "refund.success", "purchase.failed"]
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="POST",
            path="/api/v1/webhooks/register",
            body=payload
        )
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert len(data["events"]) == 4
        assert all(event in data["events"] for event in payload["events"])
    
    def test_register_webhook_invalid_url(self, test_api_key, client_with_db):
        """Test webhook registration with invalid URL"""
        payload = {
            "webhook_url": "not-a-valid-url",
            "events": ["invoice.success"]
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="POST",
            path="/api/v1/webhooks/register",
            body=payload
        )
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 422
    
    def test_register_webhook_invalid_event(self, test_api_key, client_with_db):
        """Test webhook registration with invalid event type"""
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invalid.event"]
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="POST",
            path="/api/v1/webhooks/register",
            body=payload
        )
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 422
    
    def test_register_webhook_missing_events(self, test_api_key, client_with_db):
        """Test webhook registration without events"""
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": []
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="POST",
            path="/api/v1/webhooks/register",
            body=payload
        )
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 422
    
    def test_register_webhook_missing_url(self, test_api_key, client_with_db):
        """Test webhook registration without URL"""
        payload = {
            "events": ["invoice.success"]
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="POST",
            path="/api/v1/webhooks/register",
            body=payload
        )
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_register_webhook_url_too_long(self, test_api_key, client_with_db):
        """Test webhook registration with URL exceeding max length"""
        long_url = "https://example.com/" + "a" * 500
        payload = {
            "webhook_url": long_url,
            "events": ["invoice.success"]
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="POST",
            path="/api/v1/webhooks/register",
            body=payload
        )
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers
        )
        
        assert response.status_code == 422


class TestWebhookListing:
    """Tests for webhook listing endpoint"""
    
    def test_list_webhooks_empty(self, test_api_key, client_with_db):
        """Test listing webhooks when none exist"""
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="GET",
            path="/api/v1/webhooks/list",
            body=None
        )
        
        response = client_with_db.get(
            "/api/v1/webhooks/list",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "webhooks" in data
        assert len(data["webhooks"]) == 0
    
    def test_list_webhooks_multiple(self, test_api_key, db_session, test_business, client_with_db):
        """Test listing multiple webhooks"""
        # Register multiple webhooks
        for i in range(3):
            payload = {
                "webhook_url": f"https://example.com/webhook{i}",
                "events": ["invoice.success"]
            }
            headers = generate_auth_headers(
                test_api_key.api_key,
                test_api_key.api_secret,
                method="POST",
                path="/api/v1/webhooks/register",
                body=payload
            )
            response = client_with_db.post(
                "/api/v1/webhooks/register",
                json=payload,
                headers=headers
            )
            assert response.status_code == 201
        
        # List webhooks
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="GET",
            path="/api/v1/webhooks/list",
            body=None
        )
        
        response = client_with_db.get(
            "/api/v1/webhooks/list",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["webhooks"]) == 3
        assert all("webhook_id" in w for w in data["webhooks"])
        assert all("webhook_url" in w for w in data["webhooks"])
        assert all("events" in w for w in data["webhooks"])
        assert all("is_active" in w for w in data["webhooks"])


class TestWebhookRetrieval:
    """Tests for getting individual webhook details"""
    
    def test_get_webhook_success(self, test_api_key, db_session, test_business, client_with_db):
        """Test retrieving webhook details"""
        # Register a webhook
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invoice.success", "refund.failed"]
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="POST",
            path="/api/v1/webhooks/register",
            body=payload
        )
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers
        )
        webhook_id = response.json()["webhook_id"]
        
        # Get webhook details
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="GET",
            path=f"/api/v1/webhooks/{webhook_id}",
            body=None
        )
        
        response = client_with_db.get(
            f"/api/v1/webhooks/{webhook_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["webhook_id"] == webhook_id
        assert data["webhook_url"] == payload["webhook_url"]
        assert data["events"] == payload["events"]
    
    def test_get_webhook_not_found(self, test_api_key, client_with_db):
        """Test retrieving non-existent webhook"""
        fake_id = str(uuid4())
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="GET",
            path=f"/api/v1/webhooks/{fake_id}",
            body=None
        )
        
        response = client_with_db.get(
            f"/api/v1/webhooks/{fake_id}",
            headers=headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestWebhookUpdate:
    """Tests for webhook update endpoint"""
    
    def test_update_webhook_url(self, test_api_key, db_session, test_business, client_with_db):
        """Test updating webhook URL"""
        # Register a webhook
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invoice.success"]
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="POST",
            path="/api/v1/webhooks/register",
            body=payload
        )
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers
        )
        webhook_id = response.json()["webhook_id"]
        
        # Update webhook URL
        update_payload = {
            "webhook_url": "https://newexample.com/webhooks"
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="PUT",
            path=f"/api/v1/webhooks/{webhook_id}",
            body=update_payload
        )
        
        response = client_with_db.put(
            f"/api/v1/webhooks/{webhook_id}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["webhook_url"] == update_payload["webhook_url"]
    
    def test_update_webhook_events(self, test_api_key, db_session, test_business, client_with_db):
        """Test updating webhook events"""
        # Register a webhook
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invoice.success"]
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="POST",
            path="/api/v1/webhooks/register",
            body=payload
        )
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers
        )
        webhook_id = response.json()["webhook_id"]
        
        # Update events
        update_payload = {
            "events": ["invoice.success", "invoice.failed", "refund.success"]
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="PUT",
            path=f"/api/v1/webhooks/{webhook_id}",
            body=update_payload
        )
        
        response = client_with_db.put(
            f"/api/v1/webhooks/{webhook_id}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 3
        assert all(e in data["events"] for e in update_payload["events"])
    
    def test_update_webhook_active_status(self, test_api_key, db_session, test_business, client_with_db):
        """Test updating webhook active status"""
        # Register a webhook
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invoice.success"]
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="POST",
            path="/api/v1/webhooks/register",
            body=payload
        )
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers
        )
        webhook_id = response.json()["webhook_id"]
        
        # Deactivate webhook
        update_payload = {
            "is_active": False
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="PUT",
            path=f"/api/v1/webhooks/{webhook_id}",
            body=update_payload
        )
        
        response = client_with_db.put(
            f"/api/v1/webhooks/{webhook_id}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
    
    def test_update_webhook_not_found(self, test_api_key, client_with_db):
        """Test updating non-existent webhook"""
        fake_id = str(uuid4())
        
        update_payload = {
            "webhook_url": "https://newexample.com/webhooks"
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="PUT",
            path=f"/api/v1/webhooks/{fake_id}",
            body=update_payload
        )
        
        response = client_with_db.put(
            f"/api/v1/webhooks/{fake_id}",
            json=update_payload,
            headers=headers
        )
        
        assert response.status_code == 404


class TestWebhookDeletion:
    """Tests for webhook deletion endpoint"""
    
    def test_delete_webhook_success(self, test_api_key, db_session, test_business, client_with_db):
        """Test successful webhook deletion"""
        # Register a webhook
        payload = {
            "webhook_url": "https://example.com/webhooks",
            "events": ["invoice.success"]
        }
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="POST",
            path="/api/v1/webhooks/register",
            body=payload
        )
        
        response = client_with_db.post(
            "/api/v1/webhooks/register",
            json=payload,
            headers=headers
        )
        webhook_id = response.json()["webhook_id"]
        
        # Delete webhook
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="DELETE",
            path=f"/api/v1/webhooks/{webhook_id}",
            body=None
        )
        
        response = client_with_db.delete(
            f"/api/v1/webhooks/{webhook_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["webhook_id"] == webhook_id
        
        # Verify webhook was deleted
        webhook = db_session.query(Webhook).filter(
            Webhook.id == webhook_id
        ).first()
        assert webhook is None
    
    def test_delete_webhook_not_found(self, test_api_key, client_with_db):
        """Test deleting non-existent webhook"""
        fake_id = str(uuid4())
        
        headers = generate_auth_headers(
            test_api_key.api_key,
            test_api_key.api_secret,
            method="DELETE",
            path=f"/api/v1/webhooks/{fake_id}",
            body=None
        )
        
        response = client_with_db.delete(
            f"/api/v1/webhooks/{fake_id}",
            headers=headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

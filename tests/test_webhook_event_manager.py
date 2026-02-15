"""Tests for webhook event manager"""
import pytest
import json
from uuid import uuid4
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.services.webhook_event_manager import WebhookEventManager
from app.models.models import Submission, Webhook
from tests.conftest import create_test_business


@pytest.fixture
def test_business(db_session):
    """Create a test business"""
    return create_test_business(db_session)


@pytest.fixture
def test_submission(db_session, test_business):
    """Create a test submission"""
    submission = Submission(
        business_id=test_business.id,
        submission_type="INVOICE",
        submission_status="SUCCESS",
        gra_invoice_id="GRA-INV-001",
        gra_qr_code="https://gra.gov.gh/qr/123",
        gra_receipt_num="VSDC-REC-001",
        raw_request={"test": "data"},
        submitted_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)
    return submission


@pytest.fixture
def test_webhook(db_session, test_business):
    """Create a test webhook"""
    webhook = Webhook(
        business_id=test_business.id,
        webhook_url="https://example.com/webhooks",
        events=["invoice.success", "invoice.failed"],
        secret="test-webhook-secret",
        is_active=True,
    )
    db_session.add(webhook)
    db_session.commit()
    db_session.refresh(webhook)
    return webhook


class TestEventTypeMapping:
    """Tests for event type mapping"""
    
    def test_get_event_type_invoice_success(self):
        """Test getting event type for successful invoice"""
        event_type = WebhookEventManager.get_event_type("INVOICE", "SUCCESS")
        assert event_type == "invoice.success"
    
    def test_get_event_type_invoice_failed(self):
        """Test getting event type for failed invoice"""
        event_type = WebhookEventManager.get_event_type("INVOICE", "FAILED")
        assert event_type == "invoice.failed"
    
    def test_get_event_type_refund_success(self):
        """Test getting event type for successful refund"""
        event_type = WebhookEventManager.get_event_type("REFUND", "SUCCESS")
        assert event_type == "refund.success"
    
    def test_get_event_type_refund_failed(self):
        """Test getting event type for failed refund"""
        event_type = WebhookEventManager.get_event_type("REFUND", "FAILED")
        assert event_type == "refund.failed"
    
    def test_get_event_type_purchase_success(self):
        """Test getting event type for successful purchase"""
        event_type = WebhookEventManager.get_event_type("PURCHASE", "SUCCESS")
        assert event_type == "purchase.success"
    
    def test_get_event_type_purchase_failed(self):
        """Test getting event type for failed purchase"""
        event_type = WebhookEventManager.get_event_type("PURCHASE", "FAILED")
        assert event_type == "purchase.failed"
    
    def test_get_event_type_unsupported(self):
        """Test getting event type for unsupported submission type"""
        with pytest.raises(ValueError):
            WebhookEventManager.get_event_type("UNKNOWN", "SUCCESS")
    
    def test_get_event_type_unsupported_status(self):
        """Test getting event type for unsupported status"""
        with pytest.raises(ValueError):
            WebhookEventManager.get_event_type("INVOICE", "PENDING")


class TestSubmissionDataBuilding:
    """Tests for building submission data for webhooks"""
    
    def test_build_submission_data_success(self, db_session, test_submission):
        """Test building submission data for successful submission"""
        data = WebhookEventManager.build_submission_data(db_session, test_submission)
        
        assert data["submission_id"] == str(test_submission.id)
        assert data["submission_type"] == "INVOICE"
        assert data["status"] == "SUCCESS"
        assert data["gra_invoice_id"] == "GRA-INV-001"
        assert data["gra_qr_code"] == "https://gra.gov.gh/qr/123"
        assert data["gra_receipt_num"] == "VSDC-REC-001"
        assert "submitted_at" in data
        assert "completed_at" in data
    
    def test_build_submission_data_with_error(self, db_session, test_business):
        """Test building submission data for failed submission"""
        error_details = {
            "error": "GRA error",
            "error_type": "VALIDATION_ERROR",
            "response_data": {"code": "B16"}
        }
        
        submission = Submission(
            business_id=test_business.id,
            submission_type="INVOICE",
            submission_status="FAILED",
            gra_response_code="B16",
            gra_response_message="Total amount mismatch",
            error_details=json.dumps(error_details),
            raw_request={"test": "data"},
            submitted_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)
        
        data = WebhookEventManager.build_submission_data(db_session, submission)
        
        assert data["status"] == "FAILED"
        assert data["gra_response_code"] == "B16"
        assert data["gra_response_message"] == "Total amount mismatch"
        assert "error_details" in data
        assert data["error_details"]["error"] == "GRA error"
    
    def test_build_submission_data_minimal(self, db_session, test_business):
        """Test building submission data with minimal fields"""
        submission = Submission(
            business_id=test_business.id,
            submission_type="INVOICE",
            submission_status="SUCCESS",
            raw_request={"test": "data"},
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)
        
        data = WebhookEventManager.build_submission_data(db_session, submission)
        
        assert data["submission_id"] == str(submission.id)
        assert data["submission_type"] == "INVOICE"
        assert data["status"] == "SUCCESS"
        assert "gra_invoice_id" not in data or data.get("gra_invoice_id") is None


class TestWebhookRetrieval:
    """Tests for retrieving webhooks for events"""
    
    def test_get_webhooks_for_event_single(self, db_session, test_business, test_webhook):
        """Test getting webhooks for an event"""
        webhooks = WebhookEventManager.get_webhooks_for_event(
            db_session,
            test_business.id,
            "invoice.success"
        )
        
        assert len(webhooks) == 1
        assert webhooks[0].id == test_webhook.id
    
    def test_get_webhooks_for_event_multiple(self, db_session, test_business):
        """Test getting multiple webhooks for an event"""
        # Create multiple webhooks
        for i in range(3):
            webhook = Webhook(
                business_id=test_business.id,
                webhook_url=f"https://example.com/webhook{i}",
                events=["invoice.success"],
                secret=f"secret-{i}",
                is_active=True,
            )
            db_session.add(webhook)
        db_session.commit()
        
        webhooks = WebhookEventManager.get_webhooks_for_event(
            db_session,
            test_business.id,
            "invoice.success"
        )
        
        assert len(webhooks) == 3
    
    def test_get_webhooks_for_event_filters_inactive(self, db_session, test_business):
        """Test that inactive webhooks are not returned"""
        # Create inactive webhook
        webhook = Webhook(
            business_id=test_business.id,
            webhook_url="https://example.com/inactive",
            events=["invoice.success"],
            secret="secret",
            is_active=False,
        )
        db_session.add(webhook)
        db_session.commit()
        
        webhooks = WebhookEventManager.get_webhooks_for_event(
            db_session,
            test_business.id,
            "invoice.success"
        )
        
        assert len(webhooks) == 0
    
    def test_get_webhooks_for_event_filters_unsubscribed(self, db_session, test_business):
        """Test that webhooks not subscribed to event are not returned"""
        # Create webhook subscribed to different event
        webhook = Webhook(
            business_id=test_business.id,
            webhook_url="https://example.com/webhook",
            events=["refund.success"],
            secret="secret",
            is_active=True,
        )
        db_session.add(webhook)
        db_session.commit()
        
        webhooks = WebhookEventManager.get_webhooks_for_event(
            db_session,
            test_business.id,
            "invoice.success"
        )
        
        assert len(webhooks) == 0
    
    def test_get_webhooks_for_event_no_webhooks(self, db_session, test_business):
        """Test getting webhooks when none exist"""
        webhooks = WebhookEventManager.get_webhooks_for_event(
            db_session,
            test_business.id,
            "invoice.success"
        )
        
        assert len(webhooks) == 0


class TestWebhookEventTriggering:
    """Tests for triggering webhook events"""
    
    def test_trigger_webhook_event_success(self, db_session, test_business, test_submission, test_webhook):
        """Test triggering webhook event for successful submission"""
        with patch("app.services.webhook_delivery_tasks.WebhookDeliveryTaskManager") as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            triggered_count = WebhookEventManager.trigger_webhook_event(db_session, test_submission)
            
            assert triggered_count == 1
            mock_instance.queue_webhook_delivery.assert_called_once()
            
            # Verify call arguments
            call_args = mock_instance.queue_webhook_delivery.call_args
            assert call_args[1]["webhook_id"] == str(test_webhook.id)
            assert call_args[1]["event_type"] == "invoice.success"
            assert call_args[1]["submission_id"] == str(test_submission.id)
    
    def test_trigger_webhook_event_failed(self, db_session, test_business, test_webhook):
        """Test triggering webhook event for failed submission"""
        submission = Submission(
            business_id=test_business.id,
            submission_type="INVOICE",
            submission_status="FAILED",
            gra_response_code="B16",
            gra_response_message="Total amount mismatch",
            raw_request={"test": "data"},
            submitted_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)
        
        with patch("app.services.webhook_delivery_tasks.WebhookDeliveryTaskManager") as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            triggered_count = WebhookEventManager.trigger_webhook_event(db_session, submission)
            
            assert triggered_count == 1
            
            # Verify event type is invoice.failed
            call_args = mock_instance.queue_webhook_delivery.call_args
            assert call_args[1]["event_type"] == "invoice.failed"
    
    def test_trigger_webhook_event_no_webhooks(self, db_session, test_business, test_submission):
        """Test triggering webhook event when no webhooks exist"""
        triggered_count = WebhookEventManager.trigger_webhook_event(db_session, test_submission)
        
        assert triggered_count == 0
    
    def test_trigger_webhook_event_multiple_webhooks(self, db_session, test_business, test_submission):
        """Test triggering webhook event for multiple webhooks"""
        # Create multiple webhooks
        for i in range(3):
            webhook = Webhook(
                business_id=test_business.id,
                webhook_url=f"https://example.com/webhook{i}",
                events=["invoice.success"],
                secret=f"secret-{i}",
                is_active=True,
            )
            db_session.add(webhook)
        db_session.commit()
        
        with patch("app.services.webhook_delivery_tasks.WebhookDeliveryTaskManager") as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            triggered_count = WebhookEventManager.trigger_webhook_event(db_session, test_submission)
            
            assert triggered_count == 3
            assert mock_instance.queue_webhook_delivery.call_count == 3
    
    def test_trigger_webhook_event_unsupported_type(self, db_session, test_business):
        """Test triggering webhook event for unsupported submission type"""
        submission = Submission(
            business_id=test_business.id,
            submission_type="UNKNOWN",
            submission_status="SUCCESS",
            raw_request={"test": "data"},
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)
        
        triggered_count = WebhookEventManager.trigger_webhook_event(db_session, submission)
        
        # Should return 0 for unsupported types
        assert triggered_count == 0
    
    def test_trigger_webhook_event_pending_status(self, db_session, test_business, test_webhook):
        """Test that pending submissions don't trigger webhooks"""
        submission = Submission(
            business_id=test_business.id,
            submission_type="INVOICE",
            submission_status="PENDING_GRA",
            raw_request={"test": "data"},
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)
        
        triggered_count = WebhookEventManager.trigger_webhook_event(db_session, submission)
        
        # Should return 0 for pending status
        assert triggered_count == 0
    
    def test_trigger_webhook_event_refund_success(self, db_session, test_business):
        """Test triggering webhook event for successful refund"""
        webhook = Webhook(
            business_id=test_business.id,
            webhook_url="https://example.com/webhook",
            events=["refund.success"],
            secret="secret",
            is_active=True,
        )
        db_session.add(webhook)
        db_session.commit()
        
        submission = Submission(
            business_id=test_business.id,
            submission_type="REFUND",
            submission_status="SUCCESS",
            gra_invoice_id="GRA-REF-001",
            raw_request={"test": "data"},
            submitted_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)
        
        with patch("app.services.webhook_delivery_tasks.WebhookDeliveryTaskManager") as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            triggered_count = WebhookEventManager.trigger_webhook_event(db_session, submission)
            
            assert triggered_count == 1
            
            # Verify event type is refund.success
            call_args = mock_instance.queue_webhook_delivery.call_args
            assert call_args[1]["event_type"] == "refund.success"
    
    def test_trigger_webhook_event_purchase_failed(self, db_session, test_business):
        """Test triggering webhook event for failed purchase"""
        webhook = Webhook(
            business_id=test_business.id,
            webhook_url="https://example.com/webhook",
            events=["purchase.failed"],
            secret="secret",
            is_active=True,
        )
        db_session.add(webhook)
        db_session.commit()
        
        submission = Submission(
            business_id=test_business.id,
            submission_type="PURCHASE",
            submission_status="FAILED",
            gra_response_code="B16",
            raw_request={"test": "data"},
            submitted_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)
        
        with patch("app.services.webhook_delivery_tasks.WebhookDeliveryTaskManager") as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            triggered_count = WebhookEventManager.trigger_webhook_event(db_session, submission)
            
            assert triggered_count == 1
            
            # Verify event type is purchase.failed
            call_args = mock_instance.queue_webhook_delivery.call_args
            assert call_args[1]["event_type"] == "purchase.failed"


class TestWebhookEventIntegration:
    """Integration tests for webhook event triggering"""
    
    def test_webhook_event_payload_structure(self, db_session, test_business, test_submission, test_webhook):
        """Test that webhook payload has correct structure"""
        with patch("app.services.webhook_delivery_tasks.WebhookDeliveryTaskManager") as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            WebhookEventManager.trigger_webhook_event(db_session, test_submission)
            
            # Get the submission_data from the call
            call_args = mock_instance.queue_webhook_delivery.call_args
            submission_data = call_args[1]["submission_data"]
            
            # Verify structure
            assert "submission_id" in submission_data
            assert "submission_type" in submission_data
            assert "status" in submission_data
            assert "submitted_at" in submission_data
            assert "completed_at" in submission_data
    
    def test_webhook_event_with_gra_response(self, db_session, test_business, test_webhook):
        """Test webhook event includes GRA response details"""
        submission = Submission(
            business_id=test_business.id,
            submission_type="INVOICE",
            submission_status="SUCCESS",
            gra_invoice_id="GRA-INV-001",
            gra_qr_code="https://gra.gov.gh/qr/123",
            gra_receipt_num="VSDC-REC-001",
            gra_response_code=None,
            gra_response_message=None,
            raw_request={"test": "data"},
            submitted_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db_session.add(submission)
        db_session.commit()
        db_session.refresh(submission)
        
        with patch("app.services.webhook_delivery_tasks.WebhookDeliveryTaskManager") as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            WebhookEventManager.trigger_webhook_event(db_session, submission)
            
            # Get the submission_data from the call
            call_args = mock_instance.queue_webhook_delivery.call_args
            submission_data = call_args[1]["submission_data"]
            
            # Verify GRA response details are included
            assert submission_data["gra_invoice_id"] == "GRA-INV-001"
            assert submission_data["gra_qr_code"] == "https://gra.gov.gh/qr/123"
            assert submission_data["gra_receipt_num"] == "VSDC-REC-001"

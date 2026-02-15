"""Tests for webhook delivery service with retry logic"""
import pytest
import asyncio
import json
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.webhook_delivery import WebhookDeliveryService
from app.models.models import Webhook, WebhookDelivery, Submission
from app.utils.hmac_signature import HMACSignatureManager
from tests.conftest import create_test_business, create_test_api_key


@pytest.fixture
def test_business(db_session):
    """Create a test business"""
    return create_test_business(db_session)


@pytest.fixture
def test_webhook(db_session, test_business):
    """Create a test webhook"""
    webhook = Webhook(
        business_id=test_business.id,
        webhook_url="https://example.com/webhooks",
        events=["invoice.success", "invoice.failed"],
        secret="test-webhook-secret-12345",
        is_active=True,
    )
    db_session.add(webhook)
    db_session.commit()
    db_session.refresh(webhook)
    return webhook


@pytest.fixture
def test_submission(db_session, test_business):
    """Create a test submission"""
    submission = Submission(
        business_id=test_business.id,
        submission_type="INVOICE",
        submission_status="SUCCESS",
        gra_invoice_id="GRA-INV-001",
        raw_request={"test": "data"},
    )
    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)
    return submission


class TestWebhookPayloadCreation:
    """Tests for webhook payload creation"""
    
    def test_create_webhook_payload(self):
        """Test creating webhook payload"""
        submission_id = uuid4()
        submission_data = {
            "invoice_num": "INV-001",
            "status": "SUCCESS",
            "gra_invoice_id": "GRA-INV-001",
        }
        
        payload = WebhookDeliveryService.create_webhook_payload(
            event_type="invoice.success",
            submission_id=submission_id,
            submission_data=submission_data,
        )
        
        assert payload["event_type"] == "invoice.success"
        assert payload["submission_id"] == str(submission_id)
        assert payload["data"] == submission_data
        assert "timestamp" in payload
        assert payload["timestamp"].endswith("Z")
    
    def test_create_webhook_payload_with_different_events(self):
        """Test creating payloads for different event types"""
        submission_id = uuid4()
        submission_data = {"test": "data"}
        
        events = ["invoice.success", "invoice.failed", "refund.success"]
        
        for event in events:
            payload = WebhookDeliveryService.create_webhook_payload(
                event_type=event,
                submission_id=submission_id,
                submission_data=submission_data,
            )
            
            assert payload["event_type"] == event


class TestWebhookSignature:
    """Tests for webhook signature generation"""
    
    def test_generate_webhook_signature(self):
        """Test generating webhook signature"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id",
            "data": {"test": "data"},
        }
        webhook_secret = "test-secret"
        
        signature = WebhookDeliveryService.generate_webhook_signature(
            payload,
            webhook_secret,
        )
        
        assert isinstance(signature, str)
        assert len(signature) > 0
    
    def test_webhook_signature_consistency(self):
        """Test that same payload generates same signature"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id",
            "data": {"test": "data"},
        }
        webhook_secret = "test-secret"
        
        sig1 = WebhookDeliveryService.generate_webhook_signature(payload, webhook_secret)
        sig2 = WebhookDeliveryService.generate_webhook_signature(payload, webhook_secret)
        
        assert sig1 == sig2
    
    def test_webhook_signature_different_for_different_payloads(self):
        """Test that different payloads generate different signatures"""
        payload1 = {"event_type": "invoice.success", "data": {"test": "data1"}}
        payload2 = {"event_type": "invoice.success", "data": {"test": "data2"}}
        webhook_secret = "test-secret"
        
        sig1 = WebhookDeliveryService.generate_webhook_signature(payload1, webhook_secret)
        sig2 = WebhookDeliveryService.generate_webhook_signature(payload2, webhook_secret)
        
        assert sig1 != sig2


class TestRetryDelayCalculation:
    """Tests for retry delay calculation"""
    
    def test_calculate_next_retry_time_first_attempt(self):
        """Test retry time for first attempt (1 second)"""
        now = datetime.utcnow()
        next_retry = WebhookDeliveryService.calculate_next_retry_time(0)
        
        # Should be approximately 1 second in the future
        delay = (next_retry - now).total_seconds()
        assert 0.9 < delay < 1.1
    
    def test_calculate_next_retry_time_exponential_backoff(self):
        """Test exponential backoff for multiple retries"""
        expected_delays = [1, 2, 4, 8, 16]
        
        for attempt, expected_delay in enumerate(expected_delays):
            now = datetime.utcnow()
            next_retry = WebhookDeliveryService.calculate_next_retry_time(attempt)
            
            delay = (next_retry - now).total_seconds()
            assert expected_delay - 0.1 < delay < expected_delay + 0.1
    
    def test_calculate_next_retry_time_max_delay(self):
        """Test that max delay is used for retries beyond the list"""
        now = datetime.utcnow()
        next_retry = WebhookDeliveryService.calculate_next_retry_time(10)
        
        # Should use max delay (16 seconds)
        delay = (next_retry - now).total_seconds()
        assert 15.9 < delay < 16.1


class TestWebhookDelivery:
    """Tests for webhook delivery"""
    
    @pytest.mark.asyncio
    async def test_deliver_webhook_success(self, db_session, test_webhook, test_submission):
        """Test successful webhook delivery"""
        submission_data = {
            "invoice_num": "INV-001",
            "status": "SUCCESS",
        }
        
        with patch("app.services.webhook_delivery.WebhookDeliveryService._send_webhook") as mock_send:
            mock_send.return_value = (200, "OK")
            
            delivery = await WebhookDeliveryService.deliver_webhook(
                db=db_session,
                webhook=test_webhook,
                event_type="invoice.success",
                submission_id=test_submission.id,
                submission_data=submission_data,
            )
            
            assert delivery.delivery_status == "SUCCESS"
            assert delivery.response_code == 200
            assert delivery.retry_count == 0
            assert delivery.webhook_id == test_webhook.id
    
    @pytest.mark.asyncio
    async def test_deliver_webhook_retry_on_failure(self, db_session, test_webhook, test_submission):
        """Test webhook delivery retries on failure"""
        submission_data = {"invoice_num": "INV-001"}
        
        # Mock to fail first 2 times, then succeed
        with patch("app.services.webhook_delivery.WebhookDeliveryService._send_webhook") as mock_send:
            mock_send.side_effect = [
                (500, "Internal Server Error"),
                (500, "Internal Server Error"),
                (200, "OK"),
            ]
            
            with patch("asyncio.sleep", new_callable=AsyncMock):
                delivery = await WebhookDeliveryService.deliver_webhook(
                    db=db_session,
                    webhook=test_webhook,
                    event_type="invoice.success",
                    submission_id=test_submission.id,
                    submission_data=submission_data,
                )
            
            assert delivery.delivery_status == "SUCCESS"
            assert delivery.response_code == 200
            assert delivery.retry_count == 2
    
    @pytest.mark.asyncio
    async def test_deliver_webhook_max_retries_exceeded(self, db_session, test_webhook, test_submission):
        """Test webhook delivery fails after max retries"""
        submission_data = {"invoice_num": "INV-001"}
        
        # Mock to always fail
        with patch("app.services.webhook_delivery.WebhookDeliveryService._send_webhook") as mock_send:
            mock_send.return_value = (500, "Internal Server Error")
            
            with patch("asyncio.sleep", new_callable=AsyncMock):
                delivery = await WebhookDeliveryService.deliver_webhook(
                    db=db_session,
                    webhook=test_webhook,
                    event_type="invoice.success",
                    submission_id=test_submission.id,
                    submission_data=submission_data,
                )
            
            assert delivery.delivery_status == "FAILED"
            assert delivery.retry_count == 5
    
    @pytest.mark.asyncio
    async def test_deliver_webhook_timeout_retry(self, db_session, test_webhook, test_submission):
        """Test webhook delivery retries on timeout"""
        submission_data = {"invoice_num": "INV-001"}
        
        # Mock to timeout first time, then succeed
        with patch("app.services.webhook_delivery.WebhookDeliveryService._send_webhook") as mock_send:
            mock_send.side_effect = [
                asyncio.TimeoutError(),
                (200, "OK"),
            ]
            
            with patch("asyncio.sleep", new_callable=AsyncMock):
                delivery = await WebhookDeliveryService.deliver_webhook(
                    db=db_session,
                    webhook=test_webhook,
                    event_type="invoice.success",
                    submission_id=test_submission.id,
                    submission_data=submission_data,
                )
            
            assert delivery.delivery_status == "SUCCESS"
            assert delivery.retry_count == 1
    
    @pytest.mark.asyncio
    async def test_deliver_webhook_exception_retry(self, db_session, test_webhook, test_submission):
        """Test webhook delivery retries on exception"""
        submission_data = {"invoice_num": "INV-001"}
        
        # Mock to raise exception first time, then succeed
        with patch("app.services.webhook_delivery.WebhookDeliveryService._send_webhook") as mock_send:
            mock_send.side_effect = [
                Exception("Connection error"),
                (200, "OK"),
            ]
            
            with patch("asyncio.sleep", new_callable=AsyncMock):
                delivery = await WebhookDeliveryService.deliver_webhook(
                    db=db_session,
                    webhook=test_webhook,
                    event_type="invoice.success",
                    submission_id=test_submission.id,
                    submission_data=submission_data,
                )
            
            assert delivery.delivery_status == "SUCCESS"
            assert delivery.retry_count == 1


class TestPendingDeliveries:
    """Tests for pending delivery retrieval"""
    
    def test_get_pending_deliveries_empty(self, db_session):
        """Test getting pending deliveries when none exist"""
        deliveries = WebhookDeliveryService.get_pending_deliveries(db_session)
        
        assert len(deliveries) == 0
    
    def test_get_pending_deliveries_filters_successful(self, db_session, test_webhook, test_submission):
        """Test that successful deliveries are not returned"""
        # Create successful delivery
        delivery = WebhookDelivery(
            webhook_id=test_webhook.id,
            event_type="invoice.success",
            submission_id=test_submission.id,
            payload={"test": "data"},
            delivery_status="SUCCESS",
            retry_count=0,
        )
        db_session.add(delivery)
        db_session.commit()
        
        pending = WebhookDeliveryService.get_pending_deliveries(db_session)
        
        assert len(pending) == 0
    
    def test_get_pending_deliveries_returns_pending(self, db_session, test_webhook, test_submission):
        """Test that pending deliveries are returned"""
        # Create pending delivery
        delivery = WebhookDelivery(
            webhook_id=test_webhook.id,
            event_type="invoice.success",
            submission_id=test_submission.id,
            payload={"test": "data"},
            delivery_status="PENDING",
            retry_count=0,
        )
        db_session.add(delivery)
        db_session.commit()
        
        pending = WebhookDeliveryService.get_pending_deliveries(db_session)
        
        assert len(pending) == 1
        assert pending[0].id == delivery.id
    
    def test_get_pending_deliveries_respects_retry_time(self, db_session, test_webhook, test_submission):
        """Test that deliveries with future retry times are not returned"""
        # Create pending delivery with future retry time
        future_time = datetime.utcnow() + timedelta(hours=1)
        delivery = WebhookDelivery(
            webhook_id=test_webhook.id,
            event_type="invoice.success",
            submission_id=test_submission.id,
            payload={"test": "data"},
            delivery_status="PENDING",
            retry_count=1,
            next_retry_at=future_time,
        )
        db_session.add(delivery)
        db_session.commit()
        
        pending = WebhookDeliveryService.get_pending_deliveries(db_session)
        
        assert len(pending) == 0
    
    def test_get_pending_deliveries_returns_overdue(self, db_session, test_webhook, test_submission):
        """Test that overdue deliveries are returned"""
        # Create pending delivery with past retry time
        past_time = datetime.utcnow() - timedelta(minutes=5)
        delivery = WebhookDelivery(
            webhook_id=test_webhook.id,
            event_type="invoice.success",
            submission_id=test_submission.id,
            payload={"test": "data"},
            delivery_status="PENDING",
            retry_count=1,
            next_retry_at=past_time,
        )
        db_session.add(delivery)
        db_session.commit()
        
        pending = WebhookDeliveryService.get_pending_deliveries(db_session)
        
        assert len(pending) == 1
        assert pending[0].id == delivery.id
    
    def test_get_pending_deliveries_respects_limit(self, db_session, test_webhook, test_submission):
        """Test that limit is respected"""
        # Create multiple pending deliveries
        for i in range(10):
            delivery = WebhookDelivery(
                webhook_id=test_webhook.id,
                event_type="invoice.success",
                submission_id=test_submission.id,
                payload={"test": f"data{i}"},
                delivery_status="PENDING",
                retry_count=0,
            )
            db_session.add(delivery)
        db_session.commit()
        
        pending = WebhookDeliveryService.get_pending_deliveries(db_session, limit=5)
        
        assert len(pending) == 5


class TestRetryPendingDeliveries:
    """Tests for retrying pending deliveries"""
    
    @pytest.mark.asyncio
    async def test_retry_pending_deliveries_success(self, db_session, test_webhook, test_submission):
        """Test retrying pending deliveries"""
        # Create pending delivery
        delivery = WebhookDelivery(
            webhook_id=test_webhook.id,
            event_type="invoice.success",
            submission_id=test_submission.id,
            payload={"test": "data"},
            delivery_status="PENDING",
            retry_count=1,
        )
        db_session.add(delivery)
        db_session.commit()
        
        with patch("app.services.webhook_delivery.WebhookDeliveryService._send_webhook") as mock_send:
            mock_send.return_value = (200, "OK")
            
            retried = await WebhookDeliveryService.retry_pending_deliveries(db_session)
            
            assert retried == 1
            
            # Verify delivery was updated
            db_session.refresh(delivery)
            assert delivery.delivery_status == "SUCCESS"
    
    @pytest.mark.asyncio
    async def test_retry_pending_deliveries_multiple(self, db_session, test_webhook, test_submission):
        """Test retrying multiple pending deliveries"""
        # Create multiple pending deliveries
        for i in range(3):
            delivery = WebhookDelivery(
                webhook_id=test_webhook.id,
                event_type="invoice.success",
                submission_id=test_submission.id,
                payload={"test": f"data{i}"},
                delivery_status="PENDING",
                retry_count=1,
            )
            db_session.add(delivery)
        db_session.commit()
        
        with patch("app.services.webhook_delivery.WebhookDeliveryService._send_webhook") as mock_send:
            mock_send.return_value = (200, "OK")
            
            retried = await WebhookDeliveryService.retry_pending_deliveries(db_session)
            
            assert retried == 3
    
    @pytest.mark.asyncio
    async def test_retry_pending_deliveries_webhook_not_found(self, db_session, test_submission):
        """Test retrying delivery when webhook is deleted"""
        # Create delivery with non-existent webhook
        delivery = WebhookDelivery(
            webhook_id=uuid4(),
            event_type="invoice.success",
            submission_id=test_submission.id,
            payload={"test": "data"},
            delivery_status="PENDING",
            retry_count=1,
        )
        db_session.add(delivery)
        db_session.commit()
        
        retried = await WebhookDeliveryService.retry_pending_deliveries(db_session)
        
        assert retried == 0
        
        # Verify delivery was marked as failed
        db_session.refresh(delivery)
        assert delivery.delivery_status == "FAILED"


class TestWebhookDeliveryIntegration:
    """Integration tests for webhook delivery"""
    
    @pytest.mark.asyncio
    async def test_webhook_delivery_full_flow(self, db_session, test_webhook, test_submission):
        """Test full webhook delivery flow"""
        submission_data = {
            "invoice_num": "INV-001",
            "status": "SUCCESS",
            "gra_invoice_id": "GRA-INV-001",
        }
        
        with patch("app.services.webhook_delivery.WebhookDeliveryService._send_webhook") as mock_send:
            mock_send.return_value = (200, "OK")
            
            # Deliver webhook
            delivery = await WebhookDeliveryService.deliver_webhook(
                db=db_session,
                webhook=test_webhook,
                event_type="invoice.success",
                submission_id=test_submission.id,
                submission_data=submission_data,
            )
            
            assert delivery.delivery_status == "SUCCESS"
            assert delivery.response_code == 200
            
            # Verify delivery record in database
            db_delivery = db_session.query(WebhookDelivery).filter(
                WebhookDelivery.id == delivery.id
            ).first()
            
            assert db_delivery is not None
            assert db_delivery.delivery_status == "SUCCESS"
            assert db_delivery.event_type == "invoice.success"
            assert db_delivery.submission_id == test_submission.id

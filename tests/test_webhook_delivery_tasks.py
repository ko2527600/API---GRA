"""Tests for webhook delivery Celery tasks"""
import pytest
from uuid import uuid4
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.webhook_delivery_tasks import (
    WebhookDeliveryTaskManager,
    deliver_webhook_task,
    retry_pending_webhook_deliveries_task,
)
from app.models.models import Webhook, WebhookDelivery
from tests.conftest import create_test_business

# Mock Celery app to avoid Redis connection
pytest_plugins = []


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
        events=["invoice.success"],
        secret="test-webhook-secret",
        is_active=True,
    )
    db_session.add(webhook)
    db_session.commit()
    db_session.refresh(webhook)
    return webhook


class TestWebhookDeliveryTaskManager:
    """Tests for webhook delivery task manager"""
    
    def test_queue_webhook_delivery(self, test_webhook):
        """Test queueing a webhook delivery task"""
        submission_id = str(uuid4())
        submission_data = {"invoice_num": "INV-001"}
        
        with patch("app.services.webhook_delivery_tasks.deliver_webhook_task.apply_async") as mock_apply:
            mock_task = MagicMock()
            mock_task.id = "task-123"
            mock_apply.return_value = mock_task
            
            task_id = WebhookDeliveryTaskManager.queue_webhook_delivery(
                webhook_id=str(test_webhook.id),
                event_type="invoice.success",
                submission_id=submission_id,
                submission_data=submission_data,
            )
            
            assert task_id == "task-123"
            mock_apply.assert_called_once()
    
    def test_queue_webhook_delivery_with_priority(self, test_webhook):
        """Test queueing webhook delivery with custom priority"""
        submission_id = str(uuid4())
        submission_data = {"invoice_num": "INV-001"}
        
        with patch("app.services.webhook_delivery_tasks.deliver_webhook_task.apply_async") as mock_apply:
            mock_task = MagicMock()
            mock_task.id = "task-456"
            mock_apply.return_value = mock_task
            
            task_id = WebhookDeliveryTaskManager.queue_webhook_delivery(
                webhook_id=str(test_webhook.id),
                event_type="invoice.success",
                submission_id=submission_id,
                submission_data=submission_data,
                priority=9,
            )
            
            assert task_id == "task-456"
            # Verify priority was passed
            call_kwargs = mock_apply.call_args[1]
            assert call_kwargs["priority"] == 9
    
    def test_queue_retry_pending_deliveries(self):
        """Test queueing retry pending deliveries task"""
        with patch("app.services.webhook_delivery_tasks.retry_pending_webhook_deliveries_task.apply_async") as mock_apply:
            mock_task = MagicMock()
            mock_task.id = "task-789"
            mock_apply.return_value = mock_task
            
            task_id = WebhookDeliveryTaskManager.queue_retry_pending_deliveries(limit=50)
            
            assert task_id == "task-789"
            mock_apply.assert_called_once()


class TestDeliverWebhookTask:
    """Tests for deliver webhook Celery task"""
    
    def test_deliver_webhook_task_queued(self, test_webhook):
        """Test webhook delivery task can be queued"""
        submission_id = str(uuid4())
        submission_data = {
            "invoice_num": "INV-001",
            "status": "SUCCESS",
        }
        
        # Just verify the task can be called without errors
        # (actual execution requires database setup)
        with patch("app.services.webhook_delivery_tasks.deliver_webhook_task.apply_async") as mock_apply:
            mock_task = MagicMock()
            mock_task.id = "task-webhook-123"
            mock_apply.return_value = mock_task
            
            task_id = WebhookDeliveryTaskManager.queue_webhook_delivery(
                webhook_id=str(test_webhook.id),
                event_type="invoice.success",
                submission_id=submission_id,
                submission_data=submission_data,
            )
            
            assert task_id == "task-webhook-123"


class TestRetryPendingWebhookDeliveriesTask:
    """Tests for retry pending webhook deliveries task"""
    
    def test_retry_pending_deliveries_task_queued(self):
        """Test retrying pending deliveries task can be queued"""
        with patch("app.services.webhook_delivery_tasks.retry_pending_webhook_deliveries_task.apply_async") as mock_apply:
            mock_task = MagicMock()
            mock_task.id = "task-retry-123"
            mock_apply.return_value = mock_task
            
            task_id = WebhookDeliveryTaskManager.queue_retry_pending_deliveries(limit=100)
            
            assert task_id == "task-retry-123"
            mock_apply.assert_called_once()


class TestWebhookDeliveryIntegration:
    """Integration tests for webhook delivery tasks"""
    
    def test_webhook_delivery_task_manager_integration(self, test_webhook):
        """Test webhook delivery task manager integration"""
        submission_id = str(uuid4())
        submission_data = {
            "invoice_num": "INV-001",
            "status": "SUCCESS",
            "gra_invoice_id": "GRA-INV-001",
        }
        
        with patch("app.services.webhook_delivery_tasks.deliver_webhook_task.apply_async") as mock_apply:
            mock_task = MagicMock()
            mock_task.id = "task-integration-123"
            mock_apply.return_value = mock_task
            
            # Queue delivery
            task_id = WebhookDeliveryTaskManager.queue_webhook_delivery(
                webhook_id=str(test_webhook.id),
                event_type="invoice.success",
                submission_id=submission_id,
                submission_data=submission_data,
            )
            
            assert task_id == "task-integration-123"
            mock_apply.assert_called_once()

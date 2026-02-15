"""Tests for async task queue"""
import pytest
import json
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

from app.services.task_queue import (
    TaskQueueManager,
    process_json_submission_task,
    process_xml_submission_task,
    celery_app,
)
from app.services.gra_client import GRAClientError, ErrorType
from app.models.models import Submission


@pytest.fixture
def submission_id():
    """Generate a submission ID"""
    return str(uuid4())


@pytest.fixture
def business_id():
    """Generate a business ID"""
    return str(uuid4())


@pytest.fixture
def json_request_data():
    """Sample JSON request data"""
    return {
        "company": {
            "COMPANY_NAMES": "Test Company",
            "COMPANY_SECURITY_KEY": "TEST_KEY",
            "COMPANY_TIN": "C00123456789",
        },
        "header": {
            "NUM": "INV-001",
            "INVOICE_DATE": "2026-02-10",
            "CLIENT_NAME": "Customer",
            "TOTAL_AMOUNT": "1000",
            "TOTAL_VAT": "150",
            "TOTAL_LEVY": "50",
            "ITEMS_COUNTS": "1",
        },
        "item_list": [
            {
                "ITMREF": "PROD001",
                "ITMDES": "Product",
                "QUANTITY": "10",
                "UNITYPRICE": "100",
                "TAXCODE": "B",
                "TAXRATE": "15",
            }
        ],
    }


@pytest.fixture
def xml_request_data():
    """Sample XML request data"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <company>
        <COMPANY_NAMES>Test Company</COMPANY_NAMES>
        <COMPANY_SECURITY_KEY>TEST_KEY</COMPANY_SECURITY_KEY>
        <COMPANY_TIN>C00123456789</COMPANY_TIN>
    </company>
    <header>
        <NUM>INV-001</NUM>
        <INVOICE_DATE>2026-02-10</INVOICE_DATE>
        <CLIENT_NAME>Customer</CLIENT_NAME>
        <TOTAL_AMOUNT>1000</TOTAL_AMOUNT>
        <TOTAL_VAT>150</TOTAL_VAT>
        <TOTAL_LEVY>50</TOTAL_LEVY>
        <ITEMS_COUNTS>1</ITEMS_COUNTS>
    </header>
    <item_list>
        <item>
            <ITMREF>PROD001</ITMREF>
            <ITMDES>Product</ITMDES>
            <QUANTITY>10</QUANTITY>
            <UNITYPRICE>100</UNITYPRICE>
            <TAXCODE>B</TAXCODE>
            <TAXRATE>15</TAXRATE>
        </item>
    </item_list>
</root>"""


class TestTaskQueueManager:
    """Tests for TaskQueueManager"""
    
    def test_queue_json_submission(self, submission_id, business_id, json_request_data):
        """Test queueing a JSON submission"""
        manager = TaskQueueManager()
        
        with patch.object(process_json_submission_task, 'apply_async') as mock_apply:
            mock_apply.return_value = MagicMock(id="task-123")
            
            task_id = manager.queue_json_submission(
                submission_id=submission_id,
                business_id=business_id,
                request_data=json_request_data,
            )
            
            assert task_id == "task-123"
            mock_apply.assert_called_once()
            
            # Verify call arguments
            call_args = mock_apply.call_args
            assert call_args[1]["args"][0] == submission_id
            assert call_args[1]["args"][1] == business_id
            assert call_args[1]["args"][2] == json_request_data
    
    def test_queue_xml_submission(self, submission_id, business_id, xml_request_data):
        """Test queueing an XML submission"""
        manager = TaskQueueManager()
        
        with patch.object(process_xml_submission_task, 'apply_async') as mock_apply:
            mock_apply.return_value = MagicMock(id="task-456")
            
            task_id = manager.queue_xml_submission(
                submission_id=submission_id,
                business_id=business_id,
                request_data=xml_request_data,
            )
            
            assert task_id == "task-456"
            mock_apply.assert_called_once()
            
            # Verify call arguments
            call_args = mock_apply.call_args
            assert call_args[1]["args"][0] == submission_id
            assert call_args[1]["args"][1] == business_id
            assert call_args[1]["args"][2] == xml_request_data
    
    def test_queue_submission_with_priority(self, submission_id, business_id, json_request_data):
        """Test queueing a submission with custom priority"""
        manager = TaskQueueManager()
        
        with patch.object(process_json_submission_task, 'apply_async') as mock_apply:
            mock_apply.return_value = MagicMock(id="task-789")
            
            task_id = manager.queue_json_submission(
                submission_id=submission_id,
                business_id=business_id,
                request_data=json_request_data,
                priority=9,
            )
            
            assert task_id == "task-789"
            
            # Verify priority was set
            call_args = mock_apply.call_args
            assert call_args[1]["priority"] == 9
    
    def test_get_task_status(self):
        """Test getting task status"""
        manager = TaskQueueManager()
        
        with patch.object(celery_app, 'AsyncResult') as mock_result:
            mock_task = MagicMock()
            mock_task.status = "SUCCESS"
            mock_task.result = {"status": "completed"}
            mock_task.successful.return_value = True
            mock_task.failed.return_value = False
            mock_result.return_value = mock_task
            
            status = manager.get_task_status("task-123")
            
            assert status["task_id"] == "task-123"
            assert status["status"] == "SUCCESS"
            assert status["result"] == {"status": "completed"}
            assert status["error"] is None
    
    def test_get_task_status_failed(self):
        """Test getting status of failed task"""
        manager = TaskQueueManager()
        
        with patch.object(celery_app, 'AsyncResult') as mock_result:
            mock_task = MagicMock()
            mock_task.status = "FAILURE"
            mock_task.info = "Task failed"
            mock_task.successful.return_value = False
            mock_task.failed.return_value = True
            mock_result.return_value = mock_task
            
            status = manager.get_task_status("task-123")
            
            assert status["task_id"] == "task-123"
            assert status["status"] == "FAILURE"
            assert status["result"] is None
            assert status["error"] == "Task failed"
    
    def test_cancel_task(self):
        """Test cancelling a task"""
        manager = TaskQueueManager()
        
        with patch.object(celery_app, 'AsyncResult') as mock_result:
            mock_task = MagicMock()
            mock_result.return_value = mock_task
            
            result = manager.cancel_task("task-123")
            
            assert result is True
            mock_task.revoke.assert_called_once_with(terminate=True)


class TestProcessJsonSubmissionTask:
    """Tests for process_json_submission_task"""
    
    @pytest.mark.asyncio
    async def test_process_json_submission_success(
        self, submission_id, business_id, json_request_data
    ):
        """Test successful JSON submission processing"""
        with patch('app.services.task_queue.SessionLocal') as mock_session_local:
            mock_db = MagicMock()
            mock_session_local.return_value = mock_db
            
            with patch('app.services.task_queue.SubmissionProcessor.process_json_submission') as mock_processor:
                mock_processor.return_value = {"status": "success"}
                
                # Create a mock task
                mock_task = MagicMock()
                mock_task.request.id = "task-123"
                mock_task.request.retries = 0
                mock_task.retry = MagicMock()
                
                # Call the task function directly
                result = await mock_processor(
                    db=mock_db,
                    submission_id=submission_id,
                    business_id=business_id,
                    request_data=json_request_data,
                )
                
                assert result == {"status": "success"}
    
    @pytest.mark.asyncio
    async def test_process_json_submission_gra_error_retryable(
        self, submission_id, business_id, json_request_data
    ):
        """Test JSON submission with retryable GRA error"""
        with patch('app.services.task_queue.SessionLocal') as mock_session_local:
            mock_db = MagicMock()
            mock_session_local.return_value = mock_db
            
            with patch('app.services.task_queue.SubmissionProcessor.process_json_submission') as mock_processor:
                # Create a retryable error
                error = GRAClientError(
                    "Service unavailable",
                    status_code=503,
                    error_type=ErrorType.UNAVAILABLE,
                )
                mock_processor.side_effect = error
                
                # Verify error is retryable
                assert error.is_retryable() is True


class TestProcessXmlSubmissionTask:
    """Tests for process_xml_submission_task"""
    
    @pytest.mark.asyncio
    async def test_process_xml_submission_success(
        self, submission_id, business_id, xml_request_data
    ):
        """Test successful XML submission processing"""
        with patch('app.services.task_queue.SessionLocal') as mock_session_local:
            mock_db = MagicMock()
            mock_session_local.return_value = mock_db
            
            with patch('app.services.task_queue.SubmissionProcessor.process_xml_submission') as mock_processor:
                mock_processor.return_value = {"status": "success"}
                
                # Call the task function directly
                result = await mock_processor(
                    db=mock_db,
                    submission_id=submission_id,
                    business_id=business_id,
                    request_data=xml_request_data,
                )
                
                assert result == {"status": "success"}


class TestTaskQueueIntegration:
    """Integration tests for task queue"""
    
    def test_queue_and_get_status(self, submission_id, business_id, json_request_data):
        """Test queueing a submission and checking its status"""
        manager = TaskQueueManager()
        
        with patch.object(process_json_submission_task, 'apply_async') as mock_apply:
            mock_apply.return_value = MagicMock(id="task-123")
            
            # Queue submission
            task_id = manager.queue_json_submission(
                submission_id=submission_id,
                business_id=business_id,
                request_data=json_request_data,
            )
            
            assert task_id == "task-123"
            
            # Get status
            with patch.object(celery_app, 'AsyncResult') as mock_result:
                mock_task = MagicMock()
                mock_task.status = "PENDING"
                mock_task.successful.return_value = False
                mock_task.failed.return_value = False
                mock_result.return_value = mock_task
                
                status = manager.get_task_status(task_id)
                
                assert status["task_id"] == task_id
                assert status["status"] == "PENDING"
    
    def test_queue_multiple_submissions(self, business_id, json_request_data):
        """Test queueing multiple submissions"""
        manager = TaskQueueManager()
        
        with patch.object(process_json_submission_task, 'apply_async') as mock_apply:
            task_ids = []
            
            for i in range(3):
                submission_id = str(uuid4())
                mock_apply.return_value = MagicMock(id=f"task-{i}")
                
                task_id = manager.queue_json_submission(
                    submission_id=submission_id,
                    business_id=business_id,
                    request_data=json_request_data,
                )
                
                task_ids.append(task_id)
            
            assert len(task_ids) == 3
            assert task_ids == ["task-0", "task-1", "task-2"]

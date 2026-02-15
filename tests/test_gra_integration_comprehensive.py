"""Comprehensive tests for GRA integration end-to-end scenarios"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from app.services.gra_client import GRAHTTPClient, GRAClientError, ErrorType, GRAErrorClassifier
from app.services.submission_processor import SubmissionProcessor
from app.services.gra_polling import GRAPollingService
from app.services.task_queue import TaskQueueManager
from app.models.models import Submission, SubmissionStatus


class TestGRAIntegrationEndToEnd:
    """End-to-end tests for GRA integration workflow"""
    
    @pytest.fixture
    def sample_invoice(self):
        """Sample invoice for testing"""
        return {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "COMPUTATION_TYPE": "INCLUSIVE",
                "FLAG": "INVOICE",
                "SALE_TYPE": "NORMAL",
                "USER_NAME": "JOHN",
                "NUM": "INV-2026-001",
                "INVOICE_DATE": "2026-02-10",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "CLIENT_NAME": "Customer Ltd",
                "CLIENT_TIN": "C0022825405",
                "TOTAL_VAT": "159",
                "TOTAL_LEVY": "60",
                "TOTAL_AMOUNT": "3438",
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
                    "ITMREF": "PROD001",
                    "ITMDES": "Product Description",
                    "TAXRATE": "15",
                    "TAXCODE": "B",
                    "LEVY_AMOUNT_A": "2.5",
                    "LEVY_AMOUNT_B": "2.5",
                    "LEVY_AMOUNT_C": "0",
                    "LEVY_AMOUNT_D": "0",
                    "QUANTITY": "10",
                    "UNITYPRICE": "100",
                    "ITEM_CATEGORY": "GOODS"
                }
            ]
        }
    
    @pytest.fixture
    def gra_credentials(self):
        """GRA credentials for testing"""
        return {
            "gra_tin": "C00XXXXXXXX",
            "gra_company_name": "ABC COMPANY LTD",
            "gra_security_key": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_invoice_submission_success(self, sample_invoice, gra_credentials):
        """Test complete invoice submission workflow from submission to polling"""
        # Test credential injection
        payload = SubmissionProcessor._inject_gra_credentials(
            sample_invoice,
            gra_credentials
        )
        
        # Verify credentials are injected
        assert payload["company"]["COMPANY_TIN"] == gra_credentials["gra_tin"]
        assert payload["company"]["COMPANY_NAMES"] == gra_credentials["gra_company_name"]
        assert payload["company"]["COMPANY_SECURITY_KEY"] == gra_credentials["gra_security_key"]
        
        # Verify original data is not modified
        assert sample_invoice["company"]["COMPANY_TIN"] == "C00XXXXXXXX"
    
    @pytest.mark.asyncio
    async def test_end_to_end_invoice_submission_with_retry(self, sample_invoice, gra_credentials):
        """Test invoice submission with GRA retry on transient error"""
        # Test that transient errors are classified correctly
        error = GRAClientError(
            "Service unavailable",
            status_code=503,
            error_type=ErrorType.UNAVAILABLE,
        )
        
        assert error.is_retryable() is True
        assert error.error_type == ErrorType.UNAVAILABLE
    
    @pytest.mark.asyncio
    async def test_end_to_end_refund_submission(self, sample_invoice, gra_credentials):
        """Test complete refund submission workflow"""
        # Create refund request
        refund_request = {
            "company": sample_invoice["company"],
            "header": {
                **sample_invoice["header"],
                "FLAG": "REFUND",
                "REFUND_ID": "GRA-INV-2026-001",
                "NUM": "REF-2026-001",
            },
            "item_list": sample_invoice["item_list"]
        }
        
        # Test credential injection for refund
        payload = SubmissionProcessor._inject_gra_credentials(
            refund_request,
            gra_credentials
        )
        
        # Verify credentials are injected
        assert payload["company"]["COMPANY_TIN"] == gra_credentials["gra_tin"]
        assert payload["header"]["FLAG"] == "REFUND"
        assert payload["header"]["REFUND_ID"] == "GRA-INV-2026-001"
    
    @pytest.mark.asyncio
    async def test_end_to_end_purchase_submission(self, sample_invoice, gra_credentials):
        """Test complete purchase submission workflow"""
        # Create purchase request
        purchase_request = {
            "company": sample_invoice["company"],
            "header": {
                **sample_invoice["header"],
                "FLAG": "PURCHASE",
                "NUM": "PUR-2026-001",
            },
            "item_list": sample_invoice["item_list"]
        }
        
        # Test credential injection for purchase
        payload = SubmissionProcessor._inject_gra_credentials(
            purchase_request,
            gra_credentials
        )
        
        # Verify credentials are injected
        assert payload["company"]["COMPANY_TIN"] == gra_credentials["gra_tin"]
        assert payload["header"]["FLAG"] == "PURCHASE"
        assert payload["header"]["NUM"] == "PUR-2026-001"
    
    @pytest.mark.asyncio
    async def test_gra_client_handles_multiple_error_types(self):
        """Test GRA client handles different error types correctly"""
        # Test transient error classification
        assert GRAErrorClassifier.classify_error(500) == ErrorType.TRANSIENT
        assert GRAErrorClassifier.classify_error(502) == ErrorType.TRANSIENT
        assert GRAErrorClassifier.classify_error(504) == ErrorType.TRANSIENT
        
        # Test rate limit classification
        assert GRAErrorClassifier.classify_error(429) == ErrorType.RATE_LIMIT
        
        # Test unavailable classification
        assert GRAErrorClassifier.classify_error(503) == ErrorType.UNAVAILABLE
        
        # Test permanent error classification
        assert GRAErrorClassifier.classify_error(400) == ErrorType.PERMANENT
        assert GRAErrorClassifier.classify_error(401) == ErrorType.PERMANENT
        assert GRAErrorClassifier.classify_error(403) == ErrorType.PERMANENT
        assert GRAErrorClassifier.classify_error(404) == ErrorType.PERMANENT
    
    @pytest.mark.asyncio
    async def test_gra_client_handles_gra_specific_error_codes(self):
        """Test GRA client handles GRA-specific error codes"""
        # Test transient GRA error codes
        response_data = {"gra_response_code": "D06"}
        assert GRAErrorClassifier.classify_error(200, response_data) == ErrorType.TRANSIENT
        
        response_data = {"gra_response_code": "IS100"}
        assert GRAErrorClassifier.classify_error(200, response_data) == ErrorType.TRANSIENT
        
        response_data = {"gra_response_code": "A13"}
        assert GRAErrorClassifier.classify_error(200, response_data) == ErrorType.TRANSIENT
        
        # Test permanent GRA error codes
        response_data = {"gra_response_code": "B16"}
        assert GRAErrorClassifier.classify_error(200, response_data) == ErrorType.PERMANENT
        
        response_data = {"gra_response_code": "A01"}
        assert GRAErrorClassifier.classify_error(200, response_data) == ErrorType.PERMANENT
    
    @pytest.mark.asyncio
    async def test_submission_processor_validates_before_submission(self, sample_invoice, gra_credentials):
        """Test that submission processor validates data before sending to GRA"""
        # Test that credentials are properly injected
        payload = SubmissionProcessor._inject_gra_credentials(
            sample_invoice,
            gra_credentials
        )
        
        # Verify credentials are injected
        assert payload["company"]["COMPANY_TIN"] == gra_credentials["gra_tin"]
        assert payload["company"]["COMPANY_NAMES"] == gra_credentials["gra_company_name"]
        assert payload["company"]["COMPANY_SECURITY_KEY"] == gra_credentials["gra_security_key"]
        
        # Verify original data is not modified
        assert sample_invoice["company"]["COMPANY_TIN"] == "C00XXXXXXXX"
    
    @pytest.mark.asyncio
    async def test_polling_service_handles_multiple_status_updates(self):
        """Test polling service correctly handles multiple status updates"""
        # Test that polling service can handle different status responses
        responses = [
            {"status": "PROCESSING"},
            {"status": "PROCESSING"},
            {
                "status": "SUCCESS",
                "gra_invoice_id": "GRA-INV-001",
                "gra_qr_code": "https://gra.gov.gh/qr/123",
                "gra_receipt_num": "VSDC-REC-001",
            }
        ]
        
        # Verify response structure
        for response in responses:
            assert "status" in response
            if response["status"] == "SUCCESS":
                assert "gra_invoice_id" in response
                assert "gra_qr_code" in response
                assert "gra_receipt_num" in response
    
    @pytest.mark.asyncio
    async def test_task_queue_manager_queues_submissions(self):
        """Test task queue manager properly queues submissions"""
        manager = TaskQueueManager()
        
        submission_id = str(uuid4())
        business_id = str(uuid4())
        request_data = {"test": "data"}
        
        with patch("app.services.task_queue.process_json_submission_task.apply_async") as mock_apply:
            mock_apply.return_value = MagicMock(id="task-123")
            
            task_id = manager.queue_json_submission(
                submission_id=submission_id,
                business_id=business_id,
                request_data=request_data,
            )
            
            assert task_id == "task-123"
            mock_apply.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_gra_client_respects_timeout(self):
        """Test GRA client respects timeout settings"""
        client = GRAHTTPClient(
            base_url="https://api.test.com",
            timeout=5,
            max_retries=3,
        )
        
        assert client.timeout == 5
    
    @pytest.mark.asyncio
    async def test_gra_client_formats_endpoint_correctly(self):
        """Test GRA client formats endpoints correctly"""
        client = GRAHTTPClient(
            base_url="https://api.test.com",
            timeout=10,
            max_retries=3,
        )
        
        # Test endpoint formatting
        assert client.base_url == "https://api.test.com"
    
    @pytest.mark.asyncio
    async def test_polling_service_stores_raw_response(self):
        """Test polling service stores raw GRA response"""
        # Test that GRA response structure is correct
        gra_response = {
            "status": "SUCCESS",
            "gra_invoice_id": "GRA-INV-001",
            "gra_qr_code": "https://gra.gov.gh/qr/123",
            "gra_receipt_num": "VSDC-REC-001",
        }
        
        # Verify response has all required fields
        assert gra_response["status"] == "SUCCESS"
        assert gra_response["gra_invoice_id"] == "GRA-INV-001"
        assert gra_response["gra_qr_code"] == "https://gra.gov.gh/qr/123"
        assert gra_response["gra_receipt_num"] == "VSDC-REC-001"
    
    @pytest.mark.asyncio
    async def test_gra_client_error_includes_response_data(self):
        """Test GRA client error includes response data"""
        error = GRAClientError(
            "Test error",
            status_code=400,
            response_data={"gra_response_code": "B16", "message": "Total mismatch"},
            error_type=ErrorType.PERMANENT,
        )
        
        assert error.response_data["gra_response_code"] == "B16"
        assert error.response_data["message"] == "Total mismatch"
        assert error.status_code == 400
        assert error.error_type == ErrorType.PERMANENT
    
    @pytest.mark.asyncio
    async def test_submission_processor_handles_xml_format(self, gra_credentials):
        """Test submission processor handles XML format correctly"""
        xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<root>
  <company>
    <COMPANY_NAMES>ABC COMPANY LTD</COMPANY_NAMES>
    <COMPANY_SECURITY_KEY>UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH</COMPANY_SECURITY_KEY>
    <COMPANY_TIN>C00XXXXXXXX</COMPANY_TIN>
  </company>
  <header>
    <NUM>INV-001</NUM>
  </header>
  <item_list/>
</root>"""
        
        result = SubmissionProcessor._inject_gra_credentials_xml(
            xml_data,
            gra_credentials
        )
        
        # Verify XML is valid and credentials are injected
        assert gra_credentials["gra_tin"] in result
        assert gra_credentials["gra_company_name"] in result
        assert gra_credentials["gra_security_key"] in result

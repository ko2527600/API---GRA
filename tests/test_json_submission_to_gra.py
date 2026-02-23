"""Tests for JSON submission to GRA"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from app.services.submission_processor import SubmissionProcessor
from app.services.gra_client import GRAClientError, ErrorType


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing"""
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
def sample_gra_credentials():
    """Sample GRA credentials"""
    return {
        "gra_tin": "C00XXXXXXXX",
        "gra_company_name": "ABC COMPANY LTD",
        "gra_security_key": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
    }


class TestSubmissionProcessor:
    """Tests for submission processor"""
    
    def test_inject_gra_credentials(self, sample_invoice_data, sample_gra_credentials):
        """Test GRA credentials injection into request"""
        payload = SubmissionProcessor._inject_gra_credentials(
            sample_invoice_data,
            sample_gra_credentials
        )
        
        # Verify credentials are injected
        assert payload["company"]["COMPANY_TIN"] == sample_gra_credentials["gra_tin"]
        assert payload["company"]["COMPANY_NAMES"] == sample_gra_credentials["gra_company_name"]
        assert payload["company"]["COMPANY_SECURITY_KEY"] == sample_gra_credentials["gra_security_key"]
        
        # Verify original data is not modified
        assert sample_invoice_data["company"]["COMPANY_TIN"] == "C00XXXXXXXX"
    
    def test_inject_gra_credentials_creates_company_section(self, sample_gra_credentials):
        """Test that company section is created if missing"""
        data = {
            "header": {"NUM": "INV-001"},
            "item_list": []
        }
        
        payload = SubmissionProcessor._inject_gra_credentials(
            data,
            sample_gra_credentials
        )
        
        # Verify company section was created
        assert "company" in payload
        assert payload["company"]["COMPANY_TIN"] == sample_gra_credentials["gra_tin"]
    
    def test_inject_gra_credentials_preserves_other_fields(self, sample_invoice_data, sample_gra_credentials):
        """Test that other fields are preserved during credential injection"""
        payload = SubmissionProcessor._inject_gra_credentials(
            sample_invoice_data,
            sample_gra_credentials
        )
        
        # Verify other fields are preserved
        assert payload["header"]["NUM"] == "INV-2026-001"
        assert payload["header"]["CLIENT_NAME"] == "Customer Ltd"
        assert len(payload["item_list"]) == 1
        assert payload["item_list"][0]["ITMREF"] == "PROD001"
    
    def test_inject_gra_credentials_overwrites_existing_credentials(self, sample_gra_credentials):
        """Test that existing credentials are overwritten"""
        data = {
            "company": {
                "COMPANY_TIN": "OLD_TIN",
                "COMPANY_NAMES": "OLD_NAME",
                "COMPANY_SECURITY_KEY": "OLD_KEY"
            },
            "header": {},
            "item_list": []
        }
        
        payload = SubmissionProcessor._inject_gra_credentials(
            data,
            sample_gra_credentials
        )
        
        # Verify credentials are overwritten
        assert payload["company"]["COMPANY_TIN"] == sample_gra_credentials["gra_tin"]
        assert payload["company"]["COMPANY_NAMES"] == sample_gra_credentials["gra_company_name"]
        assert payload["company"]["COMPANY_SECURITY_KEY"] == sample_gra_credentials["gra_security_key"]
    
    @pytest.mark.asyncio
    async def test_process_json_submission_calls_gra_client_with_correct_endpoint(self, sample_invoice_data, sample_gra_credentials):
        """Test that process_json_submission calls GRA client with correct endpoint"""
        business_id = uuid4()
        submission_id = str(uuid4())
        
        # Mock business service
        with patch("app.services.submission_processor.BusinessService") as mock_business_service:
            mock_business = MagicMock()
            mock_business.id = business_id
            mock_business_service.get_business_by_id.return_value = mock_business
            mock_business_service.get_decrypted_gra_credentials.return_value = sample_gra_credentials
            
            # Mock GRA client
            with patch("app.services.submission_processor.get_gra_client") as mock_get_client:
                mock_client = AsyncMock()
                mock_client.submit_json.return_value = {
                    "gra_invoice_id": "GRA-INV-2026-001"
                }
                mock_get_client.return_value = mock_client
                
                # Mock database session
                mock_db = MagicMock()
                mock_submission = MagicMock()
                mock_submission.id = submission_id
                mock_submission.submission_status = "RECEIVED"
                mock_db.query.return_value.filter.return_value.first.return_value = mock_submission
                
                # Process submission
                result = await SubmissionProcessor.process_json_submission(
                    mock_db,
                    submission_id,
                    business_id,
                    sample_invoice_data
                )
                
                # Verify GRA client was called with correct endpoint
                mock_client.submit_json.assert_called_once()
                call_args = mock_client.submit_json.call_args
                assert call_args[1]["endpoint"] == "/post_receipt_Json.jsp"
    
    @pytest.mark.asyncio
    async def test_process_json_submission_injects_credentials_in_payload(self, sample_invoice_data, sample_gra_credentials):
        """Test that process_json_submission injects credentials into payload"""
        business_id = uuid4()
        submission_id = str(uuid4())
        
        # Mock business service
        with patch("app.services.submission_processor.BusinessService") as mock_business_service:
            mock_business = MagicMock()
            mock_business.id = business_id
            mock_business_service.get_business_by_id.return_value = mock_business
            mock_business_service.get_decrypted_gra_credentials.return_value = sample_gra_credentials
            
            # Mock GRA client
            with patch("app.services.submission_processor.get_gra_client") as mock_get_client:
                mock_client = AsyncMock()
                mock_client.submit_json.return_value = {
                    "gra_invoice_id": "GRA-INV-2026-001"
                }
                mock_get_client.return_value = mock_client
                
                # Mock database session
                mock_db = MagicMock()
                mock_submission = MagicMock()
                mock_submission.id = submission_id
                mock_submission.submission_status = "RECEIVED"
                mock_db.query.return_value.filter.return_value.first.return_value = mock_submission
                
                # Process submission
                await SubmissionProcessor.process_json_submission(
                    mock_db,
                    submission_id,
                    business_id,
                    sample_invoice_data
                )
                
                # Verify payload has injected credentials
                call_args = mock_client.submit_json.call_args
                payload = call_args[1]["data"]
                assert payload["company"]["COMPANY_TIN"] == sample_gra_credentials["gra_tin"]
                assert payload["company"]["COMPANY_NAMES"] == sample_gra_credentials["gra_company_name"]
                assert payload["company"]["COMPANY_SECURITY_KEY"] == sample_gra_credentials["gra_security_key"]
    
    @pytest.mark.asyncio
    async def test_process_json_submission_returns_gra_response(self, sample_invoice_data, sample_gra_credentials):
        """Test that process_json_submission returns GRA response"""
        business_id = uuid4()
        submission_id = str(uuid4())
        
        expected_response = {
            "gra_invoice_id": "GRA-INV-2026-001",
            "gra_qr_code": "https://gra.gov.gh/qr/...",
            "gra_receipt_num": "VSDC-REC-12345"
        }
        
        # Mock business service
        with patch("app.services.submission_processor.BusinessService") as mock_business_service:
            mock_business = MagicMock()
            mock_business.id = business_id
            mock_business_service.get_business_by_id.return_value = mock_business
            mock_business_service.get_decrypted_gra_credentials.return_value = sample_gra_credentials
            
            # Mock GRA client
            with patch("app.services.submission_processor.get_gra_client") as mock_get_client:
                mock_client = AsyncMock()
                mock_client.submit_json.return_value = expected_response
                mock_get_client.return_value = mock_client
                
                # Mock database session
                mock_db = MagicMock()
                mock_submission = MagicMock()
                mock_submission.id = submission_id
                mock_submission.submission_status = "RECEIVED"
                mock_db.query.return_value.filter.return_value.first.return_value = mock_submission
                
                # Process submission
                result = await SubmissionProcessor.process_json_submission(
                    mock_db,
                    submission_id,
                    business_id,
                    sample_invoice_data
                )
                
                # Verify result matches expected response
                assert result == expected_response
    
    @pytest.mark.asyncio
    async def test_process_json_submission_handles_gra_error(self, sample_invoice_data, sample_gra_credentials):
        """Test that process_json_submission handles GRA errors"""
        business_id = uuid4()
        submission_id = str(uuid4())
        
        # Mock business service
        with patch("app.services.submission_processor.BusinessService") as mock_business_service:
            mock_business = MagicMock()
            mock_business.id = business_id
            mock_business_service.get_business_by_id.return_value = mock_business
            mock_business_service.get_decrypted_gra_credentials.return_value = sample_gra_credentials
            
            # Mock GRA client to raise error
            with patch("app.services.submission_processor.get_gra_client") as mock_get_client:
                mock_client = AsyncMock()
                mock_client.submit_json.side_effect = GRAClientError(
                    "Validation failed",
                    status_code=400,
                    response_data={
                        "gra_response_code": "B16",
                        "gra_response_message": "TOTAL AMOUNT MISMATCH"
                    },
                    error_type=ErrorType.PERMANENT
                )
                mock_get_client.return_value = mock_client
                
                # Mock database session
                mock_db = MagicMock()
                mock_submission = MagicMock()
                mock_submission.id = submission_id
                mock_submission.submission_status = "RECEIVED"
                mock_db.query.return_value.filter.return_value.first.return_value = mock_submission
                
                # Process submission - should raise error
                with pytest.raises(GRAClientError):
                    await SubmissionProcessor.process_json_submission(
                        mock_db,
                        submission_id,
                        business_id,
                        sample_invoice_data
                    )
    
    @pytest.mark.asyncio
    async def test_process_json_submission_business_not_found(self, sample_invoice_data):
        """Test JSON submission with non-existent business"""
        business_id = uuid4()
        submission_id = str(uuid4())
        
        # Mock business service to return None
        with patch("app.services.submission_processor.BusinessService") as mock_business_service:
            mock_business_service.get_business_by_id.return_value = None
            
            # Mock database session
            mock_db = MagicMock()
            
            # Process submission - should raise error
            with pytest.raises(ValueError, match="Business .* not found"):
                await SubmissionProcessor.process_json_submission(
                    mock_db,
                    submission_id,
                    business_id,
                    sample_invoice_data
                )

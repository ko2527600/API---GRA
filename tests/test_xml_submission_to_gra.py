"""Tests for XML submission to GRA"""
import pytest
import asyncio
import json
import xml.etree.ElementTree as ET
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from app.services.submission_processor import SubmissionProcessor
from app.services.gra_client import GRAClientError, ErrorType


@pytest.fixture
def sample_xml_invoice():
    """Sample XML invoice data for testing"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<root>
  <company>
    <COMPANY_NAMES>ABC COMPANY LTD</COMPANY_NAMES>
    <COMPANY_SECURITY_KEY>UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH</COMPANY_SECURITY_KEY>
    <COMPANY_TIN>C00XXXXXXXX</COMPANY_TIN>
  </company>
  <header>
    <COMPUTATION_TYPE>INCLUSIVE</COMPUTATION_TYPE>
    <FLAG>INVOICE</FLAG>
    <SALE_TYPE>NORMAL</SALE_TYPE>
    <USER_NAME>JOHN</USER_NAME>
    <NUM>INV-2026-001</NUM>
    <INVOICE_DATE>2026-02-10</INVOICE_DATE>
    <CURRENCY>GHS</CURRENCY>
    <EXCHANGE_RATE>1</EXCHANGE_RATE>
    <CLIENT_NAME>Customer Ltd</CLIENT_NAME>
    <CLIENT_TIN>C0022825405</CLIENT_TIN>
    <TOTAL_VAT>159</TOTAL_VAT>
    <TOTAL_LEVY>60</TOTAL_LEVY>
    <TOTAL_AMOUNT>3438</TOTAL_AMOUNT>
    <ITEMS_COUNTS>1</ITEMS_COUNTS>
  </header>
  <item_list>
    <item>
      <ITMREF>PROD001</ITMREF>
      <ITMDES>Product Description</ITMDES>
      <TAXRATE>15</TAXRATE>
      <TAXCODE>B</TAXCODE>
      <LEVY_AMOUNT_A>2.5</LEVY_AMOUNT_A>
      <LEVY_AMOUNT_B>2.5</LEVY_AMOUNT_B>
      <LEVY_AMOUNT_C>0</LEVY_AMOUNT_C>
      <LEVY_AMOUNT_D>0</LEVY_AMOUNT_D>
      <QUANTITY>10</QUANTITY>
      <UNITYPRICE>100</UNITYPRICE>
      <ITEM_CATEGORY>GOODS</ITEM_CATEGORY>
    </item>
  </item_list>
</root>"""


@pytest.fixture
def sample_gra_credentials():
    """Sample GRA credentials"""
    return {
        "gra_tin": "C00XXXXXXXX",
        "gra_company_name": "ABC COMPANY LTD",
        "gra_security_key": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
    }


class TestXMLSubmissionProcessor:
    """Tests for XML submission processor"""
    
    def test_inject_gra_credentials_xml_with_existing_company(self, sample_xml_invoice, sample_gra_credentials):
        """Test GRA credentials injection into XML with existing company section"""
        result = SubmissionProcessor._inject_gra_credentials_xml(
            sample_xml_invoice,
            sample_gra_credentials
        )
        
        # Parse result
        root = ET.fromstring(result)
        company = root.find("company")
        
        # Verify credentials are injected
        assert company.find("COMPANY_TIN").text == sample_gra_credentials["gra_tin"]
        assert company.find("COMPANY_NAMES").text == sample_gra_credentials["gra_company_name"]
        assert company.find("COMPANY_SECURITY_KEY").text == sample_gra_credentials["gra_security_key"]
    
    def test_inject_gra_credentials_xml_creates_company_section(self, sample_gra_credentials):
        """Test that company section is created if missing in XML"""
        xml_without_company = """<?xml version="1.0" encoding="UTF-8"?>
<root>
  <header>
    <NUM>INV-001</NUM>
  </header>
  <item_list/>
</root>"""
        
        result = SubmissionProcessor._inject_gra_credentials_xml(
            xml_without_company,
            sample_gra_credentials
        )
        
        # Parse result
        root = ET.fromstring(result)
        company = root.find("company")
        
        # Verify company section was created
        assert company is not None
        assert company.find("COMPANY_TIN").text == sample_gra_credentials["gra_tin"]
    
    def test_inject_gra_credentials_xml_preserves_other_elements(self, sample_xml_invoice, sample_gra_credentials):
        """Test that other XML elements are preserved during credential injection"""
        result = SubmissionProcessor._inject_gra_credentials_xml(
            sample_xml_invoice,
            sample_gra_credentials
        )
        
        # Parse result
        root = ET.fromstring(result)
        
        # Verify other elements are preserved
        assert root.find("header/NUM").text == "INV-2026-001"
        assert root.find("header/CLIENT_NAME").text == "Customer Ltd"
        assert len(root.find("item_list")) == 1
        assert root.find("item_list/item/ITMREF").text == "PROD001"
    
    def test_inject_gra_credentials_xml_overwrites_existing_credentials(self, sample_gra_credentials):
        """Test that existing credentials are overwritten in XML"""
        xml_with_old_creds = """<?xml version="1.0" encoding="UTF-8"?>
<root>
  <company>
    <COMPANY_TIN>OLD_TIN</COMPANY_TIN>
    <COMPANY_NAMES>OLD_NAME</COMPANY_NAMES>
    <COMPANY_SECURITY_KEY>OLD_KEY</COMPANY_SECURITY_KEY>
  </company>
  <header/>
  <item_list/>
</root>"""
        
        result = SubmissionProcessor._inject_gra_credentials_xml(
            xml_with_old_creds,
            sample_gra_credentials
        )
        
        # Parse result
        root = ET.fromstring(result)
        company = root.find("company")
        
        # Verify credentials are overwritten
        assert company.find("COMPANY_TIN").text == sample_gra_credentials["gra_tin"]
        assert company.find("COMPANY_NAMES").text == sample_gra_credentials["gra_company_name"]
        assert company.find("COMPANY_SECURITY_KEY").text == sample_gra_credentials["gra_security_key"]
    
    def test_inject_gra_credentials_xml_invalid_xml(self, sample_gra_credentials):
        """Test that invalid XML raises ValueError"""
        invalid_xml = "<root><unclosed>"
        
        with pytest.raises(ValueError, match="Invalid XML"):
            SubmissionProcessor._inject_gra_credentials_xml(
                invalid_xml,
                sample_gra_credentials
            )
    
    @pytest.mark.asyncio
    async def test_process_xml_submission_calls_gra_client_with_correct_endpoint(self, sample_xml_invoice, sample_gra_credentials):
        """Test that process_xml_submission calls GRA client with correct endpoint"""
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
                mock_client.submit_xml.return_value = {
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
                result = await SubmissionProcessor.process_xml_submission(
                    mock_db,
                    submission_id,
                    business_id,
                    sample_xml_invoice
                )
                
                # Verify GRA client was called with correct endpoint
                mock_client.submit_xml.assert_called_once()
                call_args = mock_client.submit_xml.call_args
                assert call_args[1]["endpoint"] == "/api/v1/invoices/submit"
    
    @pytest.mark.asyncio
    async def test_process_xml_submission_injects_credentials_in_payload(self, sample_xml_invoice, sample_gra_credentials):
        """Test that process_xml_submission injects credentials into XML payload"""
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
                mock_client.submit_xml.return_value = {
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
                await SubmissionProcessor.process_xml_submission(
                    mock_db,
                    submission_id,
                    business_id,
                    sample_xml_invoice
                )
                
                # Verify payload has injected credentials
                call_args = mock_client.submit_xml.call_args
                payload = call_args[1]["data"]
                
                # Parse XML and verify credentials
                root = ET.fromstring(payload)
                company = root.find("company")
                assert company.find("COMPANY_TIN").text == sample_gra_credentials["gra_tin"]
                assert company.find("COMPANY_NAMES").text == sample_gra_credentials["gra_company_name"]
                assert company.find("COMPANY_SECURITY_KEY").text == sample_gra_credentials["gra_security_key"]
    
    @pytest.mark.asyncio
    async def test_process_xml_submission_returns_gra_response(self, sample_xml_invoice, sample_gra_credentials):
        """Test that process_xml_submission returns GRA response"""
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
                mock_client.submit_xml.return_value = expected_response
                mock_get_client.return_value = mock_client
                
                # Mock database session
                mock_db = MagicMock()
                mock_submission = MagicMock()
                mock_submission.id = submission_id
                mock_submission.submission_status = "RECEIVED"
                mock_db.query.return_value.filter.return_value.first.return_value = mock_submission
                
                # Process submission
                result = await SubmissionProcessor.process_xml_submission(
                    mock_db,
                    submission_id,
                    business_id,
                    sample_xml_invoice
                )
                
                # Verify result matches expected response
                assert result == expected_response
    
    @pytest.mark.asyncio
    async def test_process_xml_submission_handles_gra_error(self, sample_xml_invoice, sample_gra_credentials):
        """Test that process_xml_submission handles GRA errors"""
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
                mock_client.submit_xml.side_effect = GRAClientError(
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
                    await SubmissionProcessor.process_xml_submission(
                        mock_db,
                        submission_id,
                        business_id,
                        sample_xml_invoice
                    )
    
    @pytest.mark.asyncio
    async def test_process_xml_submission_business_not_found(self, sample_xml_invoice):
        """Test XML submission with non-existent business"""
        business_id = uuid4()
        submission_id = str(uuid4())
        
        # Mock business service to return None
        with patch("app.services.submission_processor.BusinessService") as mock_business_service:
            mock_business_service.get_business_by_id.return_value = None
            
            # Mock database session
            mock_db = MagicMock()
            
            # Process submission - should raise error
            with pytest.raises(ValueError, match="Business .* not found"):
                await SubmissionProcessor.process_xml_submission(
                    mock_db,
                    submission_id,
                    business_id,
                    sample_xml_invoice
                )

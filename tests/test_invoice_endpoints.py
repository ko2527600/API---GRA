"""Tests for invoice API endpoints"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from app.schemas.invoice import (
    InvoiceSubmissionSchema,
    InvoiceResponseSchema,
    InvoiceAcceptedResponseSchema
)


class TestInvoiceEndpoints:
    """Tests for invoice endpoints"""
    
    def test_submit_invoice_schema_validation(self):
        """Test 1: Invoice submission schema validation"""
        invoice_data = {
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
                "INVOICE_DATE": "2026-02-11",
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
                    "ITMDES": "Product 1",
                    "QUANTITY": "10",
                    "UNITYPRICE": "100",
                    "TAXCODE": "B",
                    "TAXRATE": "15",
                    "LEVY_AMOUNT_A": "2.50",
                    "LEVY_AMOUNT_B": "2.50",
                    "LEVY_AMOUNT_C": "0",
                    "LEVY_AMOUNT_D": "0"
                }
            ]
        }
        
        submission = InvoiceSubmissionSchema(**invoice_data)
        assert submission.company.COMPANY_NAMES == "ABC COMPANY LTD"
        assert submission.header.NUM == "INV-2026-001"
        assert len(submission.item_list) == 1
    
    def test_submit_invoice_with_multiple_items(self):
        """Test 2: Submit invoice with multiple items"""
        invoice_data = {
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
                "NUM": "INV-2026-002",
                "INVOICE_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "CLIENT_NAME": "Customer Ltd",
                "CLIENT_TIN": "C0022825405",
                "TOTAL_VAT": "318",
                "TOTAL_LEVY": "120",
                "TOTAL_AMOUNT": "6876",
                "ITEMS_COUNTS": "2"
            },
            "item_list": [
                {
                    "ITMREF": "PROD001",
                    "ITMDES": "Product 1",
                    "QUANTITY": "10",
                    "UNITYPRICE": "100",
                    "TAXCODE": "B",
                    "TAXRATE": "15",
                    "LEVY_AMOUNT_A": "2.50",
                    "LEVY_AMOUNT_B": "2.50",
                    "LEVY_AMOUNT_C": "0",
                    "LEVY_AMOUNT_D": "0"
                },
                {
                    "ITMREF": "PROD002",
                    "ITMDES": "Product 2",
                    "QUANTITY": "5",
                    "UNITYPRICE": "200",
                    "TAXCODE": "B",
                    "TAXRATE": "15",
                    "LEVY_AMOUNT_A": "5.00",
                    "LEVY_AMOUNT_B": "5.00",
                    "LEVY_AMOUNT_C": "0",
                    "LEVY_AMOUNT_D": "0"
                }
            ]
        }
        
        submission = InvoiceSubmissionSchema(**invoice_data)
        assert len(submission.item_list) == 2
        assert submission.header.ITEMS_COUNTS == "2"
    
    def test_invoice_accepted_response(self):
        """Test 3: Invoice accepted response"""
        response = InvoiceAcceptedResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            invoice_num="INV-2026-001"
        )
        
        assert response.status == "RECEIVED"
        assert response.validation_passed is True
        assert response.invoice_num == "INV-2026-001"
    
    def test_invoice_response_success(self):
        """Test 4: Invoice response for successful submission"""
        now = datetime.now()
        response = InvoiceResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            invoice_num="INV-2026-001",
            status="SUCCESS",
            gra_invoice_id="GRA-INV-2026-001",
            gra_qr_code="https://gra.gov.gh/qr/abc123def456",
            gra_receipt_num="VSDC-REC-12345",
            submitted_at=now,
            completed_at=now,
            processing_time_ms=5000
        )
        
        assert response.status == "SUCCESS"
        assert response.gra_invoice_id == "GRA-INV-2026-001"
        assert response.processing_time_ms == 5000
    
    def test_invoice_response_status_lifecycle(self):
        """Test 5: Invoice response status lifecycle"""
        submission_id = "550e8400-e29b-41d4-a716-446655440000"
        now = datetime.now()
        
        # RECEIVED status
        response_received = InvoiceResponseSchema(
            submission_id=submission_id,
            invoice_num="INV-2026-001",
            status="RECEIVED",
            submitted_at=now
        )
        assert response_received.status == "RECEIVED"
        
        # PROCESSING status
        response_processing = InvoiceResponseSchema(
            submission_id=submission_id,
            invoice_num="INV-2026-001",
            status="PROCESSING",
            submitted_at=now
        )
        assert response_processing.status == "PROCESSING"
        
        # PENDING_GRA status
        response_pending = InvoiceResponseSchema(
            submission_id=submission_id,
            invoice_num="INV-2026-001",
            status="PENDING_GRA",
            submitted_at=now
        )
        assert response_pending.status == "PENDING_GRA"
        
        # SUCCESS status
        response_success = InvoiceResponseSchema(
            submission_id=submission_id,
            invoice_num="INV-2026-001",
            status="SUCCESS",
            gra_invoice_id="GRA-INV-2026-001",
            submitted_at=now,
            completed_at=now
        )
        assert response_success.status == "SUCCESS"
        
        # FAILED status
        response_failed = InvoiceResponseSchema(
            submission_id=submission_id,
            invoice_num="INV-2026-001",
            status="FAILED",
            gra_response_code="B16",
            gra_response_message="INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            submitted_at=now,
            completed_at=now
        )
        assert response_failed.status == "FAILED"
    
    def test_invoice_submission_invalid_tin(self):
        """Test 6: Invoice submission with invalid TIN"""
        from pydantic import ValidationError
        
        invoice_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "INVALID"  # Invalid TIN
            },
            "header": {
                "COMPUTATION_TYPE": "INCLUSIVE",
                "FLAG": "INVOICE",
                "SALE_TYPE": "NORMAL",
                "USER_NAME": "JOHN",
                "NUM": "INV-2026-001",
                "INVOICE_DATE": "2026-02-11",
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
                    "ITMDES": "Product 1",
                    "QUANTITY": "10",
                    "UNITYPRICE": "100",
                    "TAXCODE": "B",
                    "TAXRATE": "15",
                    "LEVY_AMOUNT_A": "2.50",
                    "LEVY_AMOUNT_B": "2.50",
                    "LEVY_AMOUNT_C": "0",
                    "LEVY_AMOUNT_D": "0"
                }
            ]
        }
        
        with pytest.raises(ValidationError):
            InvoiceSubmissionSchema(**invoice_data)
    
    def test_invoice_submission_item_count_mismatch(self):
        """Test 7: Invoice submission with item count mismatch"""
        from pydantic import ValidationError
        
        invoice_data = {
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
                "INVOICE_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "CLIENT_NAME": "Customer Ltd",
                "CLIENT_TIN": "C0022825405",
                "TOTAL_VAT": "159",
                "TOTAL_LEVY": "60",
                "TOTAL_AMOUNT": "3438",
                "ITEMS_COUNTS": "2"  # Says 2 items
            },
            "item_list": [
                {
                    "ITMREF": "PROD001",
                    "ITMDES": "Product 1",
                    "QUANTITY": "10",
                    "UNITYPRICE": "100",
                    "TAXCODE": "B",
                    "TAXRATE": "15",
                    "LEVY_AMOUNT_A": "2.50",
                    "LEVY_AMOUNT_B": "2.50",
                    "LEVY_AMOUNT_C": "0",
                    "LEVY_AMOUNT_D": "0"
                }
                # Only 1 item provided
            ]
        }
        
        with pytest.raises(ValidationError):
            InvoiceSubmissionSchema(**invoice_data)
    
    def test_invoice_response_with_gra_error(self):
        """Test 8: Invoice response with GRA error"""
        now = datetime.now()
        response = InvoiceResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            invoice_num="INV-2026-001",
            status="FAILED",
            gra_response_code="B16",
            gra_response_message="INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            submitted_at=now,
            completed_at=now
        )
        
        assert response.status == "FAILED"
        assert response.gra_response_code == "B16"
        assert response.gra_response_message is not None
    
    def test_invoice_submission_all_tax_codes(self):
        """Test 9: Invoice submission with all tax codes"""
        tax_codes = ["A", "B", "C", "D", "E"]
        tax_rates = {"A": "0", "B": "15", "C": "0", "D": "0", "E": "3"}
        
        for tax_code in tax_codes:
            invoice_data = {
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
                    "NUM": f"INV-{tax_code}-001",
                    "INVOICE_DATE": "2026-02-11",
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
                        "ITMREF": f"PROD_{tax_code}",
                        "ITMDES": f"Product {tax_code}",
                        "QUANTITY": "10",
                        "UNITYPRICE": "100",
                        "TAXCODE": tax_code,
                        "TAXRATE": tax_rates[tax_code],
                        "LEVY_AMOUNT_A": "2.50",
                        "LEVY_AMOUNT_B": "2.50",
                        "LEVY_AMOUNT_C": "0",
                        "LEVY_AMOUNT_D": "0"
                    }
                ]
            }
            
            submission = InvoiceSubmissionSchema(**invoice_data)
            assert submission.item_list[0].TAXCODE == tax_code
    
    def test_invoice_response_processing_time_calculation(self):
        """Test 10: Invoice response processing time calculation"""
        from datetime import timedelta
        
        submitted_at = datetime.now()
        completed_at = submitted_at + timedelta(seconds=5)
        
        response = InvoiceResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            invoice_num="INV-2026-001",
            status="SUCCESS",
            gra_invoice_id="GRA-INV-2026-001",
            submitted_at=submitted_at,
            completed_at=completed_at,
            processing_time_ms=5000
        )
        
        assert response.processing_time_ms == 5000
        assert response.completed_at is not None


class TestInvoiceSignatureEndpoint:
    """Tests for invoice signature/stamping endpoint"""
    
    def test_get_invoice_signature_success(self, client_with_db, db_session):
        """Test 1: Get invoice signature with successful submission"""
        from app.models.models import Business, Submission, Invoice
        from uuid import uuid4
        import json
        
        # Create test business
        business = Business(
            id=uuid4(),
            name="Test Business",
            api_key="test-api-key-sig-001",
            api_secret="test-api-secret-sig-001",
            gra_tin="C00XXXXXXXX",
            gra_company_name="Test Company",
            gra_security_key="test-security-key"
        )
        db_session.add(business)
        db_session.flush()
        
        # Create test submission with signature details
        submission_id = uuid4()
        submission = Submission(
            id=submission_id,
            business_id=business.id,
            submission_type="INVOICE",
            submission_status="SUCCESS",
            gra_invoice_id="GRA-INV-2026-001",
            gra_qr_code="https://gra.gov.gh/qr/abc123",
            gra_receipt_num="VSDC-REC-12345",
            ysdcid="VSDC-ID-001",
            ysdcrecnum="VSDC-REC-12345",
            ysdcintdata="internal-data-string",
            ysdcnrc="NRC-12345",
            raw_request={"test": "data"},
            raw_response={"test": "response"},
            submitted_at=datetime.now(),
            completed_at=datetime.now()
        )
        db_session.add(submission)
        db_session.flush()
        
        # Create test invoice
        invoice = Invoice(
            id=uuid4(),
            submission_id=submission_id,
            business_id=business.id,
            invoice_num="INV-2026-001",
            client_name="Customer Ltd",
            client_tin="C0022825405",
            invoice_date="2026-02-11",
            computation_type="INCLUSIVE",
            total_vat="159",
            total_levy="60",
            total_amount="3438",
            items_count=1
        )
        db_session.add(invoice)
        db_session.commit()
        
        # Expunge all to clear session cache and ensure fresh queries
        db_session.expunge_all()
        
        # Make request to signature endpoint
        response = client_with_db.get(
            f"/api/v1/invoices/{submission_id}/signature",
            headers={"X-API-Key": "test-api-key-sig-001"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["submission_id"] == str(submission_id)
        assert data["invoice_num"] == "INV-2026-001"
        assert data["status"] == "SUCCESS"
        assert data["ysdcid"] == "VSDC-ID-001"
        assert data["ysdcrecnum"] == "VSDC-REC-12345"
        assert data["ysdcintdata"] == "internal-data-string"
        assert data["ysdcnrc"] == "NRC-12345"
        assert data["gra_qr_code"] == "https://gra.gov.gh/qr/abc123"
        assert data["gra_invoice_id"] == "GRA-INV-2026-001"
        assert data["gra_receipt_num"] == "VSDC-REC-12345"
    
    def test_get_invoice_signature_missing_submission(self, client_with_db, db_session):
        """Test 2: Get invoice signature with missing submission"""
        from app.models.models import Business
        from uuid import uuid4
        
        # Create test business
        business = Business(
            id=uuid4(),
            name="Test Business",
            api_key="test-api-key-sig-002",
            api_secret="test-api-secret-sig-002",
            gra_tin="C00XXXXXXXX",
            gra_company_name="Test Company",
            gra_security_key="test-security-key"
        )
        db_session.add(business)
        db_session.commit()
        
        # Try to get signature for non-existent submission
        fake_submission_id = uuid4()
        response = client_with_db.get(
            f"/invoices/{fake_submission_id}/signature",
            headers={"X-API-Key": "test-api-key-sig-002"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_get_invoice_signature_unauthorized(self, client_with_db, db_session):
        """Test 3: Get invoice signature with invalid API key"""
        from uuid import uuid4
        
        fake_submission_id = uuid4()
        response = client_with_db.get(
            f"/api/v1/invoices/{fake_submission_id}/signature",
            headers={"X-API-Key": "invalid-api-key"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "unauthorized" in data["detail"].lower() or "invalid" in data["detail"].lower()
    
    def test_get_invoice_signature_cross_tenant_isolation(self, client_with_db, db_session):
        """Test 4: Get invoice signature - cross-tenant isolation"""
        from app.models.models import Business, Submission, Invoice
        from uuid import uuid4
        
        # Create two businesses
        business1 = Business(
            id=uuid4(),
            name="Business 1",
            api_key="test-api-key-sig-003",
            api_secret="test-api-secret-sig-003",
            gra_tin="C00XXXXXXXX",
            gra_company_name="Test Company 1",
            gra_security_key="test-security-key"
        )
        business2 = Business(
            id=uuid4(),
            name="Business 2",
            api_key="test-api-key-sig-004",
            api_secret="test-api-secret-sig-004",
            gra_tin="C00YYYYYYYY",
            gra_company_name="Test Company 2",
            gra_security_key="test-security-key"
        )
        db_session.add(business1)
        db_session.add(business2)
        db_session.commit()
        
        # Create submission for business2
        submission_id = uuid4()
        submission = Submission(
            id=submission_id,
            business_id=business2.id,
            submission_type="INVOICE",
            submission_status="SUCCESS",
            gra_invoice_id="GRA-INV-2026-001",
            gra_qr_code="https://gra.gov.gh/qr/abc123",
            gra_receipt_num="VSDC-REC-12345",
            ysdcid="VSDC-ID-001",
            ysdcrecnum="VSDC-REC-12345",
            ysdcintdata="internal-data-string",
            ysdcnrc="NRC-12345",
            raw_request={"test": "data"},
            raw_response={"test": "response"},
            submitted_at=datetime.now(),
            completed_at=datetime.now()
        )
        db_session.add(submission)
        db_session.commit()
        
        # Create invoice for business2
        invoice = Invoice(
            id=uuid4(),
            submission_id=submission_id,
            business_id=business2.id,
            invoice_num="INV-2026-001",
            client_name="Customer Ltd",
            client_tin="C0022825405",
            invoice_date="2026-02-11",
            computation_type="INCLUSIVE",
            total_vat="159",
            total_levy="60",
            total_amount="3438",
            items_count=1
        )
        db_session.add(invoice)
        db_session.commit()
        
        # Try to access business2's submission with business1's API key
        response = client_with_db.get(
            f"/api/v1/invoices/{submission_id}/signature",
            headers={"X-API-Key": "test-api-key-sig-003"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_get_invoice_signature_pending_status(self, client_with_db, db_session):
        """Test 5: Get invoice signature with pending submission"""
        from app.models.models import Business, Submission, Invoice
        from uuid import uuid4
        
        # Create test business
        business = Business(
            id=uuid4(),
            name="Test Business",
            api_key="test-api-key-sig-005",
            api_secret="test-api-secret-sig-005",
            gra_tin="C00XXXXXXXX",
            gra_company_name="Test Company",
            gra_security_key="test-security-key"
        )
        db_session.add(business)
        db_session.commit()
        
        # Create test submission with PENDING_GRA status
        submission_id = uuid4()
        submission = Submission(
            id=submission_id,
            business_id=business.id,
            submission_type="INVOICE",
            submission_status="PENDING_GRA",
            raw_request={"test": "data"},
            submitted_at=datetime.now()
        )
        db_session.add(submission)
        db_session.commit()
        
        # Create test invoice
        invoice = Invoice(
            id=uuid4(),
            submission_id=submission_id,
            business_id=business.id,
            invoice_num="INV-2026-002",
            client_name="Customer Ltd",
            client_tin="C0022825405",
            invoice_date="2026-02-11",
            computation_type="INCLUSIVE",
            total_vat="159",
            total_levy="60",
            total_amount="3438",
            items_count=1
        )
        db_session.add(invoice)
        db_session.commit()
        
        # Make request to signature endpoint
        response = client_with_db.get(
            f"/api/v1/invoices/{submission_id}/signature",
            headers={"X-API-Key": "test-api-key-sig-005"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PENDING_GRA"
        assert data["ysdcid"] is None
        assert data["gra_qr_code"] is None
    
    def test_get_invoice_signature_failed_status(self, client_with_db, db_session):
        """Test 6: Get invoice signature with failed submission"""
        from app.models.models import Business, Submission, Invoice
        from uuid import uuid4
        
        # Create test business
        business = Business(
            id=uuid4(),
            name="Test Business",
            api_key="test-api-key-sig-006",
            api_secret="test-api-secret-sig-006",
            gra_tin="C00XXXXXXXX",
            gra_company_name="Test Company",
            gra_security_key="test-security-key"
        )
        db_session.add(business)
        db_session.commit()
        
        # Create test submission with FAILED status
        submission_id = uuid4()
        submission = Submission(
            id=submission_id,
            business_id=business.id,
            submission_type="INVOICE",
            submission_status="FAILED",
            gra_response_code="B16",
            gra_response_message="INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            raw_request={"test": "data"},
            raw_response={"error": "B16"},
            submitted_at=datetime.now(),
            completed_at=datetime.now()
        )
        db_session.add(submission)
        db_session.commit()
        
        # Create test invoice
        invoice = Invoice(
            id=uuid4(),
            submission_id=submission_id,
            business_id=business.id,
            invoice_num="INV-2026-003",
            client_name="Customer Ltd",
            client_tin="C0022825405",
            invoice_date="2026-02-11",
            computation_type="INCLUSIVE",
            total_vat="159",
            total_levy="60",
            total_amount="3438",
            items_count=1
        )
        db_session.add(invoice)
        db_session.commit()
        
        # Make request to signature endpoint
        response = client_with_db.get(
            f"/api/v1/invoices/{submission_id}/signature",
            headers={"X-API-Key": "test-api-key-sig-006"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "FAILED"
        assert data["gra_response_code"] == "B16"
        assert data["gra_response_message"] == "INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT"
    
    def test_get_invoice_signature_qr_code_format(self, client_with_db, db_session):
        """Test 7: Get invoice signature - QR code format validation"""
        from app.models.models import Business, Submission, Invoice
        from uuid import uuid4
        
        # Create test business
        business = Business(
            id=uuid4(),
            name="Test Business",
            api_key="test-api-key-sig-007",
            api_secret="test-api-secret-sig-007",
            gra_tin="C00XXXXXXXX",
            gra_company_name="Test Company",
            gra_security_key="test-security-key"
        )
        db_session.add(business)
        db_session.commit()
        
        # Create test submission with QR code
        submission_id = uuid4()
        qr_code_url = "https://gra.gov.gh/qr/invoice-2026-001-abc123xyz789"
        submission = Submission(
            id=submission_id,
            business_id=business.id,
            submission_type="INVOICE",
            submission_status="SUCCESS",
            gra_invoice_id="GRA-INV-2026-001",
            gra_qr_code=qr_code_url,
            gra_receipt_num="VSDC-REC-12345",
            ysdcid="VSDC-ID-001",
            ysdcrecnum="VSDC-REC-12345",
            ysdcintdata="internal-data-string",
            ysdcnrc="NRC-12345",
            raw_request={"test": "data"},
            raw_response={"test": "response"},
            submitted_at=datetime.now(),
            completed_at=datetime.now()
        )
        db_session.add(submission)
        db_session.commit()
        
        # Create test invoice
        invoice = Invoice(
            id=uuid4(),
            submission_id=submission_id,
            business_id=business.id,
            invoice_num="INV-2026-001",
            client_name="Customer Ltd",
            client_tin="C0022825405",
            invoice_date="2026-02-11",
            computation_type="INCLUSIVE",
            total_vat="159",
            total_levy="60",
            total_amount="3438",
            items_count=1
        )
        db_session.add(invoice)
        db_session.commit()
        
        # Make request to signature endpoint
        response = client_with_db.get(
            f"/api/v1/invoices/{submission_id}/signature",
            headers={"X-API-Key": "test-api-key-sig-007"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["gra_qr_code"] == qr_code_url
        assert data["gra_qr_code"].startswith("https://")
    
    def test_get_invoice_signature_all_vsdc_fields(self, client_with_db, db_session):
        """Test 8: Get invoice signature - all VSDC fields populated"""
        from app.models.models import Business, Submission, Invoice
        from uuid import uuid4
        
        # Create test business
        business = Business(
            id=uuid4(),
            name="Test Business",
            api_key="test-api-key-sig-008",
            api_secret="test-api-secret-sig-008",
            gra_tin="C00XXXXXXXX",
            gra_company_name="Test Company",
            gra_security_key="test-security-key"
        )
        db_session.add(business)
        db_session.commit()
        
        # Create test submission with all VSDC fields
        submission_id = uuid4()
        submission = Submission(
            id=submission_id,
            business_id=business.id,
            submission_type="INVOICE",
            submission_status="SUCCESS",
            gra_invoice_id="GRA-INV-2026-001",
            gra_qr_code="https://gra.gov.gh/qr/abc123",
            gra_receipt_num="VSDC-REC-12345",
            ysdcid="VSDC-ID-001",
            ysdcrecnum="VSDC-REC-12345",
            ysdcintdata="integrated-data-12345-abcdef",
            ysdcnrc="NRC-12345",
            raw_request={"test": "data"},
            raw_response={"test": "response"},
            submitted_at=datetime.now(),
            completed_at=datetime.now()
        )
        db_session.add(submission)
        db_session.commit()
        
        # Create test invoice
        invoice = Invoice(
            id=uuid4(),
            submission_id=submission_id,
            business_id=business.id,
            invoice_num="INV-2026-001",
            client_name="Customer Ltd",
            client_tin="C0022825405",
            invoice_date="2026-02-11",
            computation_type="INCLUSIVE",
            total_vat="159",
            total_levy="60",
            total_amount="3438",
            items_count=1
        )
        db_session.add(invoice)
        db_session.commit()
        
        # Make request to signature endpoint
        response = client_with_db.get(
            f"/api/v1/invoices/{submission_id}/signature",
            headers={"X-API-Key": "test-api-key-sig-008"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["ysdcid"] == "VSDC-ID-001"
        assert data["ysdcrecnum"] == "VSDC-REC-12345"
        assert data["ysdcintdata"] == "integrated-data-12345-abcdef"
        assert data["ysdcnrc"] == "NRC-12345"
        assert data["gra_qr_code"] == "https://gra.gov.gh/qr/abc123"
        assert data["gra_invoice_id"] == "GRA-INV-2026-001"
        assert data["gra_receipt_num"] == "VSDC-REC-12345"
    
    def test_get_invoice_signature_refund_submission_not_found(self, client_with_db, db_session):
        """Test 9: Get invoice signature - refund submission returns 404"""
        from app.models.models import Business, Submission
        from uuid import uuid4
        
        # Create test business
        business = Business(
            id=uuid4(),
            name="Test Business",
            api_key="test-api-key-sig-009",
            api_secret="test-api-secret-sig-009",
            gra_tin="C00XXXXXXXX",
            gra_company_name="Test Company",
            gra_security_key="test-security-key"
        )
        db_session.add(business)
        db_session.commit()
        
        # Create test submission with REFUND type (not INVOICE)
        submission_id = uuid4()
        submission = Submission(
            id=submission_id,
            business_id=business.id,
            submission_type="REFUND",
            submission_status="SUCCESS",
            raw_request={"test": "data"},
            submitted_at=datetime.now(),
            completed_at=datetime.now()
        )
        db_session.add(submission)
        db_session.commit()
        
        # Try to get signature for refund submission
        response = client_with_db.get(
            f"/api/v1/invoices/{submission_id}/signature",
            headers={"X-API-Key": "test-api-key-sig-009"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_get_invoice_signature_response_schema_validation(self, client_with_db, db_session):
        """Test 10: Get invoice signature - response schema validation"""
        from app.models.models import Business, Submission, Invoice
        from uuid import uuid4
        
        # Create test business
        business = Business(
            id=uuid4(),
            name="Test Business",
            api_key="test-api-key-sig-010",
            api_secret="test-api-secret-sig-010",
            gra_tin="C00XXXXXXXX",
            gra_company_name="Test Company",
            gra_security_key="test-security-key"
        )
        db_session.add(business)
        db_session.commit()
        
        # Create test submission
        submission_id = uuid4()
        submission = Submission(
            id=submission_id,
            business_id=business.id,
            submission_type="INVOICE",
            submission_status="SUCCESS",
            gra_invoice_id="GRA-INV-2026-001",
            gra_qr_code="https://gra.gov.gh/qr/abc123",
            gra_receipt_num="VSDC-REC-12345",
            ysdcid="VSDC-ID-001",
            ysdcrecnum="VSDC-REC-12345",
            ysdcintdata="internal-data-string",
            ysdcnrc="NRC-12345",
            raw_request={"test": "data"},
            raw_response={"test": "response"},
            submitted_at=datetime.now(),
            completed_at=datetime.now()
        )
        db_session.add(submission)
        db_session.commit()
        
        # Create test invoice
        invoice = Invoice(
            id=uuid4(),
            submission_id=submission_id,
            business_id=business.id,
            invoice_num="INV-2026-001",
            client_name="Customer Ltd",
            client_tin="C0022825405",
            invoice_date="2026-02-11",
            computation_type="INCLUSIVE",
            total_vat="159",
            total_levy="60",
            total_amount="3438",
            items_count=1
        )
        db_session.add(invoice)
        db_session.commit()
        
        # Make request to signature endpoint
        response = client_with_db.get(
            f"/api/v1/invoices/{submission_id}/signature",
            headers={"X-API-Key": "test-api-key-sig-010"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response schema
        assert "submission_id" in data
        assert "invoice_num" in data
        assert "status" in data
        assert "ysdcid" in data
        assert "ysdcrecnum" in data
        assert "ysdcintdata" in data
        assert "ysdcnrc" in data
        assert "gra_qr_code" in data
        assert "gra_invoice_id" in data
        assert "gra_receipt_num" in data
        assert "gra_response_code" in data
        assert "gra_response_message" in data
        assert "completed_at" in data

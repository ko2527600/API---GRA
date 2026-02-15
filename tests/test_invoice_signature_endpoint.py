"""Tests for invoice signature/stamping endpoint"""
import pytest
from datetime import datetime
from uuid import uuid4

from app.schemas.invoice import InvoiceSignatureResponseSchema


class TestInvoiceSignatureResponseSchema:
    """Tests for InvoiceSignatureResponseSchema"""
    
    def test_signature_response_schema_success(self):
        """Test 1: Signature response schema with successful submission"""
        submission_id = str(uuid4())
        now = datetime.now()
        
        response = InvoiceSignatureResponseSchema(
            submission_id=submission_id,
            invoice_num="INV-2026-001",
            status="SUCCESS",
            ysdcid="VSDC-ID-001",
            ysdcrecnum="VSDC-REC-12345",
            ysdcintdata="internal-data-string",
            ysdcnrc="NRC-12345",
            gra_qr_code="https://gra.gov.gh/qr/abc123",
            gra_invoice_id="GRA-INV-2026-001",
            gra_receipt_num="VSDC-REC-12345",
            gra_response_code=None,
            gra_response_message=None,
            completed_at=now
        )
        
        assert response.submission_id == submission_id
        assert response.invoice_num == "INV-2026-001"
        assert response.status == "SUCCESS"
        assert response.ysdcid == "VSDC-ID-001"
        assert response.ysdcrecnum == "VSDC-REC-12345"
        assert response.ysdcintdata == "internal-data-string"
        assert response.ysdcnrc == "NRC-12345"
        assert response.gra_qr_code == "https://gra.gov.gh/qr/abc123"
        assert response.gra_invoice_id == "GRA-INV-2026-001"
        assert response.gra_response_code is None
        assert response.gra_response_message is None
    
    def test_signature_response_schema_pending(self):
        """Test 2: Signature response schema with pending submission"""
        submission_id = str(uuid4())
        
        response = InvoiceSignatureResponseSchema(
            submission_id=submission_id,
            invoice_num="INV-2026-002",
            status="PENDING_GRA",
            ysdcid=None,
            ysdcrecnum=None,
            ysdcintdata=None,
            ysdcnrc=None,
            gra_qr_code=None,
            gra_invoice_id=None,
            gra_receipt_num=None,
            gra_response_code=None,
            gra_response_message=None,
            completed_at=None
        )
        
        assert response.status == "PENDING_GRA"
        assert response.ysdcid is None
        assert response.ysdcrecnum is None
        assert response.completed_at is None
    
    def test_signature_response_schema_failed(self):
        """Test 3: Signature response schema with failed submission"""
        submission_id = str(uuid4())
        
        response = InvoiceSignatureResponseSchema(
            submission_id=submission_id,
            invoice_num="INV-2026-003",
            status="FAILED",
            ysdcid=None,
            ysdcrecnum=None,
            ysdcintdata=None,
            ysdcnrc=None,
            gra_qr_code=None,
            gra_invoice_id=None,
            gra_receipt_num=None,
            gra_response_code="B16",
            gra_response_message="INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            completed_at=datetime.now()
        )
        
        assert response.status == "FAILED"
        assert response.gra_response_code == "B16"
        assert response.gra_response_message == "INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT"
    
    def test_signature_response_schema_all_fields_optional(self):
        """Test 4: Signature response schema with minimal required fields"""
        submission_id = str(uuid4())
        
        response = InvoiceSignatureResponseSchema(
            submission_id=submission_id,
            invoice_num="INV-2026-004",
            status="RECEIVED"
        )
        
        assert response.submission_id == submission_id
        assert response.invoice_num == "INV-2026-004"
        assert response.status == "RECEIVED"
        assert response.ysdcid is None
        assert response.gra_qr_code is None
    
    def test_signature_response_schema_invalid_status(self):
        """Test 5: Signature response schema with invalid status"""
        submission_id = str(uuid4())
        
        with pytest.raises(ValueError):
            InvoiceSignatureResponseSchema(
                submission_id=submission_id,
                invoice_num="INV-2026-005",
                status="INVALID_STATUS"
            )
    
    def test_signature_response_schema_all_vsdc_fields(self):
        """Test 6: Signature response schema with all VSDC fields populated"""
        submission_id = str(uuid4())
        now = datetime.now()
        
        response = InvoiceSignatureResponseSchema(
            submission_id=submission_id,
            invoice_num="INV-2026-006",
            status="SUCCESS",
            ysdcid="VSDC-ID-002",
            ysdcrecnum="VSDC-REC-67890",
            ysdcintdata="integrated-data-12345",
            ysdcnrc="NRC-67890",
            gra_qr_code="https://gra.gov.gh/qr/xyz789",
            gra_invoice_id="GRA-INV-2026-002",
            gra_receipt_num="VSDC-REC-67890",
            gra_response_code=None,
            gra_response_message=None,
            completed_at=now
        )
        
        assert response.ysdcid == "VSDC-ID-002"
        assert response.ysdcrecnum == "VSDC-REC-67890"
        assert response.ysdcintdata == "integrated-data-12345"
        assert response.ysdcnrc == "NRC-67890"
        assert response.gra_qr_code == "https://gra.gov.gh/qr/xyz789"
    
    def test_signature_response_schema_with_error_details(self):
        """Test 7: Signature response schema with error details"""
        submission_id = str(uuid4())
        
        response = InvoiceSignatureResponseSchema(
            submission_id=submission_id,
            invoice_num="INV-2026-007",
            status="FAILED",
            ysdcid=None,
            ysdcrecnum=None,
            ysdcintdata=None,
            ysdcnrc=None,
            gra_qr_code=None,
            gra_invoice_id=None,
            gra_receipt_num=None,
            gra_response_code="A01",
            gra_response_message="Company credentials do not exist",
            completed_at=datetime.now()
        )
        
        assert response.gra_response_code == "A01"
        assert response.gra_response_message == "Company credentials do not exist"
    
    def test_signature_response_schema_received_status(self):
        """Test 8: Signature response schema with RECEIVED status"""
        submission_id = str(uuid4())
        
        response = InvoiceSignatureResponseSchema(
            submission_id=submission_id,
            invoice_num="INV-2026-008",
            status="RECEIVED"
        )
        
        assert response.status == "RECEIVED"
        assert response.completed_at is None
    
    def test_signature_response_schema_processing_status(self):
        """Test 9: Signature response schema with PROCESSING status"""
        submission_id = str(uuid4())
        
        response = InvoiceSignatureResponseSchema(
            submission_id=submission_id,
            invoice_num="INV-2026-009",
            status="PROCESSING"
        )
        
        assert response.status == "PROCESSING"
    
    def test_signature_response_schema_model_dump(self):
        """Test 10: Signature response schema model_dump"""
        submission_id = str(uuid4())
        now = datetime.now()
        
        response = InvoiceSignatureResponseSchema(
            submission_id=submission_id,
            invoice_num="INV-2026-010",
            status="SUCCESS",
            ysdcid="VSDC-ID-001",
            ysdcrecnum="VSDC-REC-12345",
            ysdcintdata="internal-data-string",
            ysdcnrc="NRC-12345",
            gra_qr_code="https://gra.gov.gh/qr/abc123",
            gra_invoice_id="GRA-INV-2026-001",
            gra_receipt_num="VSDC-REC-12345",
            gra_response_code=None,
            gra_response_message=None,
            completed_at=now
        )
        
        dumped = response.model_dump()
        assert dumped["submission_id"] == submission_id
        assert dumped["invoice_num"] == "INV-2026-010"
        assert dumped["status"] == "SUCCESS"
        assert dumped["ysdcid"] == "VSDC-ID-001"

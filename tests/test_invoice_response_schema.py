"""Tests for InvoiceResponseSchema and related response schemas"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.invoice import (
    InvoiceResponseSchema,
    InvoiceAcceptedResponseSchema,
    InvoiceErrorResponseSchema,
    ValidationErrorSchema
)


class TestValidationErrorSchema:
    """Test ValidationErrorSchema"""
    
    def test_valid_validation_error(self):
        """Test creating a valid validation error"""
        data = {
            "field": "TOTAL_AMOUNT",
            "error": "B16 - INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            "expected": "3438",
            "actual": "3400"
        }
        error = ValidationErrorSchema(**data)
        assert error.field == "TOTAL_AMOUNT"
        assert error.error == "B16 - INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT"
        assert error.expected == "3438"
        assert error.actual == "3400"
    
    def test_validation_error_without_expected_actual(self):
        """Test validation error without expected/actual values"""
        data = {
            "field": "CLIENT_NAME",
            "error": "B05 - CLIENT NAME MISSING"
        }
        error = ValidationErrorSchema(**data)
        assert error.field == "CLIENT_NAME"
        assert error.error == "B05 - CLIENT NAME MISSING"
        assert error.expected is None
        assert error.actual is None
    
    def test_missing_field(self):
        """Test missing required field"""
        data = {
            "error": "B16 - INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT"
        }
        with pytest.raises(ValidationError) as exc_info:
            ValidationErrorSchema(**data)
        assert "field" in str(exc_info.value).lower()
    
    def test_missing_error(self):
        """Test missing error message"""
        data = {
            "field": "TOTAL_AMOUNT"
        }
        with pytest.raises(ValidationError) as exc_info:
            ValidationErrorSchema(**data)
        assert "error" in str(exc_info.value).lower()


class TestInvoiceResponseSchema:
    """Test InvoiceResponseSchema for successful submissions"""
    
    def test_valid_success_response(self):
        """Test creating a valid success response"""
        data = {
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "invoice_num": "INV-2026-001",
            "status": "SUCCESS",
            "gra_response_code": None,
            "gra_response_message": None,
            "gra_invoice_id": "GRA-INV-2026-001",
            "gra_qr_code": "https://gra.gov.gh/qr/abc123def456",
            "gra_receipt_num": "VSDC-REC-12345",
            "ysdcid": "VSDC-ID-001",
            "ysdcrecnum": "VSDC-REC-12345",
            "ysdcintdata": "internal-data-string",
            "ysdcnrc": "NRC-12345",
            "submitted_at": datetime.now(),
            "completed_at": datetime.now(),
            "processing_time_ms": 5000
        }
        response = InvoiceResponseSchema(**data)
        assert response.submission_id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.invoice_num == "INV-2026-001"
        assert response.status == "SUCCESS"
        assert response.gra_invoice_id == "GRA-INV-2026-001"
        assert response.gra_qr_code == "https://gra.gov.gh/qr/abc123def456"
        assert response.processing_time_ms == 5000
    
    def test_valid_processing_response(self):
        """Test response with PROCESSING status"""
        data = {
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "invoice_num": "INV-2026-001",
            "status": "PROCESSING",
            "submitted_at": datetime.now()
        }
        response = InvoiceResponseSchema(**data)
        assert response.status == "PROCESSING"
        assert response.gra_invoice_id is None
        assert response.completed_at is None
    
    def test_valid_pending_gra_response(self):
        """Test response with PENDING_GRA status"""
        data = {
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "invoice_num": "INV-2026-001",
            "status": "PENDING_GRA",
            "submitted_at": datetime.now()
        }
        response = InvoiceResponseSchema(**data)
        assert response.status == "PENDING_GRA"
    
    def test_valid_failed_response(self):
        """Test response with FAILED status"""
        data = {
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "invoice_num": "INV-2026-001",
            "status": "FAILED",
            "gra_response_code": "B16",
            "gra_response_message": "INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            "submitted_at": datetime.now(),
            "completed_at": datetime.now()
        }
        response = InvoiceResponseSchema(**data)
        assert response.status == "FAILED"
        assert response.gra_response_code == "B16"
        assert response.gra_response_message == "INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT"
    
    def test_valid_received_response(self):
        """Test response with RECEIVED status"""
        data = {
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "invoice_num": "INV-2026-001",
            "status": "RECEIVED",
            "submitted_at": datetime.now()
        }
        response = InvoiceResponseSchema(**data)
        assert response.status == "RECEIVED"
    
    def test_invalid_status(self):
        """Test invalid status value"""
        data = {
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "invoice_num": "INV-2026-001",
            "status": "INVALID_STATUS",
            "submitted_at": datetime.now()
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceResponseSchema(**data)
        assert "status" in str(exc_info.value).lower()
    
    def test_missing_submission_id(self):
        """Test missing submission_id"""
        data = {
            "invoice_num": "INV-2026-001",
            "status": "SUCCESS",
            "submitted_at": datetime.now()
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceResponseSchema(**data)
        assert "submission_id" in str(exc_info.value).lower()
    
    def test_missing_invoice_num(self):
        """Test missing invoice_num"""
        data = {
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "SUCCESS",
            "submitted_at": datetime.now()
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceResponseSchema(**data)
        assert "invoice_num" in str(exc_info.value).lower()
    
    def test_missing_status(self):
        """Test missing status"""
        data = {
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "invoice_num": "INV-2026-001",
            "submitted_at": datetime.now()
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceResponseSchema(**data)
        assert "status" in str(exc_info.value).lower()
    
    def test_missing_submitted_at(self):
        """Test missing submitted_at timestamp"""
        data = {
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "invoice_num": "INV-2026-001",
            "status": "SUCCESS"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceResponseSchema(**data)
        assert "submitted_at" in str(exc_info.value).lower()
    
    def test_response_with_all_vsdc_fields(self):
        """Test response with all VSDC stamping fields"""
        data = {
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "invoice_num": "INV-2026-001",
            "status": "SUCCESS",
            "gra_invoice_id": "GRA-INV-2026-001",
            "gra_qr_code": "https://gra.gov.gh/qr/abc123def456",
            "gra_receipt_num": "VSDC-REC-12345",
            "ysdcid": "VSDC-ID-001",
            "ysdcrecnum": "VSDC-REC-12345",
            "ysdcintdata": "internal-data-string",
            "ysdcnrc": "NRC-12345",
            "submitted_at": datetime.now(),
            "completed_at": datetime.now(),
            "processing_time_ms": 5000
        }
        response = InvoiceResponseSchema(**data)
        assert response.ysdcid == "VSDC-ID-001"
        assert response.ysdcrecnum == "VSDC-REC-12345"
        assert response.ysdcintdata == "internal-data-string"
        assert response.ysdcnrc == "NRC-12345"


class TestInvoiceAcceptedResponseSchema:
    """Test InvoiceAcceptedResponseSchema for 202 Accepted responses"""
    
    def test_valid_accepted_response(self):
        """Test creating a valid 202 accepted response"""
        data = {
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "invoice_num": "INV-2026-001"
        }
        response = InvoiceAcceptedResponseSchema(**data)
        assert response.submission_id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.invoice_num == "INV-2026-001"
        assert response.status == "RECEIVED"
        assert response.validation_passed is True
        assert response.message == "Invoice received and queued for GRA processing"
        assert response.next_action == "Check status using submission_id"
    
    def test_accepted_response_with_custom_message(self):
        """Test accepted response with custom message"""
        data = {
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "invoice_num": "INV-2026-001",
            "message": "Custom message"
        }
        response = InvoiceAcceptedResponseSchema(**data)
        assert response.message == "Custom message"
    
    def test_accepted_response_with_validation_failed(self):
        """Test accepted response with validation_passed=False"""
        data = {
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "invoice_num": "INV-2026-001",
            "validation_passed": False
        }
        response = InvoiceAcceptedResponseSchema(**data)
        assert response.validation_passed is False
    
    def test_missing_submission_id(self):
        """Test missing submission_id"""
        data = {
            "invoice_num": "INV-2026-001"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceAcceptedResponseSchema(**data)
        assert "submission_id" in str(exc_info.value).lower()
    
    def test_missing_invoice_num(self):
        """Test missing invoice_num"""
        data = {
            "submission_id": "550e8400-e29b-41d4-a716-446655440000"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceAcceptedResponseSchema(**data)
        assert "invoice_num" in str(exc_info.value).lower()


class TestInvoiceErrorResponseSchema:
    """Test InvoiceErrorResponseSchema for error responses"""
    
    def test_valid_validation_error_response(self):
        """Test creating a valid validation error response"""
        data = {
            "error_code": "VALIDATION_FAILED",
            "message": "Validation failed: TOTAL_AMOUNT mismatch",
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "gra_response_code": "B16",
            "gra_response_message": "INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            "validation_errors": [
                {
                    "field": "TOTAL_AMOUNT",
                    "error": "B16 - INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
                    "expected": "3438",
                    "actual": "3400"
                }
            ],
            "timestamp": datetime.now()
        }
        response = InvoiceErrorResponseSchema(**data)
        assert response.error_code == "VALIDATION_FAILED"
        assert response.message == "Validation failed: TOTAL_AMOUNT mismatch"
        assert response.gra_response_code == "B16"
        assert len(response.validation_errors) == 1
        assert response.validation_errors[0].field == "TOTAL_AMOUNT"
    
    def test_valid_auth_error_response(self):
        """Test creating a valid auth error response"""
        data = {
            "error_code": "AUTH_FAILED",
            "message": "Invalid API Key or signature",
            "timestamp": datetime.now()
        }
        response = InvoiceErrorResponseSchema(**data)
        assert response.error_code == "AUTH_FAILED"
        assert response.message == "Invalid API Key or signature"
        assert response.submission_id is None
        assert response.validation_errors is None
    
    def test_valid_server_error_response(self):
        """Test creating a valid server error response"""
        data = {
            "error_code": "SERVER_ERROR",
            "message": "An unexpected error occurred",
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "timestamp": datetime.now()
        }
        response = InvoiceErrorResponseSchema(**data)
        assert response.error_code == "SERVER_ERROR"
        assert response.message == "An unexpected error occurred"
    
    def test_error_response_with_multiple_validation_errors(self):
        """Test error response with multiple validation errors"""
        data = {
            "error_code": "VALIDATION_FAILED",
            "message": "Multiple validation errors",
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "validation_errors": [
                {
                    "field": "TOTAL_AMOUNT",
                    "error": "B16 - INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
                    "expected": "3438",
                    "actual": "3400"
                },
                {
                    "field": "TOTAL_VAT",
                    "error": "B18 - TOTAL VAT MISMATCH",
                    "expected": "159",
                    "actual": "150"
                }
            ],
            "timestamp": datetime.now()
        }
        response = InvoiceErrorResponseSchema(**data)
        assert len(response.validation_errors) == 2
        assert response.validation_errors[0].field == "TOTAL_AMOUNT"
        assert response.validation_errors[1].field == "TOTAL_VAT"
    
    def test_missing_error_code(self):
        """Test missing error_code"""
        data = {
            "message": "An error occurred",
            "timestamp": datetime.now()
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceErrorResponseSchema(**data)
        assert "error_code" in str(exc_info.value).lower()
    
    def test_missing_message(self):
        """Test missing message"""
        data = {
            "error_code": "SERVER_ERROR",
            "timestamp": datetime.now()
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceErrorResponseSchema(**data)
        assert "message" in str(exc_info.value).lower()
    
    def test_missing_timestamp(self):
        """Test missing timestamp"""
        data = {
            "error_code": "SERVER_ERROR",
            "message": "An error occurred"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceErrorResponseSchema(**data)
        assert "timestamp" in str(exc_info.value).lower()
    
    def test_error_response_with_gra_error_code(self):
        """Test error response with GRA error code"""
        data = {
            "error_code": "VALIDATION_FAILED",
            "message": "GRA validation failed",
            "submission_id": "550e8400-e29b-41d4-a716-446655440000",
            "gra_response_code": "B05",
            "gra_response_message": "CLIENT NAME MISSING",
            "timestamp": datetime.now()
        }
        response = InvoiceErrorResponseSchema(**data)
        assert response.gra_response_code == "B05"
        assert response.gra_response_message == "CLIENT NAME MISSING"

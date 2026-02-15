"""Integration tests for all invoice schemas working together"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.invoice import (
    InvoiceHeaderSchema,
    InvoiceItemSchema,
    InvoiceSubmissionSchema,
    InvoiceResponseSchema,
    InvoiceAcceptedResponseSchema,
    InvoiceErrorResponseSchema,
    CompanySchema,
    ValidationErrorSchema
)


class TestInvoiceSchemasIntegration:
    """Integration tests for all invoice schemas"""
    
    def test_complete_invoice_submission_flow(self):
        """Test 1: Complete invoice submission from request to response"""
        # Create a complete invoice submission
        submission_data = {
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
        
        # Validate submission schema
        submission = InvoiceSubmissionSchema(**submission_data)
        assert submission.company.COMPANY_NAMES == "ABC COMPANY LTD"
        assert submission.header.NUM == "INV-2026-001"
        assert len(submission.item_list) == 2
        
        # Simulate 202 Accepted response
        accepted_response = InvoiceAcceptedResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            invoice_num="INV-2026-001"
        )
        assert accepted_response.status == "RECEIVED"
        assert accepted_response.validation_passed is True
        
        # Simulate successful GRA response
        success_response = InvoiceResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            invoice_num="INV-2026-001",
            status="SUCCESS",
            gra_invoice_id="GRA-INV-2026-001",
            gra_qr_code="https://gra.gov.gh/qr/abc123def456",
            gra_receipt_num="VSDC-REC-12345",
            submitted_at=datetime.now(),
            completed_at=datetime.now(),
            processing_time_ms=5000
        )
        assert success_response.status == "SUCCESS"
        assert success_response.gra_invoice_id == "GRA-INV-2026-001"
    
    def test_invoice_submission_with_validation_error_response(self):
        """Test 2: Invoice submission with validation error handling"""
        # Create submission with intentional error
        submission_data = {
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
                "TOTAL_VAT": "159",
                "TOTAL_LEVY": "60",
                "TOTAL_AMOUNT": "3438",
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
                    "ITMREF": "PROD001",
                    "ITMDES": "Product Description",
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
        
        # Valid submission
        submission = InvoiceSubmissionSchema(**submission_data)
        assert submission is not None
        
        # Create error response with validation errors
        error_response = InvoiceErrorResponseSchema(
            error_code="VALIDATION_FAILED",
            message="Validation failed: TOTAL_AMOUNT mismatch",
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            gra_response_code="B16",
            gra_response_message="INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            validation_errors=[
                {
                    "field": "TOTAL_AMOUNT",
                    "error": "B16 - INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
                    "expected": "3438",
                    "actual": "3400"
                }
            ],
            timestamp=datetime.now()
        )
        assert error_response.error_code == "VALIDATION_FAILED"
        assert error_response.gra_response_code == "B16"
        assert len(error_response.validation_errors) == 1
    
    def test_invoice_schemas_with_all_tax_codes(self):
        """Test 3: Invoice items with all valid tax codes (A, B, C, D, E)"""
        tax_codes = ["A", "B", "C", "D", "E"]
        tax_rates = {"A": "0", "B": "15", "C": "0", "D": "0", "E": "3"}
        
        for tax_code in tax_codes:
            item_data = {
                "ITMREF": f"PROD_{tax_code}",
                "ITMDES": f"Product {tax_code}",
                "QUANTITY": "10",
                "UNITYPRICE": "100",
                "TAXCODE": tax_code,
                "TAXRATE": tax_rates[tax_code],
                "LEVY_AMOUNT_A": "0",
                "LEVY_AMOUNT_B": "0",
                "LEVY_AMOUNT_C": "0",
                "LEVY_AMOUNT_D": "0"
            }
            item = InvoiceItemSchema(**item_data)
            assert item.TAXCODE == tax_code
            assert item.TAXRATE == tax_rates[tax_code]
    
    def test_invoice_submission_with_multiple_items_and_flags(self):
        """Test 4: Invoice submissions with different flags (INVOICE, REFUND, PURCHASE)"""
        flags = ["INVOICE", "REFUND", "PURCHASE"]
        
        for flag in flags:
            submission_data = {
                "company": {
                    "COMPANY_NAMES": "ABC COMPANY LTD",
                    "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                    "COMPANY_TIN": "C00XXXXXXXX"
                },
                "header": {
                    "COMPUTATION_TYPE": "INCLUSIVE",
                    "FLAG": flag,
                    "SALE_TYPE": "NORMAL",
                    "USER_NAME": "JOHN",
                    "NUM": f"{flag}-2026-001",
                    "INVOICE_DATE": "2026-02-10",
                    "CURRENCY": "GHS",
                    "EXCHANGE_RATE": "1",
                    "CLIENT_NAME": "Customer Ltd",
                    "TOTAL_VAT": "159",
                    "TOTAL_LEVY": "60",
                    "TOTAL_AMOUNT": "3438",
                    "ITEMS_COUNTS": "1"
                },
                "item_list": [
                    {
                        "ITMREF": "PROD001",
                        "ITMDES": "Product Description",
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
            
            submission = InvoiceSubmissionSchema(**submission_data)
            assert submission.header.FLAG == flag
    
    def test_invoice_response_status_lifecycle(self):
        """Test 5: Invoice response status lifecycle (RECEIVED -> PROCESSING -> PENDING_GRA -> SUCCESS/FAILED)"""
        submission_id = "550e8400-e29b-41d4-a716-446655440000"
        invoice_num = "INV-2026-001"
        now = datetime.now()
        
        # Status 1: RECEIVED
        response_received = InvoiceResponseSchema(
            submission_id=submission_id,
            invoice_num=invoice_num,
            status="RECEIVED",
            submitted_at=now
        )
        assert response_received.status == "RECEIVED"
        assert response_received.completed_at is None
        
        # Status 2: PROCESSING
        response_processing = InvoiceResponseSchema(
            submission_id=submission_id,
            invoice_num=invoice_num,
            status="PROCESSING",
            submitted_at=now
        )
        assert response_processing.status == "PROCESSING"
        
        # Status 3: PENDING_GRA
        response_pending = InvoiceResponseSchema(
            submission_id=submission_id,
            invoice_num=invoice_num,
            status="PENDING_GRA",
            submitted_at=now
        )
        assert response_pending.status == "PENDING_GRA"
        
        # Status 4: SUCCESS
        response_success = InvoiceResponseSchema(
            submission_id=submission_id,
            invoice_num=invoice_num,
            status="SUCCESS",
            gra_invoice_id="GRA-INV-2026-001",
            gra_qr_code="https://gra.gov.gh/qr/abc123def456",
            gra_receipt_num="VSDC-REC-12345",
            submitted_at=now,
            completed_at=now,
            processing_time_ms=5000
        )
        assert response_success.status == "SUCCESS"
        assert response_success.gra_invoice_id is not None
        assert response_success.completed_at is not None
        
        # Status 5: FAILED
        response_failed = InvoiceResponseSchema(
            submission_id=submission_id,
            invoice_num=invoice_num,
            status="FAILED",
            gra_response_code="B16",
            gra_response_message="INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            submitted_at=now,
            completed_at=now
        )
        assert response_failed.status == "FAILED"
        assert response_failed.gra_response_code == "B16"

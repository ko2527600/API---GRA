"""Integration tests for all refund schemas working together"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.refund import (
    RefundHeaderSchema,
    RefundItemSchema,
    RefundSubmissionSchema,
    RefundResponseSchema,
    RefundAcceptedResponseSchema,
    RefundErrorResponseSchema,
    CompanySchema,
    ValidationErrorSchema
)


class TestRefundSchemasIntegration:
    """Integration tests for all refund schemas"""
    
    def test_complete_refund_submission_flow(self):
        """Test 1: Complete refund submission from request to response"""
        submission_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "COMPUTATION_TYPE": "INCLUSIVE",
                "FLAG": "REFUND",
                "SALE_TYPE": "NORMAL",
                "USER_NAME": "JOHN",
                "NUM": "REF-2026-001",
                "ORIGINAL_INVOICE_NUM": "INV-2026-001",
                "REFUND_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "CLIENT_NAME": "Customer Ltd",
                "CLIENT_TIN": "C0022825405",
                "REFUND_REASON": "Defective product",
                "TOTAL_VAT": "79",
                "TOTAL_LEVY": "30",
                "TOTAL_AMOUNT": "1719",
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
                    "ITMREF": "PROD001",
                    "ITMDES": "Product 1",
                    "QUANTITY": "5",
                    "UNITYPRICE": "100",
                    "TAXCODE": "B",
                    "TAXRATE": "15",
                    "LEVY_AMOUNT_A": "1.25",
                    "LEVY_AMOUNT_B": "1.25",
                    "LEVY_AMOUNT_C": "0",
                    "LEVY_AMOUNT_D": "0",
                    "REFUND_REASON_ITEM": "Defective product"
                }
            ]
        }
        
        submission = RefundSubmissionSchema(**submission_data)
        assert submission.company.COMPANY_NAMES == "ABC COMPANY LTD"
        assert submission.header.NUM == "REF-2026-001"
        assert submission.header.ORIGINAL_INVOICE_NUM == "INV-2026-001"
        assert len(submission.item_list) == 1
        
        accepted_response = RefundAcceptedResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            refund_num="REF-2026-001"
        )
        assert accepted_response.status == "RECEIVED"
        assert accepted_response.validation_passed is True
        
        success_response = RefundResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            refund_num="REF-2026-001",
            original_invoice_num="INV-2026-001",
            status="SUCCESS",
            gra_refund_id="GRA-REF-2026-001",
            gra_qr_code="https://gra.gov.gh/qr/ref123def456",
            gra_receipt_num="VSDC-REC-12346",
            submitted_at=datetime.now(),
            completed_at=datetime.now(),
            processing_time_ms=5000
        )
        assert success_response.status == "SUCCESS"
        assert success_response.gra_refund_id == "GRA-REF-2026-001"
        assert success_response.original_invoice_num == "INV-2026-001"
    
    def test_refund_submission_with_validation_error_response(self):
        """Test 2: Refund submission with validation error handling"""
        submission_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "COMPUTATION_TYPE": "INCLUSIVE",
                "FLAG": "REFUND",
                "SALE_TYPE": "NORMAL",
                "USER_NAME": "JOHN",
                "NUM": "REF-2026-001",
                "ORIGINAL_INVOICE_NUM": "INV-2026-001",
                "REFUND_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "CLIENT_NAME": "Customer Ltd",
                "REFUND_REASON": "Defective product",
                "TOTAL_VAT": "79",
                "TOTAL_LEVY": "30",
                "TOTAL_AMOUNT": "1719",
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
                    "ITMREF": "PROD001",
                    "ITMDES": "Product Description",
                    "QUANTITY": "5",
                    "UNITYPRICE": "100",
                    "TAXCODE": "B",
                    "TAXRATE": "15",
                    "LEVY_AMOUNT_A": "1.25",
                    "LEVY_AMOUNT_B": "1.25",
                    "LEVY_AMOUNT_C": "0",
                    "LEVY_AMOUNT_D": "0"
                }
            ]
        }
        
        submission = RefundSubmissionSchema(**submission_data)
        assert submission is not None
        
        error_response = RefundErrorResponseSchema(
            error_code="VALIDATION_FAILED",
            message="Validation failed: TOTAL_AMOUNT mismatch",
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            gra_response_code="B16",
            gra_response_message="REFUND TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            validation_errors=[
                {
                    "field": "TOTAL_AMOUNT",
                    "error": "B16 - REFUND TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
                    "expected": "1719",
                    "actual": "1700"
                }
            ],
            timestamp=datetime.now()
        )
        assert error_response.error_code == "VALIDATION_FAILED"
        assert error_response.gra_response_code == "B16"
        assert len(error_response.validation_errors) == 1
    
    def test_refund_schemas_with_all_tax_codes(self):
        """Test 3: Refund items with all valid tax codes (A, B, C, D, E)"""
        tax_codes = ["A", "B", "C", "D", "E"]
        tax_rates = {"A": "0", "B": "15", "C": "0", "D": "0", "E": "3"}
        
        for tax_code in tax_codes:
            item_data = {
                "ITMREF": f"PROD_{tax_code}",
                "ITMDES": f"Product {tax_code}",
                "QUANTITY": "5",
                "UNITYPRICE": "100",
                "TAXCODE": tax_code,
                "TAXRATE": tax_rates[tax_code],
                "LEVY_AMOUNT_A": "0",
                "LEVY_AMOUNT_B": "0",
                "LEVY_AMOUNT_C": "0",
                "LEVY_AMOUNT_D": "0"
            }
            item = RefundItemSchema(**item_data)
            assert item.TAXCODE == tax_code
            assert item.TAXRATE == tax_rates[tax_code]
    
    def test_refund_submission_with_multiple_items_and_flags(self):
        """Test 4: Refund submissions with different flags (REFUND, PARTIAL_REFUND)"""
        flags = ["REFUND", "PARTIAL_REFUND"]
        
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
                    "ORIGINAL_INVOICE_NUM": "INV-2026-001",
                    "REFUND_DATE": "2026-02-11",
                    "CURRENCY": "GHS",
                    "EXCHANGE_RATE": "1",
                    "CLIENT_NAME": "Customer Ltd",
                    "REFUND_REASON": "Defective product",
                    "TOTAL_VAT": "79",
                    "TOTAL_LEVY": "30",
                    "TOTAL_AMOUNT": "1719",
                    "ITEMS_COUNTS": "1"
                },
                "item_list": [
                    {
                        "ITMREF": "PROD001",
                        "ITMDES": "Product Description",
                        "QUANTITY": "5",
                        "UNITYPRICE": "100",
                        "TAXCODE": "B",
                        "TAXRATE": "15",
                        "LEVY_AMOUNT_A": "1.25",
                        "LEVY_AMOUNT_B": "1.25",
                        "LEVY_AMOUNT_C": "0",
                        "LEVY_AMOUNT_D": "0"
                    }
                ]
            }
            
            submission = RefundSubmissionSchema(**submission_data)
            assert submission.header.FLAG == flag
    
    def test_refund_response_status_lifecycle(self):
        """Test 5: Refund response status lifecycle (RECEIVED -> PROCESSING -> PENDING_GRA -> SUCCESS/FAILED)"""
        submission_id = "550e8400-e29b-41d4-a716-446655440000"
        refund_num = "REF-2026-001"
        original_invoice_num = "INV-2026-001"
        now = datetime.now()
        
        # Status 1: RECEIVED
        response_received = RefundResponseSchema(
            submission_id=submission_id,
            refund_num=refund_num,
            original_invoice_num=original_invoice_num,
            status="RECEIVED",
            submitted_at=now
        )
        assert response_received.status == "RECEIVED"
        assert response_received.completed_at is None
        
        # Status 2: PROCESSING
        response_processing = RefundResponseSchema(
            submission_id=submission_id,
            refund_num=refund_num,
            original_invoice_num=original_invoice_num,
            status="PROCESSING",
            submitted_at=now
        )
        assert response_processing.status == "PROCESSING"
        
        # Status 3: PENDING_GRA
        response_pending = RefundResponseSchema(
            submission_id=submission_id,
            refund_num=refund_num,
            original_invoice_num=original_invoice_num,
            status="PENDING_GRA",
            submitted_at=now
        )
        assert response_pending.status == "PENDING_GRA"
        
        # Status 4: SUCCESS
        response_success = RefundResponseSchema(
            submission_id=submission_id,
            refund_num=refund_num,
            original_invoice_num=original_invoice_num,
            status="SUCCESS",
            gra_refund_id="GRA-REF-2026-001",
            gra_qr_code="https://gra.gov.gh/qr/ref123def456",
            gra_receipt_num="VSDC-REC-12346",
            submitted_at=now,
            completed_at=now,
            processing_time_ms=5000
        )
        assert response_success.status == "SUCCESS"
        assert response_success.gra_refund_id is not None
        assert response_success.completed_at is not None
        
        # Status 5: FAILED
        response_failed = RefundResponseSchema(
            submission_id=submission_id,
            refund_num=refund_num,
            original_invoice_num=original_invoice_num,
            status="FAILED",
            gra_response_code="B16",
            gra_response_message="REFUND TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            submitted_at=now,
            completed_at=now
        )
        assert response_failed.status == "FAILED"
        assert response_failed.gra_response_code == "B16"
    
    def test_refund_submission_with_multiple_items(self):
        """Test 6: Refund submission with multiple items"""
        submission_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "COMPUTATION_TYPE": "INCLUSIVE",
                "FLAG": "REFUND",
                "SALE_TYPE": "NORMAL",
                "USER_NAME": "JOHN",
                "NUM": "REF-2026-002",
                "ORIGINAL_INVOICE_NUM": "INV-2026-002",
                "REFUND_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "CLIENT_NAME": "Customer Ltd",
                "CLIENT_TIN": "C0022825405",
                "REFUND_REASON": "Multiple items defective",
                "TOTAL_VAT": "158",
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
                    "LEVY_AMOUNT_D": "0",
                    "REFUND_REASON_ITEM": "Defective"
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
                    "LEVY_AMOUNT_D": "0",
                    "REFUND_REASON_ITEM": "Defective"
                }
            ]
        }
        
        submission = RefundSubmissionSchema(**submission_data)
        assert len(submission.item_list) == 2
        assert submission.header.ITEMS_COUNTS == "2"
        assert submission.item_list[0].ITMREF == "PROD001"
        assert submission.item_list[1].ITMREF == "PROD002"
    
    def test_refund_item_with_optional_fields(self):
        """Test 7: Refund item with optional fields (discount, category, reason)"""
        item_data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product with discount",
            "QUANTITY": "5",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "1.25",
            "LEVY_AMOUNT_B": "1.25",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0",
            "ITMDISCOUNT": "50",
            "ITEM_CATEGORY": "GOODS",
            "REFUND_REASON_ITEM": "Defective product"
        }
        
        item = RefundItemSchema(**item_data)
        assert item.ITMDISCOUNT == "50"
        assert item.ITEM_CATEGORY == "GOODS"
        assert item.REFUND_REASON_ITEM == "Defective product"
    
    def test_refund_header_with_computation_types(self):
        """Test 8: Refund header with different computation types (INCLUSIVE, EXCLUSIVE)"""
        computation_types = ["INCLUSIVE", "EXCLUSIVE"]
        
        for comp_type in computation_types:
            header_data = {
                "COMPUTATION_TYPE": comp_type,
                "FLAG": "REFUND",
                "SALE_TYPE": "NORMAL",
                "USER_NAME": "JOHN",
                "NUM": f"REF-{comp_type}-001",
                "ORIGINAL_INVOICE_NUM": "INV-2026-001",
                "REFUND_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "CLIENT_NAME": "Customer Ltd",
                "REFUND_REASON": "Defective product",
                "TOTAL_VAT": "79",
                "TOTAL_LEVY": "30",
                "TOTAL_AMOUNT": "1719",
                "ITEMS_COUNTS": "1"
            }
            
            header = RefundHeaderSchema(**header_data)
            assert header.COMPUTATION_TYPE == comp_type
    
    def test_refund_accepted_response_defaults(self):
        """Test 9: Refund accepted response with default values"""
        response = RefundAcceptedResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            refund_num="REF-2026-001"
        )
        
        assert response.status == "RECEIVED"
        assert response.validation_passed is True
        assert response.message == "Refund received and queued for GRA processing"
        assert response.next_action == "Check status using submission_id"
    
    def test_refund_error_response_with_gra_details(self):
        """Test 10: Refund error response with GRA response details"""
        error_response = RefundErrorResponseSchema(
            error_code="AUTH_FAILED",
            message="Authentication failed with GRA",
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            gra_response_code="AUTH001",
            gra_response_message="Invalid security key",
            timestamp=datetime.now()
        )
        
        assert error_response.error_code == "AUTH_FAILED"
        assert error_response.gra_response_code == "AUTH001"
        assert error_response.submission_id is not None

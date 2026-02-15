"""Tests for refund API endpoints"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from app.schemas.refund import (
    RefundSubmissionSchema,
    RefundResponseSchema,
    RefundAcceptedResponseSchema
)


class TestRefundEndpoints:
    """Tests for refund endpoints"""
    
    def test_submit_refund_schema_validation(self):
        """Test 1: Refund submission schema validation"""
        refund_data = {
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
                    "LEVY_AMOUNT_D": "0"
                }
            ]
        }
        
        submission = RefundSubmissionSchema(**refund_data)
        assert submission.company.COMPANY_NAMES == "ABC COMPANY LTD"
        assert submission.header.NUM == "REF-2026-001"
        assert submission.header.ORIGINAL_INVOICE_NUM == "INV-2026-001"
        assert len(submission.item_list) == 1
    
    def test_submit_refund_with_multiple_items(self):
        """Test 2: Submit refund with multiple items"""
        refund_data = {
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
        
        submission = RefundSubmissionSchema(**refund_data)
        assert len(submission.item_list) == 2
        assert submission.header.ITEMS_COUNTS == "2"
    
    def test_refund_accepted_response(self):
        """Test 3: Refund accepted response"""
        response = RefundAcceptedResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            refund_num="REF-2026-001"
        )
        
        assert response.status == "RECEIVED"
        assert response.validation_passed is True
        assert response.refund_num == "REF-2026-001"
    
    def test_refund_response_success(self):
        """Test 4: Refund response for successful submission"""
        now = datetime.now()
        response = RefundResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            refund_num="REF-2026-001",
            original_invoice_num="INV-2026-001",
            status="SUCCESS",
            gra_refund_id="GRA-REF-2026-001",
            gra_qr_code="https://gra.gov.gh/qr/ref123def456",
            gra_receipt_num="VSDC-REC-12346",
            submitted_at=now,
            completed_at=now,
            processing_time_ms=5000
        )
        
        assert response.status == "SUCCESS"
        assert response.gra_refund_id == "GRA-REF-2026-001"
        assert response.original_invoice_num == "INV-2026-001"
        assert response.processing_time_ms == 5000
    
    def test_refund_response_status_lifecycle(self):
        """Test 5: Refund response status lifecycle"""
        submission_id = "550e8400-e29b-41d4-a716-446655440000"
        now = datetime.now()
        
        # RECEIVED status
        response_received = RefundResponseSchema(
            submission_id=submission_id,
            refund_num="REF-2026-001",
            original_invoice_num="INV-2026-001",
            status="RECEIVED",
            submitted_at=now
        )
        assert response_received.status == "RECEIVED"
        
        # PROCESSING status
        response_processing = RefundResponseSchema(
            submission_id=submission_id,
            refund_num="REF-2026-001",
            original_invoice_num="INV-2026-001",
            status="PROCESSING",
            submitted_at=now
        )
        assert response_processing.status == "PROCESSING"
        
        # PENDING_GRA status
        response_pending = RefundResponseSchema(
            submission_id=submission_id,
            refund_num="REF-2026-001",
            original_invoice_num="INV-2026-001",
            status="PENDING_GRA",
            submitted_at=now
        )
        assert response_pending.status == "PENDING_GRA"
        
        # SUCCESS status
        response_success = RefundResponseSchema(
            submission_id=submission_id,
            refund_num="REF-2026-001",
            original_invoice_num="INV-2026-001",
            status="SUCCESS",
            gra_refund_id="GRA-REF-2026-001",
            submitted_at=now,
            completed_at=now
        )
        assert response_success.status == "SUCCESS"
        
        # FAILED status
        response_failed = RefundResponseSchema(
            submission_id=submission_id,
            refund_num="REF-2026-001",
            original_invoice_num="INV-2026-001",
            status="FAILED",
            gra_response_code="B16",
            gra_response_message="REFUND TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            submitted_at=now,
            completed_at=now
        )
        assert response_failed.status == "FAILED"
    
    def test_refund_submission_invalid_tin(self):
        """Test 6: Refund submission with invalid TIN"""
        refund_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "INVALID"  # Invalid TIN
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
                    "LEVY_AMOUNT_D": "0"
                }
            ]
        }
        
        with pytest.raises(ValidationError):
            RefundSubmissionSchema(**refund_data)
    
    def test_refund_submission_item_count_mismatch(self):
        """Test 7: Refund submission with item count mismatch"""
        refund_data = {
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
                "ITEMS_COUNTS": "2"  # Says 2 items
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
                    "LEVY_AMOUNT_D": "0"
                }
                # Only 1 item provided
            ]
        }
        
        with pytest.raises(ValidationError):
            RefundSubmissionSchema(**refund_data)
    
    def test_refund_response_with_gra_error(self):
        """Test 8: Refund response with GRA error"""
        now = datetime.now()
        response = RefundResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            refund_num="REF-2026-001",
            original_invoice_num="INV-2026-001",
            status="FAILED",
            gra_response_code="B16",
            gra_response_message="REFUND TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            submitted_at=now,
            completed_at=now
        )
        
        assert response.status == "FAILED"
        assert response.gra_response_code == "B16"
        assert response.gra_response_message is not None
    
    def test_refund_submission_all_tax_codes(self):
        """Test 9: Refund submission with all tax codes"""
        tax_codes = ["A", "B", "C", "D", "E"]
        tax_rates = {"A": "0", "B": "15", "C": "0", "D": "0", "E": "3"}
        
        for tax_code in tax_codes:
            refund_data = {
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
                    "NUM": f"REF-{tax_code}-001",
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
                        "ITMREF": f"PROD_{tax_code}",
                        "ITMDES": f"Product {tax_code}",
                        "QUANTITY": "5",
                        "UNITYPRICE": "100",
                        "TAXCODE": tax_code,
                        "TAXRATE": tax_rates[tax_code],
                        "LEVY_AMOUNT_A": "1.25",
                        "LEVY_AMOUNT_B": "1.25",
                        "LEVY_AMOUNT_C": "0",
                        "LEVY_AMOUNT_D": "0"
                    }
                ]
            }
            
            submission = RefundSubmissionSchema(**refund_data)
            assert submission.item_list[0].TAXCODE == tax_code
    
    def test_refund_response_processing_time_calculation(self):
        """Test 10: Refund response processing time calculation"""
        submitted_at = datetime.now()
        completed_at = submitted_at + timedelta(seconds=5)
        
        response = RefundResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            refund_num="REF-2026-001",
            original_invoice_num="INV-2026-001",
            status="SUCCESS",
            gra_refund_id="GRA-REF-2026-001",
            submitted_at=submitted_at,
            completed_at=completed_at,
            processing_time_ms=5000
        )
        
        assert response.processing_time_ms == 5000
        assert response.completed_at is not None
    
    def test_refund_submission_partial_refund_flag(self):
        """Test 11: Refund submission with PARTIAL_REFUND flag"""
        refund_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "COMPUTATION_TYPE": "INCLUSIVE",
                "FLAG": "PARTIAL_REFUND",
                "SALE_TYPE": "NORMAL",
                "USER_NAME": "JOHN",
                "NUM": "REF-2026-001",
                "ORIGINAL_INVOICE_NUM": "INV-2026-001",
                "REFUND_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "CLIENT_NAME": "Customer Ltd",
                "CLIENT_TIN": "C0022825405",
                "REFUND_REASON": "Partial refund",
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
                    "LEVY_AMOUNT_D": "0"
                }
            ]
        }
        
        submission = RefundSubmissionSchema(**refund_data)
        assert submission.header.FLAG == "PARTIAL_REFUND"
    
    def test_refund_submission_exclusive_computation(self):
        """Test 12: Refund submission with EXCLUSIVE computation type"""
        refund_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "COMPUTATION_TYPE": "EXCLUSIVE",
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
                    "LEVY_AMOUNT_D": "0"
                }
            ]
        }
        
        submission = RefundSubmissionSchema(**refund_data)
        assert submission.header.COMPUTATION_TYPE == "EXCLUSIVE"

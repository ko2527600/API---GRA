"""Tests for purchase API endpoints"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from app.schemas.purchase import (
    PurchaseSubmissionSchema,
    PurchaseResponseSchema,
    PurchaseAcceptedResponseSchema
)


class TestPurchaseEndpoints:
    """Tests for purchase endpoints"""
    
    def test_submit_purchase_schema_validation(self):
        """Test 1: Purchase submission schema validation"""
        purchase_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "COMPUTATION_TYPE": "INCLUSIVE",
                "FLAG": "PURCHASE",
                "PURCHASE_TYPE": "NORMAL",
                "USER_NAME": "JOHN",
                "NUM": "PUR-2026-001",
                "SUPPLIER_NAME": "Supplier Ltd",
                "SUPPLIER_TIN": "C0022825405",
                "PURCHASE_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "PURCHASE_DESCRIPTION": "Office supplies purchase",
                "TOTAL_VAT": "79",
                "TOTAL_LEVY": "30",
                "TOTAL_AMOUNT": "1719",
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
                    "ITMREF": "SUPP001",
                    "ITMDES": "Office Supplies",
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
        
        submission = PurchaseSubmissionSchema(**purchase_data)
        assert submission.company.COMPANY_NAMES == "ABC COMPANY LTD"
        assert submission.header.NUM == "PUR-2026-001"
        assert submission.header.SUPPLIER_NAME == "Supplier Ltd"
        assert len(submission.item_list) == 1
    
    def test_submit_purchase_with_multiple_items(self):
        """Test 2: Submit purchase with multiple items"""
        purchase_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "COMPUTATION_TYPE": "INCLUSIVE",
                "FLAG": "PURCHASE",
                "PURCHASE_TYPE": "NORMAL",
                "USER_NAME": "JOHN",
                "NUM": "PUR-2026-002",
                "SUPPLIER_NAME": "Supplier Ltd",
                "SUPPLIER_TIN": "C0022825405",
                "PURCHASE_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "PURCHASE_DESCRIPTION": "Multiple items purchase",
                "TOTAL_VAT": "158",
                "TOTAL_LEVY": "60",
                "TOTAL_AMOUNT": "3438",
                "ITEMS_COUNTS": "2"
            },
            "item_list": [
                {
                    "ITMREF": "SUPP001",
                    "ITMDES": "Office Supplies",
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
                    "ITMREF": "SUPP002",
                    "ITMDES": "Equipment",
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
        
        submission = PurchaseSubmissionSchema(**purchase_data)
        assert len(submission.item_list) == 2
        assert submission.header.ITEMS_COUNTS == "2"
    
    def test_purchase_accepted_response(self):
        """Test 3: Purchase accepted response"""
        response = PurchaseAcceptedResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            purchase_num="PUR-2026-001"
        )
        
        assert response.status == "RECEIVED"
        assert response.validation_passed is True
        assert response.purchase_num == "PUR-2026-001"
    
    def test_purchase_response_success(self):
        """Test 4: Purchase response for successful submission"""
        now = datetime.now()
        response = PurchaseResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            purchase_num="PUR-2026-001",
            status="SUCCESS",
            gra_purchase_id="GRA-PUR-2026-001",
            gra_qr_code="https://gra.gov.gh/qr/pur123def456",
            gra_receipt_num="VSDC-REC-12347",
            submitted_at=now,
            completed_at=now,
            processing_time_ms=5000
        )
        
        assert response.status == "SUCCESS"
        assert response.gra_purchase_id == "GRA-PUR-2026-001"
        assert response.processing_time_ms == 5000
    
    def test_purchase_response_status_lifecycle(self):
        """Test 5: Purchase response status lifecycle"""
        submission_id = "550e8400-e29b-41d4-a716-446655440000"
        now = datetime.now()
        
        # RECEIVED status
        response_received = PurchaseResponseSchema(
            submission_id=submission_id,
            purchase_num="PUR-2026-001",
            status="RECEIVED",
            submitted_at=now
        )
        assert response_received.status == "RECEIVED"
        
        # PROCESSING status
        response_processing = PurchaseResponseSchema(
            submission_id=submission_id,
            purchase_num="PUR-2026-001",
            status="PROCESSING",
            submitted_at=now
        )
        assert response_processing.status == "PROCESSING"
        
        # PENDING_GRA status
        response_pending = PurchaseResponseSchema(
            submission_id=submission_id,
            purchase_num="PUR-2026-001",
            status="PENDING_GRA",
            submitted_at=now
        )
        assert response_pending.status == "PENDING_GRA"
        
        # SUCCESS status
        response_success = PurchaseResponseSchema(
            submission_id=submission_id,
            purchase_num="PUR-2026-001",
            status="SUCCESS",
            gra_purchase_id="GRA-PUR-2026-001",
            submitted_at=now,
            completed_at=now
        )
        assert response_success.status == "SUCCESS"
        
        # FAILED status
        response_failed = PurchaseResponseSchema(
            submission_id=submission_id,
            purchase_num="PUR-2026-001",
            status="FAILED",
            gra_response_code="B16",
            gra_response_message="PURCHASE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            submitted_at=now,
            completed_at=now
        )
        assert response_failed.status == "FAILED"
    
    def test_purchase_submission_invalid_tin(self):
        """Test 6: Purchase submission with invalid TIN"""
        purchase_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "INVALID"  # Invalid TIN
            },
            "header": {
                "COMPUTATION_TYPE": "INCLUSIVE",
                "FLAG": "PURCHASE",
                "PURCHASE_TYPE": "NORMAL",
                "USER_NAME": "JOHN",
                "NUM": "PUR-2026-001",
                "SUPPLIER_NAME": "Supplier Ltd",
                "SUPPLIER_TIN": "C0022825405",
                "PURCHASE_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "PURCHASE_DESCRIPTION": "Office supplies purchase",
                "TOTAL_VAT": "79",
                "TOTAL_LEVY": "30",
                "TOTAL_AMOUNT": "1719",
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
                    "ITMREF": "SUPP001",
                    "ITMDES": "Office Supplies",
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
            PurchaseSubmissionSchema(**purchase_data)
    
    def test_purchase_submission_item_count_mismatch(self):
        """Test 7: Purchase submission with item count mismatch"""
        purchase_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "COMPUTATION_TYPE": "INCLUSIVE",
                "FLAG": "PURCHASE",
                "PURCHASE_TYPE": "NORMAL",
                "USER_NAME": "JOHN",
                "NUM": "PUR-2026-001",
                "SUPPLIER_NAME": "Supplier Ltd",
                "SUPPLIER_TIN": "C0022825405",
                "PURCHASE_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "PURCHASE_DESCRIPTION": "Office supplies purchase",
                "TOTAL_VAT": "79",
                "TOTAL_LEVY": "30",
                "TOTAL_AMOUNT": "1719",
                "ITEMS_COUNTS": "2"  # Says 2 items
            },
            "item_list": [
                {
                    "ITMREF": "SUPP001",
                    "ITMDES": "Office Supplies",
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
            PurchaseSubmissionSchema(**purchase_data)
    
    def test_purchase_response_with_gra_error(self):
        """Test 8: Purchase response with GRA error"""
        now = datetime.now()
        response = PurchaseResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            purchase_num="PUR-2026-001",
            status="FAILED",
            gra_response_code="B16",
            gra_response_message="PURCHASE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            submitted_at=now,
            completed_at=now
        )
        
        assert response.status == "FAILED"
        assert response.gra_response_code == "B16"
        assert response.gra_response_message is not None
    
    def test_purchase_submission_all_tax_codes(self):
        """Test 9: Purchase submission with all tax codes"""
        tax_codes = ["A", "B", "C", "D", "E"]
        tax_rates = {"A": "0", "B": "15", "C": "0", "D": "0", "E": "3"}
        
        for tax_code in tax_codes:
            purchase_data = {
                "company": {
                    "COMPANY_NAMES": "ABC COMPANY LTD",
                    "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                    "COMPANY_TIN": "C00XXXXXXXX"
                },
                "header": {
                    "COMPUTATION_TYPE": "INCLUSIVE",
                    "FLAG": "PURCHASE",
                    "PURCHASE_TYPE": "NORMAL",
                    "USER_NAME": "JOHN",
                    "NUM": f"PUR-{tax_code}-001",
                    "SUPPLIER_NAME": "Supplier Ltd",
                    "SUPPLIER_TIN": "C0022825405",
                    "PURCHASE_DATE": "2026-02-11",
                    "CURRENCY": "GHS",
                    "EXCHANGE_RATE": "1",
                    "PURCHASE_DESCRIPTION": "Office supplies purchase",
                    "TOTAL_VAT": "79",
                    "TOTAL_LEVY": "30",
                    "TOTAL_AMOUNT": "1719",
                    "ITEMS_COUNTS": "1"
                },
                "item_list": [
                    {
                        "ITMREF": f"SUPP_{tax_code}",
                        "ITMDES": f"Supplies {tax_code}",
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
            
            submission = PurchaseSubmissionSchema(**purchase_data)
            assert submission.item_list[0].TAXCODE == tax_code
    
    def test_purchase_response_processing_time_calculation(self):
        """Test 10: Purchase response processing time calculation"""
        submitted_at = datetime.now()
        completed_at = submitted_at + timedelta(seconds=5)
        
        response = PurchaseResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            purchase_num="PUR-2026-001",
            status="SUCCESS",
            gra_purchase_id="GRA-PUR-2026-001",
            submitted_at=submitted_at,
            completed_at=completed_at,
            processing_time_ms=5000
        )
        
        assert response.processing_time_ms == 5000
        assert response.completed_at is not None
    
    def test_purchase_submission_credit_purchase_type(self):
        """Test 11: Purchase submission with CREDIT_PURCHASE type"""
        purchase_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "COMPUTATION_TYPE": "INCLUSIVE",
                "FLAG": "PURCHASE",
                "PURCHASE_TYPE": "CREDIT_PURCHASE",
                "USER_NAME": "JOHN",
                "NUM": "PUR-2026-001",
                "SUPPLIER_NAME": "Supplier Ltd",
                "SUPPLIER_TIN": "C0022825405",
                "PURCHASE_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "PURCHASE_DESCRIPTION": "Credit purchase",
                "TOTAL_VAT": "79",
                "TOTAL_LEVY": "30",
                "TOTAL_AMOUNT": "1719",
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
                    "ITMREF": "SUPP001",
                    "ITMDES": "Office Supplies",
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
        
        submission = PurchaseSubmissionSchema(**purchase_data)
        assert submission.header.PURCHASE_TYPE == "CREDIT_PURCHASE"
    
    def test_purchase_submission_exclusive_computation(self):
        """Test 12: Purchase submission with EXCLUSIVE computation type"""
        purchase_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "COMPUTATION_TYPE": "EXCLUSIVE",
                "FLAG": "PURCHASE",
                "PURCHASE_TYPE": "NORMAL",
                "USER_NAME": "JOHN",
                "NUM": "PUR-2026-001",
                "SUPPLIER_NAME": "Supplier Ltd",
                "SUPPLIER_TIN": "C0022825405",
                "PURCHASE_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "PURCHASE_DESCRIPTION": "Office supplies purchase",
                "TOTAL_VAT": "79",
                "TOTAL_LEVY": "30",
                "TOTAL_AMOUNT": "1719",
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
                    "ITMREF": "SUPP001",
                    "ITMDES": "Office Supplies",
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
        
        submission = PurchaseSubmissionSchema(**purchase_data)
        assert submission.header.COMPUTATION_TYPE == "EXCLUSIVE"


class TestPurchaseCancellation:
    """Tests for purchase cancellation endpoint"""
    
    def test_purchase_cancellation_schema_validation(self):
        """Test 1: Purchase cancellation schema validation"""
        from app.schemas.purchase import PurchaseCancellationRequestSchema
        
        cancellation_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "FLAG": "CANCEL",
                "NUM": "PUR-2026-001",
                "PURCHASE_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1"
            }
        }
        
        cancellation = PurchaseCancellationRequestSchema(**cancellation_data)
        assert cancellation.company.COMPANY_NAMES == "ABC COMPANY LTD"
        assert cancellation.header.FLAG == "CANCEL"
        assert cancellation.header.NUM == "PUR-2026-001"
    
    def test_purchase_cancellation_invalid_flag(self):
        """Test 2: Purchase cancellation with invalid flag"""
        from app.schemas.purchase import PurchaseCancellationRequestSchema
        
        cancellation_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "FLAG": "PURCHASE",  # Invalid flag for cancellation
                "NUM": "PUR-2026-001",
                "PURCHASE_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1"
            }
        }
        
        with pytest.raises(ValidationError):
            PurchaseCancellationRequestSchema(**cancellation_data)
    
    def test_purchase_cancellation_invalid_currency(self):
        """Test 3: Purchase cancellation with invalid currency"""
        from app.schemas.purchase import PurchaseCancellationRequestSchema
        
        cancellation_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "FLAG": "CANCEL",
                "NUM": "PUR-2026-001",
                "PURCHASE_DATE": "2026-02-11",
                "CURRENCY": "USD",  # Invalid currency
                "EXCHANGE_RATE": "1"
            }
        }
        
        with pytest.raises(ValidationError):
            PurchaseCancellationRequestSchema(**cancellation_data)
    
    def test_purchase_cancellation_invalid_exchange_rate(self):
        """Test 4: Purchase cancellation with invalid exchange rate"""
        from app.schemas.purchase import PurchaseCancellationRequestSchema
        
        cancellation_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "FLAG": "CANCEL",
                "NUM": "PUR-2026-001",
                "PURCHASE_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "2"  # Invalid exchange rate for GHS
            }
        }
        
        with pytest.raises(ValidationError):
            PurchaseCancellationRequestSchema(**cancellation_data)
    
    def test_purchase_cancellation_response(self):
        """Test 5: Purchase cancellation response"""
        from app.schemas.purchase import PurchaseCancellationResponseSchema
        
        now = datetime.now()
        response = PurchaseCancellationResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            purchase_num="PUR-2026-001",
            status="RECEIVED",
            submitted_at=now
        )
        
        assert response.submission_id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.purchase_num == "PUR-2026-001"
        assert response.status == "RECEIVED"
    
    def test_purchase_cancellation_response_success(self):
        """Test 6: Purchase cancellation response with success status"""
        from app.schemas.purchase import PurchaseCancellationResponseSchema
        
        now = datetime.now()
        response = PurchaseCancellationResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            purchase_num="PUR-2026-001",
            status="SUCCESS",
            submitted_at=now,
            completed_at=now,
            processing_time_ms=3000
        )
        
        assert response.status == "SUCCESS"
        assert response.processing_time_ms == 3000
    
    def test_purchase_cancellation_response_failed(self):
        """Test 7: Purchase cancellation response with failed status"""
        from app.schemas.purchase import PurchaseCancellationResponseSchema
        
        now = datetime.now()
        response = PurchaseCancellationResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            purchase_num="PUR-2026-001",
            status="FAILED",
            gra_response_code="D01",
            gra_response_message="Purchase not found",
            submitted_at=now,
            completed_at=now
        )
        
        assert response.status == "FAILED"
        assert response.gra_response_code == "D01"
    
    def test_purchase_cancellation_response_status_lifecycle(self):
        """Test 8: Purchase cancellation response status lifecycle"""
        from app.schemas.purchase import PurchaseCancellationResponseSchema
        
        submission_id = "550e8400-e29b-41d4-a716-446655440000"
        now = datetime.now()
        
        # RECEIVED status
        response_received = PurchaseCancellationResponseSchema(
            submission_id=submission_id,
            purchase_num="PUR-2026-001",
            status="RECEIVED",
            submitted_at=now
        )
        assert response_received.status == "RECEIVED"
        
        # PROCESSING status
        response_processing = PurchaseCancellationResponseSchema(
            submission_id=submission_id,
            purchase_num="PUR-2026-001",
            status="PROCESSING",
            submitted_at=now
        )
        assert response_processing.status == "PROCESSING"
        
        # PENDING_GRA status
        response_pending = PurchaseCancellationResponseSchema(
            submission_id=submission_id,
            purchase_num="PUR-2026-001",
            status="PENDING_GRA",
            submitted_at=now
        )
        assert response_pending.status == "PENDING_GRA"
        
        # SUCCESS status
        response_success = PurchaseCancellationResponseSchema(
            submission_id=submission_id,
            purchase_num="PUR-2026-001",
            status="SUCCESS",
            submitted_at=now,
            completed_at=now
        )
        assert response_success.status == "SUCCESS"
        
        # FAILED status
        response_failed = PurchaseCancellationResponseSchema(
            submission_id=submission_id,
            purchase_num="PUR-2026-001",
            status="FAILED",
            gra_response_code="D01",
            submitted_at=now,
            completed_at=now
        )
        assert response_failed.status == "FAILED"
    
    def test_purchase_cancellation_invalid_date_format(self):
        """Test 9: Purchase cancellation with invalid date format"""
        from app.schemas.purchase import PurchaseCancellationRequestSchema
        
        cancellation_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "FLAG": "CANCEL",
                "NUM": "PUR-2026-001",
                "PURCHASE_DATE": "11-02-2026",  # Invalid date format
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1"
            }
        }
        
        with pytest.raises(ValidationError):
            PurchaseCancellationRequestSchema(**cancellation_data)
    
    def test_purchase_cancellation_missing_purchase_number(self):
        """Test 10: Purchase cancellation with missing purchase number"""
        from app.schemas.purchase import PurchaseCancellationRequestSchema
        
        cancellation_data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "FLAG": "CANCEL",
                # NUM is missing
                "PURCHASE_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1"
            }
        }
        
        with pytest.raises(ValidationError):
            PurchaseCancellationRequestSchema(**cancellation_data)

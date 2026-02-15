"""Integration tests for all purchase schemas working together"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.purchase import (
    PurchaseHeaderSchema,
    PurchaseItemSchema,
    PurchaseSubmissionSchema,
    PurchaseResponseSchema,
    PurchaseAcceptedResponseSchema,
    PurchaseErrorResponseSchema,
    CompanySchema,
    ValidationErrorSchema
)


class TestPurchaseSchemasIntegration:
    """Integration tests for all purchase schemas"""
    
    def test_complete_purchase_submission_flow(self):
        """Test 1: Complete purchase submission from request to response"""
        submission_data = {
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
                    "LEVY_AMOUNT_D": "0",
                    "PURCHASE_NOTE": "Bulk order"
                }
            ]
        }
        
        submission = PurchaseSubmissionSchema(**submission_data)
        assert submission.company.COMPANY_NAMES == "ABC COMPANY LTD"
        assert submission.header.NUM == "PUR-2026-001"
        assert submission.header.SUPPLIER_NAME == "Supplier Ltd"
        assert len(submission.item_list) == 1
        
        accepted_response = PurchaseAcceptedResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            purchase_num="PUR-2026-001"
        )
        assert accepted_response.status == "RECEIVED"
        assert accepted_response.validation_passed is True
        
        success_response = PurchaseResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            purchase_num="PUR-2026-001",
            status="SUCCESS",
            gra_purchase_id="GRA-PUR-2026-001",
            gra_qr_code="https://gra.gov.gh/qr/pur123def456",
            gra_receipt_num="VSDC-REC-12347",
            submitted_at=datetime.now(),
            completed_at=datetime.now(),
            processing_time_ms=5000
        )
        assert success_response.status == "SUCCESS"
        assert success_response.gra_purchase_id == "GRA-PUR-2026-001"
    
    def test_purchase_submission_with_validation_error_response(self):
        """Test 2: Purchase submission with validation error handling"""
        submission_data = {
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
        
        submission = PurchaseSubmissionSchema(**submission_data)
        assert submission is not None
        
        error_response = PurchaseErrorResponseSchema(
            error_code="VALIDATION_FAILED",
            message="Validation failed: TOTAL_AMOUNT mismatch",
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            gra_response_code="B16",
            gra_response_message="PURCHASE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            validation_errors=[
                {
                    "field": "TOTAL_AMOUNT",
                    "error": "B16 - PURCHASE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
                    "expected": "1719",
                    "actual": "1700"
                }
            ],
            timestamp=datetime.now()
        )
        assert error_response.error_code == "VALIDATION_FAILED"
        assert error_response.gra_response_code == "B16"
        assert len(error_response.validation_errors) == 1
    
    def test_purchase_schemas_with_all_tax_codes(self):
        """Test 3: Purchase items with all valid tax codes (A, B, C, D, E)"""
        tax_codes = ["A", "B", "C", "D", "E"]
        tax_rates = {"A": "0", "B": "15", "C": "0", "D": "0", "E": "3"}
        
        for tax_code in tax_codes:
            item_data = {
                "ITMREF": f"SUPP_{tax_code}",
                "ITMDES": f"Supplies {tax_code}",
                "QUANTITY": "5",
                "UNITYPRICE": "100",
                "TAXCODE": tax_code,
                "TAXRATE": tax_rates[tax_code],
                "LEVY_AMOUNT_A": "0",
                "LEVY_AMOUNT_B": "0",
                "LEVY_AMOUNT_C": "0",
                "LEVY_AMOUNT_D": "0"
            }
            item = PurchaseItemSchema(**item_data)
            assert item.TAXCODE == tax_code
            assert item.TAXRATE == tax_rates[tax_code]
    
    def test_purchase_submission_with_multiple_items_and_types(self):
        """Test 4: Purchase submissions with different purchase types (NORMAL, CREDIT_PURCHASE)"""
        purchase_types = ["NORMAL", "CREDIT_PURCHASE"]
        
        for purchase_type in purchase_types:
            submission_data = {
                "company": {
                    "COMPANY_NAMES": "ABC COMPANY LTD",
                    "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                    "COMPANY_TIN": "C00XXXXXXXX"
                },
                "header": {
                    "COMPUTATION_TYPE": "INCLUSIVE",
                    "FLAG": "PURCHASE",
                    "PURCHASE_TYPE": purchase_type,
                    "USER_NAME": "JOHN",
                    "NUM": f"{purchase_type}-2026-001",
                    "SUPPLIER_NAME": "Supplier Ltd",
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
            
            submission = PurchaseSubmissionSchema(**submission_data)
            assert submission.header.PURCHASE_TYPE == purchase_type
    
    def test_purchase_response_status_lifecycle(self):
        """Test 5: Purchase response status lifecycle (RECEIVED -> PROCESSING -> PENDING_GRA -> SUCCESS/FAILED)"""
        submission_id = "550e8400-e29b-41d4-a716-446655440000"
        purchase_num = "PUR-2026-001"
        now = datetime.now()
        
        # Status 1: RECEIVED
        response_received = PurchaseResponseSchema(
            submission_id=submission_id,
            purchase_num=purchase_num,
            status="RECEIVED",
            submitted_at=now
        )
        assert response_received.status == "RECEIVED"
        assert response_received.completed_at is None
        
        # Status 2: PROCESSING
        response_processing = PurchaseResponseSchema(
            submission_id=submission_id,
            purchase_num=purchase_num,
            status="PROCESSING",
            submitted_at=now
        )
        assert response_processing.status == "PROCESSING"
        
        # Status 3: PENDING_GRA
        response_pending = PurchaseResponseSchema(
            submission_id=submission_id,
            purchase_num=purchase_num,
            status="PENDING_GRA",
            submitted_at=now
        )
        assert response_pending.status == "PENDING_GRA"
        
        # Status 4: SUCCESS
        response_success = PurchaseResponseSchema(
            submission_id=submission_id,
            purchase_num=purchase_num,
            status="SUCCESS",
            gra_purchase_id="GRA-PUR-2026-001",
            gra_qr_code="https://gra.gov.gh/qr/pur123def456",
            gra_receipt_num="VSDC-REC-12347",
            submitted_at=now,
            completed_at=now,
            processing_time_ms=5000
        )
        assert response_success.status == "SUCCESS"
        assert response_success.gra_purchase_id is not None
        assert response_success.completed_at is not None
        
        # Status 5: FAILED
        response_failed = PurchaseResponseSchema(
            submission_id=submission_id,
            purchase_num=purchase_num,
            status="FAILED",
            gra_response_code="B16",
            gra_response_message="PURCHASE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
            submitted_at=now,
            completed_at=now
        )
        assert response_failed.status == "FAILED"
        assert response_failed.gra_response_code == "B16"
    
    def test_purchase_submission_with_multiple_items(self):
        """Test 6: Purchase submission with multiple items"""
        submission_data = {
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
        
        submission = PurchaseSubmissionSchema(**submission_data)
        assert len(submission.item_list) == 2
        assert submission.header.ITEMS_COUNTS == "2"
        assert submission.item_list[0].ITMREF == "SUPP001"
        assert submission.item_list[1].ITMREF == "SUPP002"
    
    def test_purchase_item_with_optional_fields(self):
        """Test 7: Purchase item with optional fields (discount, category, note)"""
        item_data = {
            "ITMREF": "SUPP001",
            "ITMDES": "Office Supplies with discount",
            "QUANTITY": "5",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "1.25",
            "LEVY_AMOUNT_B": "1.25",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0",
            "ITMDISCOUNT": "50",
            "ITEM_CATEGORY": "SUPPLIES",
            "PURCHASE_NOTE": "Bulk order discount applied"
        }
        
        item = PurchaseItemSchema(**item_data)
        assert item.ITMDISCOUNT == "50"
        assert item.ITEM_CATEGORY == "SUPPLIES"
        assert item.PURCHASE_NOTE == "Bulk order discount applied"
    
    def test_purchase_header_with_computation_types(self):
        """Test 8: Purchase header with different computation types (INCLUSIVE, EXCLUSIVE)"""
        computation_types = ["INCLUSIVE", "EXCLUSIVE"]
        
        for comp_type in computation_types:
            header_data = {
                "COMPUTATION_TYPE": comp_type,
                "FLAG": "PURCHASE",
                "PURCHASE_TYPE": "NORMAL",
                "USER_NAME": "JOHN",
                "NUM": f"PUR-{comp_type}-001",
                "SUPPLIER_NAME": "Supplier Ltd",
                "PURCHASE_DATE": "2026-02-11",
                "CURRENCY": "GHS",
                "EXCHANGE_RATE": "1",
                "PURCHASE_DESCRIPTION": "Office supplies purchase",
                "TOTAL_VAT": "79",
                "TOTAL_LEVY": "30",
                "TOTAL_AMOUNT": "1719",
                "ITEMS_COUNTS": "1"
            }
            
            header = PurchaseHeaderSchema(**header_data)
            assert header.COMPUTATION_TYPE == comp_type
    
    def test_purchase_accepted_response_defaults(self):
        """Test 9: Purchase accepted response with default values"""
        response = PurchaseAcceptedResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            purchase_num="PUR-2026-001"
        )
        
        assert response.status == "RECEIVED"
        assert response.validation_passed is True
        assert response.message == "Purchase received and queued for GRA processing"
        assert response.next_action == "Check status using submission_id"
    
    def test_purchase_error_response_with_gra_details(self):
        """Test 10: Purchase error response with GRA response details"""
        error_response = PurchaseErrorResponseSchema(
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

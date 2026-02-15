"""Integration tests for all item and inventory schemas working together"""
import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from app.schemas.item import (
    ItemRegistrationSchema,
    ItemRegistrationResponseSchema,
    InventoryUpdateSchema,
    InventoryUpdateResponseSchema,
    TINValidationSchema,
    TINValidationResponseSchema,
    TagDescriptionSchema,
    TagDescriptionResponseSchema,
    ItemErrorResponseSchema
)


class TestItemSchemasIntegration:
    """Integration tests for all item and inventory schemas"""
    
    def test_item_registration_complete_flow(self):
        """Test 1: Complete item registration flow"""
        registration_data = {
            "ITEM_REF": "PROD001",
            "ITEM_DESCRIPTION": "Office Chair",
            "ITEM_CATEGORY": "GOODS",
            "UNIT_OF_MEASURE": "PIECES",
            "TAX_CODE": "B",
            "TAX_RATE": "15",
            "STANDARD_PRICE": "250.00",
            "COMPANY_TIN": "C00XXXXXXXX",
            "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
        }
        
        registration = ItemRegistrationSchema(**registration_data)
        assert registration.ITEM_REF == "PROD001"
        assert registration.ITEM_DESCRIPTION == "Office Chair"
        assert registration.TAX_CODE == "B"
        assert registration.TAX_RATE == "15"
        
        response = ItemRegistrationResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            item_ref="PROD001",
            status="SUCCESS",
            gra_item_id="GRA-ITEM-001",
            submitted_at=datetime.now(),
            completed_at=datetime.now()
        )
        assert response.status == "SUCCESS"
        assert response.gra_item_id == "GRA-ITEM-001"
    
    def test_item_registration_with_all_tax_codes(self):
        """Test 2: Item registration with all valid tax codes"""
        tax_codes = ["A", "B", "C", "D", "E"]
        tax_rates = {"A": "0", "B": "15", "C": "0", "D": "0", "E": "3"}
        
        for tax_code in tax_codes:
            registration_data = {
                "ITEM_REF": f"PROD_{tax_code}",
                "ITEM_DESCRIPTION": f"Product {tax_code}",
                "ITEM_CATEGORY": "GOODS",
                "UNIT_OF_MEASURE": "PIECES",
                "TAX_CODE": tax_code,
                "TAX_RATE": tax_rates[tax_code],
                "STANDARD_PRICE": "100.00",
                "COMPANY_TIN": "C00XXXXXXXX",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
            }
            
            registration = ItemRegistrationSchema(**registration_data)
            assert registration.TAX_CODE == tax_code
            assert registration.TAX_RATE == tax_rates[tax_code]
    
    def test_inventory_update_all_operation_types(self):
        """Test 3: Inventory updates with all operation types (IN, OUT, ADJUSTMENT, RETURN)"""
        operation_types = ["IN", "OUT", "ADJUSTMENT", "RETURN"]
        
        for op_type in operation_types:
            update_data = {
                "ITEM_REF": "PROD001",
                "QUANTITY_CHANGE": "50" if op_type in ["IN", "ADJUSTMENT"] else "-30",
                "OPERATION_TYPE": op_type,
                "REFERENCE_NUM": f"REF-{op_type}-001",
                "NOTES": f"Stock {op_type} operation",
                "COMPANY_TIN": "C00XXXXXXXX"
            }
            
            update = InventoryUpdateSchema(**update_data)
            assert update.OPERATION_TYPE == op_type
            
            response = InventoryUpdateResponseSchema(
                submission_id="550e8400-e29b-41d4-a716-446655440000",
                item_ref="PROD001",
                status="SUCCESS",
                previous_quantity="100",
                new_quantity="150" if op_type in ["IN", "ADJUSTMENT"] else "70",
                updated_at=datetime.now()
            )
            assert response.status == "SUCCESS"
    
    def test_inventory_update_with_negative_quantity(self):
        """Test 4: Inventory update with negative quantity change"""
        update_data = {
            "ITEM_REF": "PROD001",
            "QUANTITY_CHANGE": "-25",
            "OPERATION_TYPE": "OUT",
            "REFERENCE_NUM": "INV-2026-001",
            "NOTES": "Stock sold",
            "COMPANY_TIN": "C00XXXXXXXX"
        }
        
        update = InventoryUpdateSchema(**update_data)
        assert update.QUANTITY_CHANGE == "-25"
        assert update.OPERATION_TYPE == "OUT"
    
    def test_tin_validation_company_tin(self):
        """Test 5: TIN validation for company TIN"""
        validation_data = {
            "TIN": "C0022825405",
            "TIN_TYPE": "COMPANY"
        }
        
        validation = TINValidationSchema(**validation_data)
        assert validation.TIN == "C0022825405"
        assert validation.TIN_TYPE == "COMPANY"
        
        response = TINValidationResponseSchema(
            tin="C0022825405",
            is_valid=True,
            tin_type="COMPANY",
            entity_name="ABC COMPANY LTD",
            registration_status="ACTIVE",
            cached=False,
            validated_at=datetime.now()
        )
        assert response.is_valid is True
        assert response.entity_name == "ABC COMPANY LTD"
    
    def test_tin_validation_individual_tin(self):
        """Test 6: TIN validation for individual TIN"""
        validation_data = {
            "TIN": "P0022825405",
            "TIN_TYPE": "INDIVIDUAL"
        }
        
        validation = TINValidationSchema(**validation_data)
        assert validation.TIN == "P0022825405"
        assert validation.TIN_TYPE == "INDIVIDUAL"
    
    def test_tin_validation_cached_response(self):
        """Test 7: TIN validation with cached response"""
        response = TINValidationResponseSchema(
            tin="C0022825405",
            is_valid=True,
            tin_type="COMPANY",
            entity_name="ABC COMPANY LTD",
            registration_status="ACTIVE",
            cached=True,
            cache_expires_at=datetime.now() + timedelta(hours=24),
            validated_at=datetime.now()
        )
        
        assert response.cached is True
        assert response.cache_expires_at is not None
    
    def test_tag_description_registration(self):
        """Test 8: Tag description registration"""
        tag_data = {
            "TAG_CODE": "TAG001",
            "TAG_DESCRIPTION": "Premium Product",
            "TAG_CATEGORY": "PRODUCT_TYPE",
            "COMPANY_TIN": "C00XXXXXXXX",
            "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
        }
        
        tag = TagDescriptionSchema(**tag_data)
        assert tag.TAG_CODE == "TAG001"
        assert tag.TAG_DESCRIPTION == "Premium Product"
        
        response = TagDescriptionResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            tag_code="TAG001",
            status="SUCCESS",
            gra_tag_id="GRA-TAG-001",
            submitted_at=datetime.now(),
            completed_at=datetime.now()
        )
        assert response.status == "SUCCESS"
        assert response.gra_tag_id == "GRA-TAG-001"
    
    def test_item_error_response_validation_failed(self):
        """Test 9: Item error response for validation failure"""
        error_response = ItemErrorResponseSchema(
            error_code="VALIDATION_FAILED",
            message="Item reference already exists",
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            gra_response_code="ITEM001",
            gra_response_message="Duplicate item reference",
            timestamp=datetime.now()
        )
        
        assert error_response.error_code == "VALIDATION_FAILED"
        assert error_response.gra_response_code == "ITEM001"
    
    def test_item_error_response_auth_failed(self):
        """Test 10: Item error response for authentication failure"""
        error_response = ItemErrorResponseSchema(
            error_code="AUTH_FAILED",
            message="Invalid security key",
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            gra_response_code="AUTH001",
            gra_response_message="Security key validation failed",
            timestamp=datetime.now()
        )
        
        assert error_response.error_code == "AUTH_FAILED"
        assert error_response.gra_response_code == "AUTH001"
    
    def test_item_registration_status_lifecycle(self):
        """Test 11: Item registration status lifecycle"""
        submission_id = "550e8400-e29b-41d4-a716-446655440000"
        now = datetime.now()
        
        # Status 1: RECEIVED
        response_received = ItemRegistrationResponseSchema(
            submission_id=submission_id,
            item_ref="PROD001",
            status="RECEIVED",
            submitted_at=now
        )
        assert response_received.status == "RECEIVED"
        assert response_received.completed_at is None
        
        # Status 2: PROCESSING
        response_processing = ItemRegistrationResponseSchema(
            submission_id=submission_id,
            item_ref="PROD001",
            status="PROCESSING",
            submitted_at=now
        )
        assert response_processing.status == "PROCESSING"
        
        # Status 3: SUCCESS
        response_success = ItemRegistrationResponseSchema(
            submission_id=submission_id,
            item_ref="PROD001",
            status="SUCCESS",
            gra_item_id="GRA-ITEM-001",
            submitted_at=now,
            completed_at=now
        )
        assert response_success.status == "SUCCESS"
        assert response_success.gra_item_id is not None
        
        # Status 4: FAILED
        response_failed = ItemRegistrationResponseSchema(
            submission_id=submission_id,
            item_ref="PROD001",
            status="FAILED",
            gra_response_code="ITEM001",
            gra_response_message="Item registration failed",
            submitted_at=now,
            completed_at=now
        )
        assert response_failed.status == "FAILED"
        assert response_failed.gra_response_code == "ITEM001"
    
    def test_inventory_update_response_with_quantities(self):
        """Test 12: Inventory update response with quantity tracking"""
        response = InventoryUpdateResponseSchema(
            submission_id="550e8400-e29b-41d4-a716-446655440000",
            item_ref="PROD001",
            status="SUCCESS",
            previous_quantity="100.50",
            new_quantity="150.75",
            updated_at=datetime.now()
        )
        
        assert response.previous_quantity == "100.50"
        assert response.new_quantity == "150.75"
        assert response.status == "SUCCESS"
    
    def test_tag_description_response_status_lifecycle(self):
        """Test 13: Tag description response status lifecycle"""
        submission_id = "550e8400-e29b-41d4-a716-446655440000"
        now = datetime.now()
        
        # Status 1: RECEIVED
        response_received = TagDescriptionResponseSchema(
            submission_id=submission_id,
            tag_code="TAG001",
            status="RECEIVED",
            submitted_at=now
        )
        assert response_received.status == "RECEIVED"
        
        # Status 2: SUCCESS
        response_success = TagDescriptionResponseSchema(
            submission_id=submission_id,
            tag_code="TAG001",
            status="SUCCESS",
            gra_tag_id="GRA-TAG-001",
            submitted_at=now,
            completed_at=now
        )
        assert response_success.status == "SUCCESS"
        assert response_success.gra_tag_id == "GRA-TAG-001"
    
    def test_tin_validation_invalid_tin(self):
        """Test 14: TIN validation with invalid result"""
        response = TINValidationResponseSchema(
            tin="INVALID123",
            is_valid=False,
            tin_type="COMPANY",
            gra_response_code="TIN001",
            gra_response_message="TIN not found in GRA database",
            cached=False,
            validated_at=datetime.now()
        )
        
        assert response.is_valid is False
        assert response.entity_name is None
    
    def test_item_registration_with_long_description(self):
        """Test 15: Item registration with maximum length description"""
        registration_data = {
            "ITEM_REF": "PROD001",
            "ITEM_DESCRIPTION": "A" * 500,  # Maximum length
            "ITEM_CATEGORY": "GOODS",
            "UNIT_OF_MEASURE": "PIECES",
            "TAX_CODE": "B",
            "TAX_RATE": "15",
            "STANDARD_PRICE": "100.00",
            "COMPANY_TIN": "C00XXXXXXXX",
            "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
        }
        
        registration = ItemRegistrationSchema(**registration_data)
        assert len(registration.ITEM_DESCRIPTION) == 500

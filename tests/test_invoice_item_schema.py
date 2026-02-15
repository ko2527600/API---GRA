"""Tests for InvoiceItemSchema"""
import pytest
from pydantic import ValidationError
from app.schemas.invoice import InvoiceItemSchema, InvoiceItemResponseSchema
from datetime import datetime


class TestInvoiceItemSchemaValidation:
    """Test InvoiceItemSchema validation"""
    
    def test_valid_invoice_item_minimal(self):
        """Test creating a valid invoice item with minimal fields"""
        data = {
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
        schema = InvoiceItemSchema(**data)
        assert schema.ITMREF == "PROD001"
        assert schema.ITMDES == "Product Description"
        assert schema.QUANTITY == "10"
        assert schema.UNITYPRICE == "100"
        assert schema.TAXCODE == "B"
        assert schema.TAXRATE == "15"
    
    def test_valid_invoice_item_with_all_fields(self):
        """Test creating a valid invoice item with all fields"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "QUANTITY": "10",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0",
            "ITMDISCOUNT": "5.00",
            "ITEM_CATEGORY": "GOODS",
            "BATCH": "BATCH001",
            "EXPIRE": "2026-12-31"
        }
        schema = InvoiceItemSchema(**data)
        assert schema.ITMDISCOUNT == "5.00"
        assert schema.ITEM_CATEGORY == "GOODS"
        assert schema.BATCH == "BATCH001"
        assert schema.EXPIRE == "2026-12-31"
    
    def test_valid_invoice_item_tax_code_a(self):
        """Test invoice item with TAX_CODE A (Exempted)"""
        data = {
            "ITMREF": "PROD002",
            "ITMDES": "Exempted Product",
            "QUANTITY": "5",
            "UNITYPRICE": "50",
            "TAXCODE": "A",
            "TAXRATE": "0",
            "LEVY_AMOUNT_A": "0",
            "LEVY_AMOUNT_B": "0",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        schema = InvoiceItemSchema(**data)
        assert schema.TAXCODE == "A"
        assert schema.TAXRATE == "0"
    
    def test_valid_invoice_item_tax_code_c(self):
        """Test invoice item with TAX_CODE C (Export)"""
        data = {
            "ITMREF": "PROD003",
            "ITMDES": "Export Product",
            "QUANTITY": "20",
            "UNITYPRICE": "200",
            "TAXCODE": "C",
            "TAXRATE": "0",
            "LEVY_AMOUNT_A": "0",
            "LEVY_AMOUNT_B": "0",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        schema = InvoiceItemSchema(**data)
        assert schema.TAXCODE == "C"
    
    def test_valid_invoice_item_tax_code_d(self):
        """Test invoice item with TAX_CODE D (Non-Taxable)"""
        data = {
            "ITMREF": "PROD004",
            "ITMDES": "Non-Taxable Product",
            "QUANTITY": "15",
            "UNITYPRICE": "75",
            "TAXCODE": "D",
            "TAXRATE": "0",
            "LEVY_AMOUNT_A": "0",
            "LEVY_AMOUNT_B": "0",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        schema = InvoiceItemSchema(**data)
        assert schema.TAXCODE == "D"
    
    def test_valid_invoice_item_tax_code_e(self):
        """Test invoice item with TAX_CODE E (Non-VAT)"""
        data = {
            "ITMREF": "PROD005",
            "ITMDES": "Non-VAT Product",
            "QUANTITY": "8",
            "UNITYPRICE": "120",
            "TAXCODE": "E",
            "TAXRATE": "3",
            "LEVY_AMOUNT_A": "0",
            "LEVY_AMOUNT_B": "0",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        schema = InvoiceItemSchema(**data)
        assert schema.TAXCODE == "E"
        assert schema.TAXRATE == "3"
    
    def test_valid_invoice_item_decimal_quantities(self):
        """Test invoice item with decimal quantities"""
        data = {
            "ITMREF": "PROD006",
            "ITMDES": "Decimal Quantity Product",
            "QUANTITY": "10.50",
            "UNITYPRICE": "100.75",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        schema = InvoiceItemSchema(**data)
        assert schema.QUANTITY == "10.50"
        assert schema.UNITYPRICE == "100.75"
    
    def test_valid_invoice_item_zero_levies(self):
        """Test invoice item with zero levies"""
        data = {
            "ITMREF": "PROD007",
            "ITMDES": "Zero Levy Product",
            "QUANTITY": "5",
            "UNITYPRICE": "50",
            "TAXCODE": "A",
            "TAXRATE": "0",
            "LEVY_AMOUNT_A": "0",
            "LEVY_AMOUNT_B": "0",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        schema = InvoiceItemSchema(**data)
        assert schema.LEVY_AMOUNT_A == "0"
        assert schema.LEVY_AMOUNT_B == "0"
        assert schema.LEVY_AMOUNT_C == "0"
        assert schema.LEVY_AMOUNT_D == "0"
    
    def test_valid_invoice_item_all_levies(self):
        """Test invoice item with all levies"""
        data = {
            "ITMREF": "PROD008",
            "ITMDES": "All Levies Product",
            "QUANTITY": "10",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "1.00",
            "LEVY_AMOUNT_D": "5.00"
        }
        schema = InvoiceItemSchema(**data)
        assert schema.LEVY_AMOUNT_A == "2.50"
        assert schema.LEVY_AMOUNT_B == "2.50"
        assert schema.LEVY_AMOUNT_C == "1.00"
        assert schema.LEVY_AMOUNT_D == "5.00"
    
    def test_valid_invoice_item_with_discount(self):
        """Test invoice item with discount"""
        data = {
            "ITMREF": "PROD009",
            "ITMDES": "Discounted Product",
            "QUANTITY": "10",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0",
            "ITMDISCOUNT": "10.00"
        }
        schema = InvoiceItemSchema(**data)
        assert schema.ITMDISCOUNT == "10.00"
    
    def test_valid_invoice_item_large_quantities(self):
        """Test invoice item with large quantities"""
        data = {
            "ITMREF": "PROD010",
            "ITMDES": "Large Quantity Product",
            "QUANTITY": "999999.99",
            "UNITYPRICE": "999999.99",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        schema = InvoiceItemSchema(**data)
        assert schema.QUANTITY == "999999.99"
        assert schema.UNITYPRICE == "999999.99"
    
    def test_invalid_tax_code(self):
        """Test invalid tax code"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "QUANTITY": "10",
            "UNITYPRICE": "100",
            "TAXCODE": "Z",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "TAXCODE" in str(exc_info.value)
    
    def test_invalid_tax_rate(self):
        """Test invalid tax rate"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "QUANTITY": "10",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "20",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "TAXRATE" in str(exc_info.value)
    
    def test_invalid_quantity_zero(self):
        """Test invalid quantity (zero)"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "QUANTITY": "0",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "QUANTITY" in str(exc_info.value)
    
    def test_invalid_quantity_negative(self):
        """Test invalid quantity (negative)"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "QUANTITY": "-5",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "QUANTITY" in str(exc_info.value)
    
    def test_invalid_unityprice_zero(self):
        """Test invalid unit price (zero)"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "QUANTITY": "10",
            "UNITYPRICE": "0",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "UNITYPRICE" in str(exc_info.value)
    
    def test_invalid_unityprice_negative(self):
        """Test invalid unit price (negative)"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "QUANTITY": "10",
            "UNITYPRICE": "-100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "UNITYPRICE" in str(exc_info.value)
    
    def test_invalid_levy_amount_negative(self):
        """Test invalid levy amount (negative)"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "QUANTITY": "10",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "-2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "LEVY_AMOUNT_A" in str(exc_info.value)
    
    def test_invalid_discount_negative(self):
        """Test invalid discount (negative)"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "QUANTITY": "10",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0",
            "ITMDISCOUNT": "-5.00"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "ITMDISCOUNT" in str(exc_info.value)
    
    def test_invalid_expire_date_format(self):
        """Test invalid expiry date format"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "QUANTITY": "10",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0",
            "EXPIRE": "31-12-2026"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "EXPIRE" in str(exc_info.value)
    
    def test_missing_required_field_itmref(self):
        """Test missing required field ITMREF"""
        data = {
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
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "ITMREF" in str(exc_info.value)
    
    def test_missing_required_field_itmdes(self):
        """Test missing required field ITMDES"""
        data = {
            "ITMREF": "PROD001",
            "QUANTITY": "10",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "ITMDES" in str(exc_info.value)
    
    def test_missing_required_field_quantity(self):
        """Test missing required field QUANTITY"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "QUANTITY" in str(exc_info.value)
    
    def test_missing_required_field_unityprice(self):
        """Test missing required field UNITYPRICE"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "QUANTITY": "10",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "UNITYPRICE" in str(exc_info.value)
    
    def test_missing_required_field_taxcode(self):
        """Test missing required field TAXCODE"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "QUANTITY": "10",
            "UNITYPRICE": "100",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "TAXCODE" in str(exc_info.value)
    
    def test_missing_required_field_taxrate(self):
        """Test missing required field TAXRATE"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "QUANTITY": "10",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "TAXRATE" in str(exc_info.value)
    
    def test_missing_required_field_levy_amount_a(self):
        """Test missing required field LEVY_AMOUNT_A"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "Product Description",
            "QUANTITY": "10",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "LEVY_AMOUNT_A" in str(exc_info.value)
    
    def test_empty_itmref(self):
        """Test empty ITMREF"""
        data = {
            "ITMREF": "",
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
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "ITMREF" in str(exc_info.value)
    
    def test_empty_itmdes(self):
        """Test empty ITMDES"""
        data = {
            "ITMREF": "PROD001",
            "ITMDES": "",
            "QUANTITY": "10",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "2.50",
            "LEVY_AMOUNT_B": "2.50",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceItemSchema(**data)
        assert "ITMDES" in str(exc_info.value)
    
    def test_valid_invoice_item_default_discount(self):
        """Test invoice item with default discount (0)"""
        data = {
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
        schema = InvoiceItemSchema(**data)
        assert schema.ITMDISCOUNT == "0"
    
    def test_valid_invoice_item_all_tax_codes(self):
        """Test invoice item with all valid tax codes"""
        tax_codes = ["A", "B", "C", "D", "E"]
        for tax_code in tax_codes:
            data = {
                "ITMREF": f"PROD_{tax_code}",
                "ITMDES": f"Product {tax_code}",
                "QUANTITY": "10",
                "UNITYPRICE": "100",
                "TAXCODE": tax_code,
                "TAXRATE": "0" if tax_code != "B" else "15",
                "LEVY_AMOUNT_A": "0",
                "LEVY_AMOUNT_B": "0",
                "LEVY_AMOUNT_C": "0",
                "LEVY_AMOUNT_D": "0"
            }
            schema = InvoiceItemSchema(**data)
            assert schema.TAXCODE == tax_code


class TestInvoiceItemResponseSchema:
    """Test InvoiceItemResponseSchema"""
    
    def test_valid_response_schema(self):
        """Test creating a valid response schema"""
        data = {
            "itmref": "PROD001",
            "itmdes": "Product Description",
            "quantity": 10.0,
            "unityprice": 100.0,
            "taxcode": "B",
            "taxrate": 15.0,
            "levy_amount_a": 2.50,
            "levy_amount_b": 2.50,
            "levy_amount_c": 0.0,
            "levy_amount_d": 0.0,
            "itmdiscount": 0.0,
            "item_total": 1200.0,
            "item_category": "GOODS",
            "created_at": datetime.now()
        }
        schema = InvoiceItemResponseSchema(**data)
        assert schema.itmref == "PROD001"
        assert schema.quantity == 10.0
        assert schema.item_total == 1200.0
    
    def test_response_schema_without_category(self):
        """Test response schema without item category"""
        data = {
            "itmref": "PROD001",
            "itmdes": "Product Description",
            "quantity": 10.0,
            "unityprice": 100.0,
            "taxcode": "B",
            "taxrate": 15.0,
            "levy_amount_a": 2.50,
            "levy_amount_b": 2.50,
            "levy_amount_c": 0.0,
            "levy_amount_d": 0.0,
            "itmdiscount": 0.0,
            "item_total": 1200.0,
            "created_at": datetime.now()
        }
        schema = InvoiceItemResponseSchema(**data)
        assert schema.item_category is None

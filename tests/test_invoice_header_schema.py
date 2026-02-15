"""Tests for InvoiceHeaderSchema"""
import pytest
from pydantic import ValidationError
from app.schemas.invoice import InvoiceHeaderSchema, InvoiceHeaderResponseSchema
from datetime import datetime


class TestInvoiceHeaderSchemaValidation:
    """Test InvoiceHeaderSchema validation"""
    
    def test_valid_invoice_header_minimal(self):
        """Test creating a valid invoice header with minimal fields"""
        data = {
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
            "ITEMS_COUNTS": "2"
        }
        schema = InvoiceHeaderSchema(**data)
        assert schema.COMPUTATION_TYPE == "INCLUSIVE"
        assert schema.FLAG == "INVOICE"
        assert schema.NUM == "INV-2026-001"
        assert schema.CLIENT_NAME == "Customer Ltd"
    
    def test_valid_invoice_header_with_client_tin(self):
        """Test invoice header with client TIN"""
        data = {
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
        }
        schema = InvoiceHeaderSchema(**data)
        assert schema.CLIENT_TIN == "C0022825405"
    
    def test_valid_invoice_header_exclusive_computation(self):
        """Test invoice header with EXCLUSIVE computation type"""
        data = {
            "COMPUTATION_TYPE": "EXCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-002",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "TOTAL_VAT": "200",
            "TOTAL_LEVY": "80",
            "TOTAL_AMOUNT": "4000",
            "ITEMS_COUNTS": "3"
        }
        schema = InvoiceHeaderSchema(**data)
        assert schema.COMPUTATION_TYPE == "EXCLUSIVE"
    
    def test_valid_invoice_header_refund_flag(self):
        """Test invoice header with REFUND flag"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "REFUND",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "REF-2026-001",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "TOTAL_VAT": "50",
            "TOTAL_LEVY": "20",
            "TOTAL_AMOUNT": "1000",
            "ITEMS_COUNTS": "1"
        }
        schema = InvoiceHeaderSchema(**data)
        assert schema.FLAG == "REFUND"
    
    def test_valid_invoice_header_purchase_flag(self):
        """Test invoice header with PURCHASE flag"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "PURCHASE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "PUR-2026-001",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Supplier Ltd",
            "TOTAL_VAT": "100",
            "TOTAL_LEVY": "40",
            "TOTAL_AMOUNT": "2000",
            "ITEMS_COUNTS": "2"
        }
        schema = InvoiceHeaderSchema(**data)
        assert schema.FLAG == "PURCHASE"
    
    def test_valid_invoice_header_credit_sale(self):
        """Test invoice header with CREDIT_SALE type"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "CREDIT_SALE",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-003",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "TOTAL_VAT": "159",
            "TOTAL_LEVY": "60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        schema = InvoiceHeaderSchema(**data)
        assert schema.SALE_TYPE == "CREDIT_SALE"
    
    def test_valid_invoice_header_decimal_amounts(self):
        """Test invoice header with decimal amounts"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-004",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "TOTAL_VAT": "159.50",
            "TOTAL_LEVY": "60.25",
            "TOTAL_AMOUNT": "3438.75",
            "ITEMS_COUNTS": "2"
        }
        schema = InvoiceHeaderSchema(**data)
        assert schema.TOTAL_VAT == "159.50"
        assert schema.TOTAL_LEVY == "60.25"
        assert schema.TOTAL_AMOUNT == "3438.75"
    
    def test_valid_invoice_header_zero_amounts(self):
        """Test invoice header with zero amounts"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-005",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "TOTAL_VAT": "0",
            "TOTAL_LEVY": "0",
            "TOTAL_AMOUNT": "1000",
            "ITEMS_COUNTS": "1"
        }
        schema = InvoiceHeaderSchema(**data)
        assert schema.TOTAL_VAT == "0"
        assert schema.TOTAL_LEVY == "0"
    
    def test_valid_invoice_header_large_amounts(self):
        """Test invoice header with large amounts"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-006",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "TOTAL_VAT": "999999.99",
            "TOTAL_LEVY": "999999.99",
            "TOTAL_AMOUNT": "9999999.99",
            "ITEMS_COUNTS": "100"
        }
        schema = InvoiceHeaderSchema(**data)
        assert schema.TOTAL_AMOUNT == "9999999.99"
    
    def test_invalid_computation_type(self):
        """Test invalid computation type"""
        data = {
            "COMPUTATION_TYPE": "INVALID",
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
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "COMPUTATION_TYPE" in str(exc_info.value)
    
    def test_invalid_flag(self):
        """Test invalid flag"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVALID_FLAG",
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
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "FLAG" in str(exc_info.value)
    
    def test_invalid_sale_type(self):
        """Test invalid sale type"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "INVALID_SALE",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-001",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "TOTAL_VAT": "159",
            "TOTAL_LEVY": "60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "SALE_TYPE" in str(exc_info.value)
    
    def test_invalid_currency(self):
        """Test invalid currency"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-001",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "USD",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "TOTAL_VAT": "159",
            "TOTAL_LEVY": "60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "CURRENCY" in str(exc_info.value)
    
    def test_invalid_exchange_rate(self):
        """Test invalid exchange rate"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-001",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "2",
            "CLIENT_NAME": "Customer Ltd",
            "TOTAL_VAT": "159",
            "TOTAL_LEVY": "60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "EXCHANGE_RATE" in str(exc_info.value)
    
    def test_invalid_invoice_date_format(self):
        """Test invalid invoice date format"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-001",
            "INVOICE_DATE": "02-10-2026",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "TOTAL_VAT": "159",
            "TOTAL_LEVY": "60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "INVOICE_DATE" in str(exc_info.value)
    
    def test_invalid_client_tin_length_short(self):
        """Test invalid client TIN length (too short)"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-001",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "CLIENT_TIN": "C00228254",
            "TOTAL_VAT": "159",
            "TOTAL_LEVY": "60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "CLIENT_TIN" in str(exc_info.value)
    
    def test_invalid_client_tin_length_long(self):
        """Test invalid client TIN length (too long)"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-001",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "CLIENT_TIN": "C002282540512345678",
            "TOTAL_VAT": "159",
            "TOTAL_LEVY": "60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "CLIENT_TIN" in str(exc_info.value)
    
    def test_invalid_total_vat_negative(self):
        """Test invalid total VAT (negative)"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-001",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "TOTAL_VAT": "-159",
            "TOTAL_LEVY": "60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "TOTAL_VAT" in str(exc_info.value)
    
    def test_invalid_total_levy_negative(self):
        """Test invalid total levy (negative)"""
        data = {
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
            "TOTAL_LEVY": "-60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "TOTAL_LEVY" in str(exc_info.value)
    
    def test_invalid_total_amount_negative(self):
        """Test invalid total amount (negative)"""
        data = {
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
            "TOTAL_AMOUNT": "-3438",
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "TOTAL_AMOUNT" in str(exc_info.value)
    
    def test_invalid_items_count_zero(self):
        """Test invalid items count (zero)"""
        data = {
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
            "ITEMS_COUNTS": "0"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "ITEMS_COUNTS" in str(exc_info.value)
    
    def test_invalid_items_count_negative(self):
        """Test invalid items count (negative)"""
        data = {
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
            "ITEMS_COUNTS": "-5"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "ITEMS_COUNTS" in str(exc_info.value)
    
    def test_missing_required_field_num(self):
        """Test missing required field NUM"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "TOTAL_VAT": "159",
            "TOTAL_LEVY": "60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "NUM" in str(exc_info.value)
    
    def test_missing_required_field_client_name(self):
        """Test missing required field CLIENT_NAME"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-001",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "TOTAL_VAT": "159",
            "TOTAL_LEVY": "60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "CLIENT_NAME" in str(exc_info.value)
    
    def test_empty_client_name(self):
        """Test empty client name"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-001",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "",
            "TOTAL_VAT": "159",
            "TOTAL_LEVY": "60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "CLIENT_NAME" in str(exc_info.value)
    
    def test_empty_user_name(self):
        """Test empty user name"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "",
            "NUM": "INV-2026-001",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "TOTAL_VAT": "159",
            "TOTAL_LEVY": "60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceHeaderSchema(**data)
        assert "USER_NAME" in str(exc_info.value)
    
    def test_valid_invoice_header_11_char_tin(self):
        """Test valid invoice header with 11-character TIN"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-001",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "CLIENT_TIN": "P0012345678",
            "TOTAL_VAT": "159",
            "TOTAL_LEVY": "60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        schema = InvoiceHeaderSchema(**data)
        assert schema.CLIENT_TIN == "P0012345678"
        assert len(schema.CLIENT_TIN) == 11
    
    def test_valid_invoice_header_15_char_tin(self):
        """Test valid invoice header with 15-character TIN"""
        data = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "SALE_TYPE": "NORMAL",
            "USER_NAME": "JOHN",
            "NUM": "INV-2026-001",
            "INVOICE_DATE": "2026-02-10",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "CLIENT_NAME": "Customer Ltd",
            "CLIENT_TIN": "C00228254051234",
            "TOTAL_VAT": "159",
            "TOTAL_LEVY": "60",
            "TOTAL_AMOUNT": "3438",
            "ITEMS_COUNTS": "2"
        }
        schema = InvoiceHeaderSchema(**data)
        assert schema.CLIENT_TIN == "C00228254051234"
        assert len(schema.CLIENT_TIN) == 15


class TestInvoiceHeaderResponseSchema:
    """Test InvoiceHeaderResponseSchema"""
    
    def test_valid_response_schema(self):
        """Test creating a valid response schema"""
        data = {
            "invoice_num": "INV-2026-001",
            "client_name": "Customer Ltd",
            "client_tin": "C0022825405",
            "invoice_date": "2026-02-10",
            "computation_type": "INCLUSIVE",
            "total_vat": 159.0,
            "total_levy": 60.0,
            "total_amount": 3438.0,
            "items_count": 2,
            "created_at": datetime.now()
        }
        schema = InvoiceHeaderResponseSchema(**data)
        assert schema.invoice_num == "INV-2026-001"
        assert schema.client_name == "Customer Ltd"
        assert schema.total_amount == 3438.0
    
    def test_response_schema_without_client_tin(self):
        """Test response schema without client TIN"""
        data = {
            "invoice_num": "INV-2026-001",
            "client_name": "Customer Ltd",
            "invoice_date": "2026-02-10",
            "computation_type": "INCLUSIVE",
            "total_vat": 159.0,
            "total_levy": 60.0,
            "total_amount": 3438.0,
            "items_count": 2,
            "created_at": datetime.now()
        }
        schema = InvoiceHeaderResponseSchema(**data)
        assert schema.client_tin is None

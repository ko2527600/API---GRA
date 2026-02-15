"""Tests for business logic validation"""
import pytest
from decimal import Decimal
from app.utils.business_logic_validator import BusinessLogicValidator


class TestInvoiceTotalsValidation:
    """Tests for invoice totals validation"""
    
    def test_validate_invoice_totals_correct(self):
        """Test validation passes when totals are correct"""
        header = {
            "TOTAL_VAT": "31.66",
            "TOTAL_LEVY": "12.00",
            "TOTAL_AMOUNT": "243.66"
        }
        
        items = [
            {
                "vat": Decimal("31.66"),
                "LEVY_AMOUNT_A": Decimal("6.00"),
                "LEVY_AMOUNT_B": Decimal("6.00"),
                "LEVY_AMOUNT_C": Decimal("0"),
                "LEVY_AMOUNT_D": Decimal("0"),
                "item_total": Decimal("243.66")
            }
        ]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_invoice_totals(header, items)
        
        assert is_valid is True
        assert error_code is None
        assert error_message is None
    
    def test_validate_invoice_totals_vat_mismatch(self):
        """Test validation fails when VAT doesn't match"""
        header = {
            "TOTAL_VAT": "20.00",  # Wrong VAT
            "TOTAL_LEVY": "12.00",
            "TOTAL_AMOUNT": "243.66"
        }
        
        items = [
            {
                "vat": Decimal("31.66"),
                "LEVY_AMOUNT_A": Decimal("6.00"),
                "LEVY_AMOUNT_B": Decimal("6.00"),
                "LEVY_AMOUNT_C": Decimal("0"),
                "LEVY_AMOUNT_D": Decimal("0"),
                "item_total": Decimal("243.66")
            }
        ]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_invoice_totals(header, items)
        
        assert is_valid is False
        assert error_code == "B18"
        assert "VAT mismatch" in error_message
    
    def test_validate_invoice_totals_levy_mismatch(self):
        """Test validation fails when levy doesn't match"""
        header = {
            "TOTAL_VAT": "31.66",
            "TOTAL_LEVY": "10.00",  # Wrong levy
            "TOTAL_AMOUNT": "243.66"
        }
        
        items = [
            {
                "vat": Decimal("31.66"),
                "LEVY_AMOUNT_A": Decimal("6.00"),
                "LEVY_AMOUNT_B": Decimal("6.00"),
                "LEVY_AMOUNT_C": Decimal("0"),
                "LEVY_AMOUNT_D": Decimal("0"),
                "item_total": Decimal("243.66")
            }
        ]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_invoice_totals(header, items)
        
        assert is_valid is False
        assert error_code == "B34"
        assert "levy mismatch" in error_message.lower()
    
    def test_validate_invoice_totals_amount_mismatch(self):
        """Test validation fails when total amount doesn't match"""
        header = {
            "TOTAL_VAT": "31.66",
            "TOTAL_LEVY": "12.00",
            "TOTAL_AMOUNT": "250.00"  # Wrong amount
        }
        
        items = [
            {
                "vat": Decimal("31.66"),
                "LEVY_AMOUNT_A": Decimal("6.00"),
                "LEVY_AMOUNT_B": Decimal("6.00"),
                "LEVY_AMOUNT_C": Decimal("0"),
                "LEVY_AMOUNT_D": Decimal("0"),
                "item_total": Decimal("243.66")
            }
        ]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_invoice_totals(header, items)
        
        assert is_valid is False
        assert error_code == "B16"
        assert "Total amount mismatch" in error_message
    
    def test_validate_invoice_totals_multiple_items(self):
        """Test validation with multiple items"""
        header = {
            "TOTAL_VAT": "27.71",
            "TOTAL_LEVY": "10.50",
            "TOTAL_AMOUNT": "213.21"
        }
        
        items = [
            {
                "vat": Decimal("15.83"),
                "LEVY_AMOUNT_A": Decimal("3.00"),
                "LEVY_AMOUNT_B": Decimal("3.00"),
                "LEVY_AMOUNT_C": Decimal("0"),
                "LEVY_AMOUNT_D": Decimal("0"),
                "item_total": Decimal("121.83")
            },
            {
                "vat": Decimal("11.88"),
                "LEVY_AMOUNT_A": Decimal("2.25"),
                "LEVY_AMOUNT_B": Decimal("2.25"),
                "LEVY_AMOUNT_C": Decimal("0"),
                "LEVY_AMOUNT_D": Decimal("0"),
                "item_total": Decimal("91.38")
            }
        ]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_invoice_totals(header, items)
        
        assert is_valid is True


class TestItemsCountValidation:
    """Tests for items count validation"""
    
    def test_validate_items_count_correct(self):
        """Test validation passes when count matches"""
        header = {"ITEMS_COUNTS": "2"}
        items = [{}, {}]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_items_count(header, items)
        
        assert is_valid is True
        assert error_code is None
    
    def test_validate_items_count_mismatch(self):
        """Test validation fails when count doesn't match"""
        header = {"ITEMS_COUNTS": "3"}
        items = [{}, {}]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_items_count(header, items)
        
        assert is_valid is False
        assert error_code == "B15"
        assert "Item count mismatch" in error_message


class TestItemQuantitiesValidation:
    """Tests for item quantities validation"""
    
    def test_validate_item_quantities_positive(self):
        """Test validation passes for positive quantities"""
        items = [
            {"QUANTITY": "10"},
            {"QUANTITY": "5.5"}
        ]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_item_quantities(items)
        
        assert is_valid is True
    
    def test_validate_item_quantities_zero(self):
        """Test validation fails for zero quantity"""
        items = [{"QUANTITY": "0"}]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_item_quantities(items)
        
        assert is_valid is False
        assert error_code == "B11"
    
    def test_validate_item_quantities_negative(self):
        """Test validation fails for negative quantity"""
        items = [{"QUANTITY": "-5"}]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_item_quantities(items)
        
        assert is_valid is False
        assert error_code == "B11"
    
    def test_validate_item_quantities_non_numeric(self):
        """Test validation fails for non-numeric quantity"""
        items = [{"QUANTITY": "abc"}]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_item_quantities(items)
        
        assert is_valid is False
        assert error_code == "B12"


class TestItemPricesValidation:
    """Tests for item prices validation"""
    
    def test_validate_item_prices_positive(self):
        """Test validation passes for positive prices"""
        items = [
            {"UNITYPRICE": "100"},
            {"UNITYPRICE": "50.50"}
        ]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_item_prices(items)
        
        assert is_valid is True
    
    def test_validate_item_prices_zero(self):
        """Test validation fails for zero price"""
        items = [{"UNITYPRICE": "0"}]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_item_prices(items)
        
        assert is_valid is False
        assert error_code == "B21"
    
    def test_validate_item_prices_negative(self):
        """Test validation fails for negative price"""
        items = [{"UNITYPRICE": "-100"}]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_item_prices(items)
        
        assert is_valid is False
        assert error_code == "B21"
    
    def test_validate_item_prices_non_numeric(self):
        """Test validation fails for non-numeric price"""
        items = [{"UNITYPRICE": "abc"}]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_item_prices(items)
        
        assert is_valid is False
        assert error_code == "A06"


class TestClientNameValidation:
    """Tests for client name validation"""
    
    def test_validate_client_name_provided(self):
        """Test validation passes when client name is provided"""
        header = {"CLIENT_NAME": "Customer Ltd"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_client_name(header)
        
        assert is_valid is True
    
    def test_validate_client_name_empty(self):
        """Test validation fails when client name is empty"""
        header = {"CLIENT_NAME": ""}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_client_name(header)
        
        assert is_valid is False
        assert error_code == "B05"
    
    def test_validate_client_name_missing(self):
        """Test validation fails when client name is missing"""
        header = {}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_client_name(header)
        
        assert is_valid is False
        assert error_code == "B05"


class TestClientTINValidation:
    """Tests for client TIN format validation"""
    
    def test_validate_client_tin_11_chars(self):
        """Test validation passes for 11-character TIN"""
        header = {"CLIENT_TIN": "C0022825405"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_client_tin_format(header)
        
        assert is_valid is True
    
    def test_validate_client_tin_15_chars(self):
        """Test validation passes for 15-character TIN"""
        header = {"CLIENT_TIN": "C00228254051234"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_client_tin_format(header)
        
        assert is_valid is True
    
    def test_validate_client_tin_invalid_length(self):
        """Test validation fails for invalid TIN length"""
        header = {"CLIENT_TIN": "C00228"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_client_tin_format(header)
        
        assert is_valid is False
        assert error_code == "B051"
    
    def test_validate_client_tin_optional(self):
        """Test validation passes when TIN is not provided"""
        header = {}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_client_tin_format(header)
        
        assert is_valid is True


class TestCurrencyValidation:
    """Tests for currency validation"""
    
    def test_validate_currency_ghs(self):
        """Test validation passes for GHS currency"""
        header = {"CURRENCY": "GHS"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_currency(header)
        
        assert is_valid is True
    
    def test_validate_currency_invalid(self):
        """Test validation fails for non-GHS currency"""
        header = {"CURRENCY": "USD"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_currency(header)
        
        assert is_valid is False
        assert error_code == "B70"


class TestExchangeRateValidation:
    """Tests for exchange rate validation"""
    
    def test_validate_exchange_rate_one(self):
        """Test validation passes for exchange rate of 1"""
        header = {"EXCHANGE_RATE": "1"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_exchange_rate(header)
        
        assert is_valid is True
    
    def test_validate_exchange_rate_invalid(self):
        """Test validation fails for exchange rate not equal to 1"""
        header = {"EXCHANGE_RATE": "2"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_exchange_rate(header)
        
        assert is_valid is False
        assert error_code == "B70"


class TestInvoiceDateValidation:
    """Tests for invoice date validation"""
    
    def test_validate_invoice_date_valid(self):
        """Test validation passes for valid date format"""
        header = {"INVOICE_DATE": "2026-02-10"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_invoice_date_format(header)
        
        assert is_valid is True
    
    def test_validate_invoice_date_invalid_format(self):
        """Test validation fails for invalid date format"""
        header = {"INVOICE_DATE": "10-02-2026"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_invoice_date_format(header)
        
        assert is_valid is False
        assert error_code == "B19"


class TestTaxCodeValidation:
    """Tests for tax code validation"""
    
    def test_validate_tax_codes_valid(self):
        """Test validation passes for valid tax codes"""
        items = [
            {"TAXCODE": "A"},
            {"TAXCODE": "B"},
            {"TAXCODE": "C"},
            {"TAXCODE": "D"},
            {"TAXCODE": "E"}
        ]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_tax_codes(items)
        
        assert is_valid is True
    
    def test_validate_tax_codes_invalid(self):
        """Test validation fails for invalid tax code"""
        items = [{"TAXCODE": "F"}]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_tax_codes(items)
        
        assert is_valid is False
        assert error_code == "A08"


class TestTaxRateValidation:
    """Tests for tax rate validation"""
    
    def test_validate_tax_rates_valid(self):
        """Test validation passes for valid tax rates"""
        items = [
            {"TAXRATE": "0"},
            {"TAXRATE": "15"},
            {"TAXRATE": "3"}
        ]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_tax_rates(items)
        
        assert is_valid is True
    
    def test_validate_tax_rates_invalid(self):
        """Test validation fails for invalid tax rate"""
        items = [{"TAXRATE": "10"}]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_tax_rates(items)
        
        assert is_valid is False
        assert error_code == "A09"


class TestLevyAmountsValidation:
    """Tests for levy amounts validation"""
    
    def test_validate_levy_amounts_valid(self):
        """Test validation passes for valid levy amounts"""
        items = [
            {
                "LEVY_AMOUNT_A": "2.50",
                "LEVY_AMOUNT_B": "2.50",
                "LEVY_AMOUNT_D": "0"
            }
        ]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_levy_amounts(items)
        
        assert is_valid is True
    
    def test_validate_levy_amounts_negative(self):
        """Test validation fails for negative levy amount"""
        items = [
            {
                "LEVY_AMOUNT_A": "-2.50",
                "LEVY_AMOUNT_B": "2.50",
                "LEVY_AMOUNT_D": "0"
            }
        ]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_levy_amounts(items)
        
        assert is_valid is False
        assert error_code == "B31"


class TestRefundIDValidation:
    """Tests for refund ID validation"""
    
    def test_validate_refund_id_provided_for_refund(self):
        """Test validation passes when REFUND_ID is provided for REFUND flag"""
        header = {"FLAG": "REFUND", "REFUND_ID": "INV-2026-001"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_refund_id_provided(header)
        
        assert is_valid is True
    
    def test_validate_refund_id_missing_for_refund(self):
        """Test validation fails when REFUND_ID is missing for REFUND flag"""
        header = {"FLAG": "REFUND", "REFUND_ID": ""}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_refund_id_provided(header)
        
        assert is_valid is False
        assert error_code == "A05"
    
    def test_validate_refund_id_not_required_for_invoice(self):
        """Test validation passes when REFUND_ID is not required for INVOICE flag"""
        header = {"FLAG": "INVOICE"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_refund_id_provided(header)
        
        assert is_valid is True


class TestItemDiscountValidation:
    """Tests for item discount validation"""
    
    def test_validate_item_discounts_valid(self):
        """Test validation passes for valid item discounts"""
        items = [
            {"ITMDISCOUNT": "10"},
            {"ITMDISCOUNT": "5.50"}
        ]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_item_discounts(items)
        
        assert is_valid is True
    
    def test_validate_item_discounts_zero(self):
        """Test validation passes for zero discount"""
        items = [{"ITMDISCOUNT": "0"}]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_item_discounts(items)
        
        assert is_valid is True
    
    def test_validate_item_discounts_negative(self):
        """Test validation fails for negative discount"""
        items = [{"ITMDISCOUNT": "-5"}]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_item_discounts(items)
        
        assert is_valid is False
        assert error_code == "A07"
    
    def test_validate_item_discounts_non_numeric(self):
        """Test validation fails for non-numeric discount"""
        items = [{"ITMDISCOUNT": "abc"}]
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_item_discounts(items)
        
        assert is_valid is False
        assert error_code == "A07"


class TestHeaderDiscountValidation:
    """Tests for header-level discount validation"""
    
    def test_validate_header_discount_valid(self):
        """Test validation passes for valid header discount"""
        header = {"DISCOUNT_AMOUNT": "50"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_header_discount(header)
        
        assert is_valid is True
    
    def test_validate_header_discount_zero(self):
        """Test validation passes for zero header discount"""
        header = {"DISCOUNT_AMOUNT": "0"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_header_discount(header)
        
        assert is_valid is True
    
    def test_validate_header_discount_negative(self):
        """Test validation fails for negative header discount"""
        header = {"DISCOUNT_AMOUNT": "-50"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_header_discount(header)
        
        assert is_valid is False
        assert error_code == "A07"
    
    def test_validate_header_discount_non_numeric(self):
        """Test validation fails for non-numeric header discount"""
        header = {"DISCOUNT_AMOUNT": "abc"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_header_discount(header)
        
        assert is_valid is False
        assert error_code == "A07"
    
    def test_validate_header_discount_missing(self):
        """Test validation passes when header discount is missing (defaults to 0)"""
        header = {}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_header_discount(header)
        
        assert is_valid is True


class TestComputationTypeValidation:
    """Tests for computation type validation"""
    
    def test_validate_computation_type_inclusive(self):
        """Test validation passes for INCLUSIVE computation type"""
        header = {"COMPUTATION_TYPE": "INCLUSIVE"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_computation_type(header)
        
        assert is_valid is True
    
    def test_validate_computation_type_exclusive(self):
        """Test validation passes for EXCLUSIVE computation type"""
        header = {"COMPUTATION_TYPE": "EXCLUSIVE"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_computation_type(header)
        
        assert is_valid is True
    
    def test_validate_computation_type_invalid(self):
        """Test validation fails for invalid computation type"""
        header = {"COMPUTATION_TYPE": "INVALID"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_computation_type(header)
        
        assert is_valid is False
        assert error_code == "B70"


class TestFlagTypeValidation:
    """Tests for flag type validation"""
    
    def test_validate_flag_type_valid(self):
        """Test validation passes for valid flag types"""
        for flag in ["INVOICE", "REFUND", "PROFORMA", "PARTIAL_REFUND", "PURCHASE"]:
            header = {"FLAG": flag}
            
            is_valid, error_code, error_message = BusinessLogicValidator.validate_flag_type(header)
            
            assert is_valid is True
    
    def test_validate_flag_type_invalid(self):
        """Test validation fails for invalid flag type"""
        header = {"FLAG": "INVALID"}
        
        is_valid, error_code, error_message = BusinessLogicValidator.validate_flag_type(header)
        
        assert is_valid is False


class TestAllInvoiceBusinessLogic:
    """Tests for comprehensive invoice business logic validation"""
    
    def test_validate_all_invoice_business_logic_valid(self):
        """Test all validations pass for valid invoice"""
        header = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "INVOICE",
            "CLIENT_NAME": "Customer Ltd",
            "CLIENT_TIN": "C0022825405",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "INVOICE_DATE": "2026-02-10",
            "ITEMS_COUNTS": "1",
            "TOTAL_VAT": "31.66",
            "TOTAL_LEVY": "12.00",
            "TOTAL_AMOUNT": "243.66"
        }
        
        items = [
            {
                "QUANTITY": "10",
                "UNITYPRICE": "100",
                "TAXCODE": "B",
                "TAXRATE": "15",
                "LEVY_AMOUNT_A": "6.00",
                "LEVY_AMOUNT_B": "6.00",
                "LEVY_AMOUNT_C": "0",
                "LEVY_AMOUNT_D": "0",
                "vat": Decimal("31.66"),
                "item_total": Decimal("243.66")
            }
        ]
        
        is_valid, errors = BusinessLogicValidator.validate_all_invoice_business_logic(header, items)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_all_invoice_business_logic_multiple_errors(self):
        """Test multiple validation errors are collected"""
        header = {
            "COMPUTATION_TYPE": "INVALID",
            "FLAG": "INVALID",
            "CLIENT_NAME": "",
            "CURRENCY": "USD",
            "EXCHANGE_RATE": "2",
            "INVOICE_DATE": "invalid",
            "ITEMS_COUNTS": "2",
            "TOTAL_VAT": "100",
            "TOTAL_LEVY": "100",
            "TOTAL_AMOUNT": "1000"
        }
        
        items = [
            {
                "QUANTITY": "0",
                "UNITYPRICE": "-100",
                "TAXCODE": "F",
                "TAXRATE": "10",
                "LEVY_AMOUNT_A": "-5",
                "LEVY_AMOUNT_B": "2.50",
                "LEVY_AMOUNT_C": "0",
                "LEVY_AMOUNT_D": "0",
                "vat": Decimal("0"),
                "item_total": Decimal("0")
            }
        ]
        
        is_valid, errors = BusinessLogicValidator.validate_all_invoice_business_logic(header, items)
        
        assert is_valid is False
        assert len(errors) > 0


class TestAllRefundBusinessLogic:
    """Tests for comprehensive refund business logic validation"""
    
    def test_validate_all_refund_business_logic_valid(self):
        """Test all validations pass for valid refund"""
        header = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "REFUND",
            "REFUND_ID": "INV-2026-001",
            "CLIENT_NAME": "Customer Ltd",
            "CLIENT_TIN": "C0022825405",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "INVOICE_DATE": "2026-02-10",
            "ITEMS_COUNTS": "1",
            "TOTAL_VAT": "31.66",
            "TOTAL_LEVY": "12.00",
            "TOTAL_AMOUNT": "243.66"
        }
        
        items = [
            {
                "QUANTITY": "10",
                "UNITYPRICE": "100",
                "TAXCODE": "B",
                "TAXRATE": "15",
                "LEVY_AMOUNT_A": "6.00",
                "LEVY_AMOUNT_B": "6.00",
                "LEVY_AMOUNT_C": "0",
                "LEVY_AMOUNT_D": "0",
                "vat": Decimal("31.66"),
                "item_total": Decimal("243.66")
            }
        ]
        
        is_valid, errors = BusinessLogicValidator.validate_all_refund_business_logic(header, items)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_all_refund_business_logic_missing_refund_id(self):
        """Test validation fails when REFUND_ID is missing"""
        header = {
            "COMPUTATION_TYPE": "INCLUSIVE",
            "FLAG": "REFUND",
            "REFUND_ID": "",
            "CLIENT_NAME": "Customer Ltd",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1",
            "INVOICE_DATE": "2026-02-10",
            "ITEMS_COUNTS": "1",
            "TOTAL_VAT": "31.66",
            "TOTAL_LEVY": "12.00",
            "TOTAL_AMOUNT": "243.66"
        }
        
        items = [
            {
                "QUANTITY": "10",
                "UNITYPRICE": "100",
                "TAXCODE": "B",
                "TAXRATE": "15",
                "LEVY_AMOUNT_A": "6.00",
                "LEVY_AMOUNT_B": "6.00",
                "LEVY_AMOUNT_C": "0",
                "LEVY_AMOUNT_D": "0",
                "vat": Decimal("31.66"),
                "item_total": Decimal("243.66")
            }
        ]
        
        is_valid, errors = BusinessLogicValidator.validate_all_refund_business_logic(header, items)
        
        assert is_valid is False
        assert any(e["error_code"] == "A05" for e in errors)

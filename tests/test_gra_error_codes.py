"""Tests for GRA Error Code Validators"""
import pytest
from decimal import Decimal
from app.utils.gra_error_codes import GRAErrorValidator, GRAErrorCode


class TestAuthenticationErrors:
    """Tests for authentication error codes A01, B01"""
    
    def test_a01_company_credentials_missing_tin(self):
        """A01: Company credentials do not exist - missing TIN"""
        valid, error = GRAErrorValidator.validate_company_credentials_exist(None, "Company", "key")
        assert not valid
        assert "A01" in error
    
    def test_a01_company_credentials_missing_name(self):
        """A01: Company credentials do not exist - missing name"""
        valid, error = GRAErrorValidator.validate_company_credentials_exist("TIN123", None, "key")
        assert not valid
        assert "A01" in error
    
    def test_a01_company_credentials_missing_key(self):
        """A01: Company credentials do not exist - missing key"""
        valid, error = GRAErrorValidator.validate_company_credentials_exist("TIN123", "Company", None)
        assert not valid
        assert "A01" in error
    
    def test_a01_company_credentials_valid(self):
        """A01: Company credentials exist"""
        valid, error = GRAErrorValidator.validate_company_credentials_exist("TIN123", "Company", "key")
        assert valid
        assert error is None
    
    def test_b01_client_tin_pin_missing(self):
        """B01: Incorrect client TIN PIN - missing PIN"""
        valid, error = GRAErrorValidator.validate_client_tin_pin("TIN123", None)
        assert not valid
        assert "B01" in error
    
    def test_b01_client_tin_pin_valid(self):
        """B01: Client TIN PIN provided"""
        valid, error = GRAErrorValidator.validate_client_tin_pin("TIN123", "PIN123")
        assert valid
        assert error is None


class TestInvoiceRefundErrors:
    """Tests for invoice/refund error codes B16, B18, B19, B20, B22, B70, A05"""
    
    def test_b16_total_amount_mismatch(self):
        """B16: Total amount mismatch"""
        valid, error = GRAErrorValidator.validate_total_amount(
            Decimal("900"),  # Wrong total
            Decimal("800"),
            Decimal("150"),
            Decimal("50")
        )
        assert not valid
        assert "B16" in error
    
    def test_b16_total_amount_valid(self):
        """B16: Total amount correct"""
        valid, error = GRAErrorValidator.validate_total_amount(
            Decimal("1000"),
            Decimal("800"),
            Decimal("150"),
            Decimal("50")
        )
        # 800 + 150 + 50 = 1000
        assert valid
        assert error is None
    
    def test_b16_total_amount_within_tolerance(self):
        """B16: Total amount within tolerance"""
        valid, error = GRAErrorValidator.validate_total_amount(
            Decimal("1000.00"),
            Decimal("800.00"),
            Decimal("150.00"),
            Decimal("50.00")
        )
        assert valid
        assert error is None
    
    def test_b18_total_vat_mismatch(self):
        """B18: Total VAT mismatch"""
        valid, error = GRAErrorValidator.validate_total_vat(
            Decimal("100"),
            Decimal("150")
        )
        assert not valid
        assert "B18" in error
    
    def test_b18_total_vat_valid(self):
        """B18: Total VAT correct"""
        valid, error = GRAErrorValidator.validate_total_vat(
            Decimal("150"),
            Decimal("150")
        )
        assert valid
        assert error is None
    
    def test_b19_invoice_reference_missing(self):
        """B19: Invoice reference missing"""
        valid, error = GRAErrorValidator.validate_invoice_reference_present(None)
        assert not valid
        assert "B19" in error
    
    def test_b19_invoice_reference_empty(self):
        """B19: Invoice reference empty"""
        valid, error = GRAErrorValidator.validate_invoice_reference_present("")
        assert not valid
        assert "B19" in error
    
    def test_b19_invoice_reference_valid(self):
        """B19: Invoice reference present"""
        valid, error = GRAErrorValidator.validate_invoice_reference_present("INV-001")
        assert valid
        assert error is None
    
    def test_b20_invoice_duplicate(self):
        """B20: Invoice reference already sent"""
        valid, error = GRAErrorValidator.validate_invoice_not_duplicate(
            "INV-001",
            ["INV-001", "INV-002"]
        )
        assert not valid
        assert "B20" in error
    
    def test_b20_invoice_unique(self):
        """B20: Invoice reference unique"""
        valid, error = GRAErrorValidator.validate_invoice_not_duplicate(
            "INV-003",
            ["INV-001", "INV-002"]
        )
        assert valid
        assert error is None
    
    def test_b22_zero_total_invoice(self):
        """B22: Zero total invoice not supported"""
        valid, error = GRAErrorValidator.validate_non_zero_total(Decimal("0"))
        assert not valid
        assert "B22" in error
    
    def test_b22_non_zero_total(self):
        """B22: Non-zero total invoice"""
        valid, error = GRAErrorValidator.validate_non_zero_total(Decimal("100"))
        assert valid
        assert error is None
    
    def test_b70_wrong_currency(self):
        """B70: Wrong currency"""
        valid, error = GRAErrorValidator.validate_currency_ghs("USD")
        assert not valid
        assert "B70" in error
    
    def test_b70_correct_currency(self):
        """B70: Correct currency"""
        valid, error = GRAErrorValidator.validate_currency_ghs("GHS")
        assert valid
        assert error is None
    
    def test_a05_refund_id_missing(self):
        """A05: Missing original invoice number for refund"""
        valid, error = GRAErrorValidator.validate_refund_id_present(None)
        assert not valid
        assert "A05" in error
    
    def test_a05_refund_id_present(self):
        """A05: Refund ID present"""
        valid, error = GRAErrorValidator.validate_refund_id_present("INV-001")
        assert valid
        assert error is None


class TestItemErrors:
    """Tests for item error codes B05, B051, B07, B09, B10, B11, B12, B13, B15, B21, A06, A08, A09, A11"""
    
    def test_b05_client_name_missing(self):
        """B05: Client name missing"""
        valid, error = GRAErrorValidator.validate_client_name_present(None)
        assert not valid
        assert "B05" in error
    
    def test_b05_client_name_valid(self):
        """B05: Client name present"""
        valid, error = GRAErrorValidator.validate_client_name_present("ABC Company")
        assert valid
        assert error is None
    
    def test_b051_tin_format_invalid_length(self):
        """B051: Tax number format not accepted - invalid length"""
        valid, error = GRAErrorValidator.validate_tin_format("12345")
        assert not valid
        assert "B051" in error
    
    def test_b051_tin_format_valid_11(self):
        """B051: Tax number format valid - 11 characters"""
        valid, error = GRAErrorValidator.validate_tin_format("12345678901")
        assert valid
        assert error is None
    
    def test_b051_tin_format_valid_15(self):
        """B051: Tax number format valid - 15 characters"""
        valid, error = GRAErrorValidator.validate_tin_format("123456789012345")
        assert valid
        assert error is None
    
    def test_b07_item_code_missing(self):
        """B07: Item code missing"""
        valid, error = GRAErrorValidator.validate_item_code_present(None)
        assert not valid
        assert "B07" in error
    
    def test_b07_item_code_valid(self):
        """B07: Item code present"""
        valid, error = GRAErrorValidator.validate_item_code_present("ITEM001")
        assert valid
        assert error is None
    
    def test_b09_description_missing(self):
        """B09: Item description missing"""
        valid, error = GRAErrorValidator.validate_item_description_present(None)
        assert not valid
        assert "B09" in error
    
    def test_b09_description_valid(self):
        """B09: Item description present"""
        valid, error = GRAErrorValidator.validate_item_description_present("Product Description")
        assert valid
        assert error is None
    
    def test_b10_quantity_missing(self):
        """B10: Quantity missing"""
        valid, error = GRAErrorValidator.validate_quantity_present(None)
        assert not valid
        assert "B10" in error
    
    def test_b10_quantity_valid(self):
        """B10: Quantity present"""
        valid, error = GRAErrorValidator.validate_quantity_present("10")
        assert valid
        assert error is None
    
    def test_b11_quantity_negative(self):
        """B11: Quantity is negative"""
        valid, error = GRAErrorValidator.validate_quantity_non_negative(Decimal("-5"))
        assert not valid
        assert "B11" in error
    
    def test_b11_quantity_valid(self):
        """B11: Quantity non-negative"""
        valid, error = GRAErrorValidator.validate_quantity_non_negative(Decimal("10"))
        assert valid
        assert error is None
    
    def test_b12_quantity_not_numeric(self):
        """B12: Quantity not a number"""
        valid, error = GRAErrorValidator.validate_quantity_numeric("abc")
        assert not valid
        assert "B12" in error
    
    def test_b12_quantity_numeric(self):
        """B12: Quantity is numeric"""
        valid, error = GRAErrorValidator.validate_quantity_numeric("10.5")
        assert valid
        assert error is None
    
    def test_b13_tax_rate_invalid(self):
        """B13: Tax rate not accepted"""
        valid, error = GRAErrorValidator.validate_tax_rate_valid("20", "B")
        assert not valid
        assert "B13" in error
    
    def test_b13_tax_rate_valid_b(self):
        """B13: Tax rate valid for code B"""
        valid, error = GRAErrorValidator.validate_tax_rate_valid("15", "B")
        assert valid
        assert error is None
    
    def test_b13_tax_rate_valid_a(self):
        """B13: Tax rate valid for code A"""
        valid, error = GRAErrorValidator.validate_tax_rate_valid("0", "A")
        assert valid
        assert error is None
    
    def test_b15_item_count_mismatch(self):
        """B15: Item count mismatch"""
        valid, error = GRAErrorValidator.validate_item_count_match(5, 3)
        assert not valid
        assert "B15" in error
    
    def test_b15_item_count_valid(self):
        """B15: Item count matches"""
        valid, error = GRAErrorValidator.validate_item_count_match(5, 5)
        assert valid
        assert error is None
    
    def test_b21_negative_price(self):
        """B21: Negative sale price"""
        valid, error = GRAErrorValidator.validate_unit_price_non_negative(Decimal("-10"))
        assert not valid
        assert "B21" in error
    
    def test_b21_valid_price(self):
        """B21: Valid sale price"""
        valid, error = GRAErrorValidator.validate_unit_price_non_negative(Decimal("100"))
        assert valid
        assert error is None
    
    def test_a06_invalid_unit_price_missing(self):
        """A06: Invalid unit price - missing"""
        valid, error = GRAErrorValidator.validate_unit_price_present(None)
        assert not valid
        assert "A06" in error
    
    def test_a06_invalid_unit_price_negative(self):
        """A06: Invalid unit price - negative"""
        valid, error = GRAErrorValidator.validate_unit_price_present("-10")
        assert not valid
        assert "A06" in error
    
    def test_a06_valid_unit_price(self):
        """A06: Valid unit price"""
        valid, error = GRAErrorValidator.validate_unit_price_present("100.50")
        assert valid
        assert error is None
    
    def test_a08_invalid_tax_code(self):
        """A08: Invalid tax code"""
        valid, error = GRAErrorValidator.validate_tax_code_valid("X")
        assert not valid
        assert "A08" in error
    
    def test_a08_valid_tax_code(self):
        """A08: Valid tax code"""
        valid, error = GRAErrorValidator.validate_tax_code_valid("B")
        assert valid
        assert error is None
    
    def test_a09_invalid_tax_rate(self):
        """A09: Invalid tax rate"""
        valid, error = GRAErrorValidator.validate_tax_rate_value("20")
        assert not valid
        assert "A09" in error
    
    def test_a09_valid_tax_rate(self):
        """A09: Valid tax rate"""
        valid, error = GRAErrorValidator.validate_tax_rate_value("15")
        assert valid
        assert error is None
    
    def test_a11_item_count_not_numeric(self):
        """A11: Item count not a number"""
        valid, error = GRAErrorValidator.validate_item_count_numeric("abc")
        assert not valid
        assert "A11" in error
    
    def test_a11_item_count_numeric(self):
        """A11: Item count is numeric"""
        valid, error = GRAErrorValidator.validate_item_count_numeric("5")
        assert valid
        assert error is None


class TestLevyErrors:
    """Tests for levy error codes B31, B32, B33, B34, B35"""
    
    def test_b31_levy_a_mismatch(self):
        """B31: Levy A amount discrepancy"""
        valid, error = GRAErrorValidator.validate_levy_a_amount(
            Decimal("2.5"),
            Decimal("3.0")
        )
        assert not valid
        assert "B31" in error
    
    def test_b31_levy_a_valid(self):
        """B31: Levy A amount correct"""
        valid, error = GRAErrorValidator.validate_levy_a_amount(
            Decimal("2.5"),
            Decimal("2.5")
        )
        assert valid
        assert error is None
    
    def test_b32_levy_b_mismatch(self):
        """B32: Levy B amount discrepancy"""
        valid, error = GRAErrorValidator.validate_levy_b_amount(
            Decimal("2.5"),
            Decimal("3.0")
        )
        assert not valid
        assert "B32" in error
    
    def test_b33_levy_c_mismatch(self):
        """B33: Levy C amount discrepancy"""
        valid, error = GRAErrorValidator.validate_levy_c_amount(
            Decimal("1.0"),
            Decimal("1.5")
        )
        assert not valid
        assert "B33" in error
    
    def test_b34_levy_d_mismatch(self):
        """B34: Levy D amount discrepancy"""
        valid, error = GRAErrorValidator.validate_levy_d_amount(
            Decimal("1.0"),
            Decimal("2.0")
        )
        assert not valid
        assert "B34" in error
    
    def test_b35_total_levy_mismatch(self):
        """B35: Total levy amount discrepancy"""
        valid, error = GRAErrorValidator.validate_total_levy_amount(
            Decimal("10.0"),
            Decimal("12.0")
        )
        assert not valid
        assert "B35" in error


class TestTINValidatorErrors:
    """Tests for TIN validator error codes T01, T03, T04, T05, T06"""
    
    def test_t01_invalid_tin(self):
        """T01: Invalid TIN number"""
        valid, error = GRAErrorValidator.validate_tin_valid("12345")
        assert not valid
        assert "T01" in error
    
    def test_t01_valid_tin(self):
        """T01: Valid TIN number"""
        valid, error = GRAErrorValidator.validate_tin_valid("12345678901")
        assert valid
        assert error is None
    
    def test_t03_tin_not_found(self):
        """T03: TIN number not found"""
        valid, error = GRAErrorValidator.validate_tin_found(False)
        assert not valid
        assert "T03" in error
    
    def test_t03_tin_found(self):
        """T03: TIN number found"""
        valid, error = GRAErrorValidator.validate_tin_found(True)
        assert valid
        assert error is None
    
    def test_t04_tin_stopped(self):
        """T04: TIN stopped"""
        valid, error = GRAErrorValidator.validate_tin_not_stopped(True)
        assert not valid
        assert "T04" in error
    
    def test_t04_tin_active(self):
        """T04: TIN active"""
        valid, error = GRAErrorValidator.validate_tin_not_stopped(False)
        assert valid
        assert error is None
    
    def test_t05_tin_protected(self):
        """T05: TIN protected"""
        valid, error = GRAErrorValidator.validate_tin_not_protected(True)
        assert not valid
        assert "T05" in error
    
    def test_t05_tin_not_protected(self):
        """T05: TIN not protected"""
        valid, error = GRAErrorValidator.validate_tin_not_protected(False)
        assert valid
        assert error is None
    
    def test_t06_incorrect_pin(self):
        """T06: Incorrect client TIN PIN"""
        valid, error = GRAErrorValidator.validate_tin_pin_correct(False)
        assert not valid
        assert "T06" in error
    
    def test_t06_correct_pin(self):
        """T06: Correct client TIN PIN"""
        valid, error = GRAErrorValidator.validate_tin_pin_correct(True)
        assert valid
        assert error is None


class TestSystemErrors:
    """Tests for system error codes D01, D05, D06, IS100, A13"""
    
    def test_d01_invoice_exists(self):
        """D01: Invoice already exists"""
        valid, error = GRAErrorValidator.validate_invoice_not_exists(True)
        assert not valid
        assert "D01" in error
    
    def test_d01_invoice_new(self):
        """D01: Invoice does not exist"""
        valid, error = GRAErrorValidator.validate_invoice_not_exists(False)
        assert valid
        assert error is None
    
    def test_d05_invoice_stamping(self):
        """D05: Invoice under stamping"""
        valid, error = GRAErrorValidator.validate_invoice_not_stamping(True)
        assert not valid
        assert "D05" in error
    
    def test_d05_invoice_not_stamping(self):
        """D05: Invoice not under stamping"""
        valid, error = GRAErrorValidator.validate_invoice_not_stamping(False)
        assert valid
        assert error is None
    
    def test_d06_stamping_engine_down(self):
        """D06: Stamping engine is down"""
        valid, error = GRAErrorValidator.validate_stamping_engine_available(False)
        assert not valid
        assert "D06" in error
    
    def test_d06_stamping_engine_up(self):
        """D06: Stamping engine is up"""
        valid, error = GRAErrorValidator.validate_stamping_engine_available(True)
        assert valid
        assert error is None
    
    def test_is100_internal_error(self):
        """IS100: Internal error"""
        valid, error = GRAErrorValidator.validate_no_internal_error(True)
        assert not valid
        assert "IS100" in error
    
    def test_is100_no_error(self):
        """IS100: No internal error"""
        valid, error = GRAErrorValidator.validate_no_internal_error(False)
        assert valid
        assert error is None
    
    def test_a13_database_unavailable(self):
        """A13: E-VAT unable to reach database"""
        valid, error = GRAErrorValidator.validate_database_available(False)
        assert not valid
        assert "A13" in error
    
    def test_a13_database_available(self):
        """A13: Database available"""
        valid, error = GRAErrorValidator.validate_database_available(True)
        assert valid
        assert error is None


class TestConsistencyErrors:
    """Tests for consistency error codes B06, B061, B27, B28, B29"""
    
    def test_b06_client_name_different(self):
        """B06: Client name different from previous"""
        valid, error = GRAErrorValidator.validate_client_name_consistency(
            "Company A",
            "Company B"
        )
        assert not valid
        assert "B06" in error
    
    def test_b06_client_name_same(self):
        """B06: Client name same as previous"""
        valid, error = GRAErrorValidator.validate_client_name_consistency(
            "Company A",
            "Company A"
        )
        assert valid
        assert error is None
    
    def test_b061_item_code_different(self):
        """B061: Item code different from previous"""
        valid, error = GRAErrorValidator.validate_item_code_consistency(
            "ITEM001",
            "ITEM002"
        )
        assert not valid
        assert "B061" in error
    
    def test_b061_item_code_same(self):
        """B061: Item code same as previous"""
        valid, error = GRAErrorValidator.validate_item_code_consistency(
            "ITEM001",
            "ITEM001"
        )
        assert valid
        assert error is None
    
    def test_b27_tax_rate_different(self):
        """B27: Tax rate different from previous"""
        valid, error = GRAErrorValidator.validate_tax_rate_consistency("15", "0")
        assert not valid
        assert "B27" in error
    
    def test_b27_tax_rate_same(self):
        """B27: Tax rate same as previous"""
        valid, error = GRAErrorValidator.validate_tax_rate_consistency("15", "15")
        assert valid
        assert error is None
    
    def test_b28_client_tin_different(self):
        """B28: Client tax number different"""
        valid, error = GRAErrorValidator.validate_client_tin_consistency(
            "TIN001",
            "TIN002"
        )
        assert not valid
        assert "B28" in error
    
    def test_b28_client_tin_same(self):
        """B28: Client tax number same"""
        valid, error = GRAErrorValidator.validate_client_tin_consistency(
            "TIN001",
            "TIN001"
        )
        assert valid
        assert error is None
    
    def test_b29_client_tin_for_another(self):
        """B29: Client tax number for another client"""
        valid, error = GRAErrorValidator.validate_client_tin_not_for_another(
            "TIN001",
            ["TIN001", "TIN002"]
        )
        assert not valid
        assert "B29" in error
    
    def test_b29_client_tin_unique(self):
        """B29: Client tax number unique"""
        valid, error = GRAErrorValidator.validate_client_tin_not_for_another(
            "TIN003",
            ["TIN001", "TIN002"]
        )
        assert valid
        assert error is None


class TestDiscountErrors:
    """Tests for discount error code A07"""
    
    def test_a07_invalid_discount_negative(self):
        """A07: Invalid discount - negative"""
        valid, error = GRAErrorValidator.validate_discount_valid(Decimal("-10"))
        assert not valid
        assert "A07" in error
    
    def test_a07_valid_discount(self):
        """A07: Valid discount"""
        valid, error = GRAErrorValidator.validate_discount_valid(Decimal("10"))
        assert valid
        assert error is None


class TestErrorCodeUtilities:
    """Tests for error code utility functions"""
    
    def test_get_error_code_description(self):
        """Get description for valid error code"""
        desc = GRAErrorValidator.get_error_code_description("B16")
        assert "Total amount mismatch" in desc
    
    def test_get_error_code_description_invalid(self):
        """Get description for invalid error code"""
        desc = GRAErrorValidator.get_error_code_description("INVALID")
        assert "Unknown error code" in desc
    
    def test_get_all_error_codes(self):
        """Get all error codes"""
        codes = GRAErrorValidator.get_all_error_codes()
        assert len(codes) > 40  # Should have 50+ error codes
        assert "B16" in codes
        assert "A01" in codes
        assert "T01" in codes
        assert "D06" in codes

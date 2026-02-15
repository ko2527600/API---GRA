"""GRA Error Code Validators - Comprehensive validation for all 50+ GRA error codes"""
from enum import Enum
from typing import Tuple, Optional, Dict, List
from decimal import Decimal


class GRAErrorCode(Enum):
    """All GRA error codes with descriptions"""
    
    # Authentication Errors
    A01 = "Company credentials do not exist"
    B01 = "Incorrect client TIN PIN"
    
    # Invoice/Refund Errors
    B16 = "Total amount mismatch"
    B18 = "Total VAT mismatch"
    B19 = "Invoice reference missing"
    B20 = "Invoice reference already sent"
    B22 = "Zero total invoice not supported"
    B70 = "Wrong currency"
    A05 = "Missing original invoice number (for refunds)"
    
    # Item Errors
    B05 = "Client name missing"
    B051 = "Tax number format not accepted"
    B06 = "Client name different from previous"
    B061 = "Item code different from previous"
    B07 = "Code missing"
    B09 = "Description missing"
    B10 = "Quantity missing"
    B11 = "Quantity is negative"
    B12 = "Quantity not a number"
    B13 = "Tax rate not accepted"
    B15 = "Item count mismatch"
    B21 = "Negative sale price"
    B27 = "Tax rate different from previous"
    B28 = "Client tax number different"
    B29 = "Client tax number for another client"
    B31 = "Levy A amount discrepancy"
    B32 = "Levy B amount discrepancy"
    B33 = "Levy C amount discrepancy"
    B34 = "Levy D amount discrepancy"
    B35 = "Total levy amount discrepancy"
    A06 = "Invalid unit price"
    A07 = "Invalid discount"
    A08 = "Invalid tax code"
    A09 = "Invalid tax rate"
    A11 = "Item count not a number"
    
    # TIN Validator Errors
    T01 = "Invalid TIN number"
    T03 = "TIN number not found"
    T04 = "TIN stopped"
    T05 = "TIN protected"
    T06 = "Incorrect client TIN PIN"
    
    # System Errors
    D01 = "Invoice already exists"
    D05 = "Invoice under stamping"
    D06 = "Stamping engine is down"
    IS100 = "Internal error"
    A13 = "E-VAT unable to reach database"


class GRAErrorValidator:
    """Validates data against all GRA error codes"""
    
    # Tolerance for decimal comparisons (0.01 GHS)
    DECIMAL_TOLERANCE = Decimal("0.01")
    
    @staticmethod
    def validate_company_credentials_exist(company_tin: Optional[str], 
                                          company_name: Optional[str],
                                          security_key: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: A01 - Company credentials do not exist
        """
        if not company_tin or not company_name or not security_key:
            return False, "A01: Company credentials do not exist"
        return True, None
    
    @staticmethod
    def validate_client_tin_pin(client_tin: Optional[str], 
                               client_tin_pin: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: B01 - Incorrect client TIN PIN
        """
        if client_tin and not client_tin_pin:
            return False, "B01: Incorrect client TIN PIN"
        return True, None
    
    @staticmethod
    def validate_total_amount(total_amount: Decimal, 
                             items_total: Decimal,
                             total_vat: Decimal,
                             total_levy: Decimal) -> Tuple[bool, Optional[str]]:
        """
        Validates: B16 - Total amount mismatch
        TOTAL_AMOUNT should equal sum of items + VAT + levies
        """
        expected_total = items_total + total_vat + total_levy
        if abs(total_amount - expected_total) > GRAErrorValidator.DECIMAL_TOLERANCE:
            return False, f"B16: Total amount mismatch. Expected {expected_total}, got {total_amount}"
        return True, None
    
    @staticmethod
    def validate_total_vat(total_vat: Decimal, 
                          items_vat_sum: Decimal) -> Tuple[bool, Optional[str]]:
        """
        Validates: B18 - Total VAT mismatch
        TOTAL_VAT should equal sum of all item VATs
        """
        if abs(total_vat - items_vat_sum) > GRAErrorValidator.DECIMAL_TOLERANCE:
            return False, f"B18: Total VAT mismatch. Expected {items_vat_sum}, got {total_vat}"
        return True, None
    
    @staticmethod
    def validate_invoice_reference_present(invoice_ref: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: B19 - Invoice reference missing
        """
        if not invoice_ref or invoice_ref.strip() == "":
            return False, "B19: Invoice reference missing"
        return True, None
    
    @staticmethod
    def validate_invoice_not_duplicate(invoice_num: str, 
                                      existing_invoices: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: B20 - Invoice reference already sent
        """
        if invoice_num in existing_invoices:
            return False, f"B20: Invoice reference {invoice_num} already sent"
        return True, None
    
    @staticmethod
    def validate_non_zero_total(total_amount: Decimal) -> Tuple[bool, Optional[str]]:
        """
        Validates: B22 - Zero total invoice not supported
        """
        if total_amount == 0:
            return False, "B22: Zero total invoice not supported"
        return True, None
    
    @staticmethod
    def validate_currency_ghs(currency: str) -> Tuple[bool, Optional[str]]:
        """
        Validates: B70 - Wrong currency
        """
        if currency != "GHS":
            return False, f"B70: Wrong currency. Expected GHS, got {currency}"
        return True, None
    
    @staticmethod
    def validate_refund_id_present(refund_id: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: A05 - Missing original invoice number (for refunds)
        """
        if not refund_id or refund_id.strip() == "":
            return False, "A05: Missing original invoice number for refund"
        return True, None
    
    @staticmethod
    def validate_client_name_present(client_name: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: B05 - Client name missing
        """
        if not client_name or client_name.strip() == "":
            return False, "B05: Client name missing"
        return True, None
    
    @staticmethod
    def validate_tin_format(tin: str) -> Tuple[bool, Optional[str]]:
        """
        Validates: B051 - Tax number format not accepted
        TIN must be 11 or 15 characters
        """
        if not tin:
            return False, "B051: Tax number format not accepted (empty)"
        
        if len(tin) not in [11, 15]:
            return False, f"B051: Tax number format not accepted (length {len(tin)}, expected 11 or 15)"
        
        if not tin.isalnum():
            return False, "B051: Tax number format not accepted (non-alphanumeric)"
        
        return True, None
    
    @staticmethod
    def validate_client_name_consistency(client_name: str, 
                                        previous_client_name: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: B06 - Client name different from previous
        """
        if previous_client_name and client_name != previous_client_name:
            return False, f"B06: Client name different from previous. Got {client_name}, expected {previous_client_name}"
        return True, None
    
    @staticmethod
    def validate_item_code_consistency(item_code: str, 
                                      previous_item_code: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: B061 - Item code different from previous
        """
        if previous_item_code and item_code != previous_item_code:
            return False, f"B061: Item code different from previous. Got {item_code}, expected {previous_item_code}"
        return True, None
    
    @staticmethod
    def validate_item_code_present(item_code: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: B07 - Code missing
        """
        if not item_code or item_code.strip() == "":
            return False, "B07: Item code missing"
        return True, None
    
    @staticmethod
    def validate_item_description_present(description: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: B09 - Description missing
        """
        if not description or description.strip() == "":
            return False, "B09: Item description missing"
        return True, None
    
    @staticmethod
    def validate_quantity_present(quantity: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: B10 - Quantity missing
        """
        if quantity is None or quantity == "":
            return False, "B10: Quantity missing"
        return True, None
    
    @staticmethod
    def validate_quantity_non_negative(quantity: Decimal) -> Tuple[bool, Optional[str]]:
        """
        Validates: B11 - Quantity is negative
        """
        if quantity < 0:
            return False, f"B11: Quantity is negative ({quantity})"
        return True, None
    
    @staticmethod
    def validate_quantity_numeric(quantity: str) -> Tuple[bool, Optional[str]]:
        """
        Validates: B12 - Quantity not a number
        """
        try:
            Decimal(quantity)
            return True, None
        except:
            return False, f"B12: Quantity not a number ({quantity})"
    
    @staticmethod
    def validate_tax_rate_valid(tax_rate: str, tax_code: str) -> Tuple[bool, Optional[str]]:
        """
        Validates: B13 - Tax rate not accepted
        """
        valid_rates = {
            "A": [Decimal("0")],
            "B": [Decimal("15")],
            "C": [Decimal("0")],
            "D": [Decimal("0")],
            "E": [Decimal("3")],
        }
        
        try:
            rate = Decimal(tax_rate)
            if tax_code not in valid_rates:
                return False, f"B13: Unknown tax code {tax_code}"
            
            if rate not in valid_rates[tax_code]:
                return False, f"B13: Tax rate {rate} not accepted for tax code {tax_code}"
            
            return True, None
        except:
            return False, f"B13: Tax rate not a valid number ({tax_rate})"
    
    @staticmethod
    def validate_item_count_match(item_count: int, 
                                 actual_items: int) -> Tuple[bool, Optional[str]]:
        """
        Validates: B15 - Item count mismatch
        """
        if item_count != actual_items:
            return False, f"B15: Item count mismatch. Expected {item_count}, got {actual_items}"
        return True, None
    
    @staticmethod
    def validate_unit_price_non_negative(unit_price: Decimal) -> Tuple[bool, Optional[str]]:
        """
        Validates: B21 - Negative sale price
        """
        if unit_price < 0:
            return False, f"B21: Negative sale price ({unit_price})"
        return True, None
    
    @staticmethod
    def validate_tax_rate_consistency(tax_rate: str, 
                                     previous_tax_rate: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: B27 - Tax rate different from previous
        """
        if previous_tax_rate and tax_rate != previous_tax_rate:
            return False, f"B27: Tax rate different from previous. Got {tax_rate}, expected {previous_tax_rate}"
        return True, None
    
    @staticmethod
    def validate_client_tin_consistency(client_tin: str, 
                                       previous_client_tin: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: B28 - Client tax number different
        """
        if previous_client_tin and client_tin != previous_client_tin:
            return False, f"B28: Client tax number different. Got {client_tin}, expected {previous_client_tin}"
        return True, None
    
    @staticmethod
    def validate_client_tin_not_for_another(client_tin: str, 
                                           other_client_tins: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: B29 - Client tax number for another client
        """
        if client_tin in other_client_tins:
            return False, f"B29: Client tax number {client_tin} belongs to another client"
        return True, None
    
    @staticmethod
    def validate_levy_a_amount(levy_a: Decimal, 
                              expected_levy_a: Decimal) -> Tuple[bool, Optional[str]]:
        """
        Validates: B31 - Levy A amount discrepancy
        """
        if abs(levy_a - expected_levy_a) > GRAErrorValidator.DECIMAL_TOLERANCE:
            return False, f"B31: Levy A amount discrepancy. Expected {expected_levy_a}, got {levy_a}"
        return True, None
    
    @staticmethod
    def validate_levy_b_amount(levy_b: Decimal, 
                              expected_levy_b: Decimal) -> Tuple[bool, Optional[str]]:
        """
        Validates: B32 - Levy B amount discrepancy
        """
        if abs(levy_b - expected_levy_b) > GRAErrorValidator.DECIMAL_TOLERANCE:
            return False, f"B32: Levy B amount discrepancy. Expected {expected_levy_b}, got {levy_b}"
        return True, None
    
    @staticmethod
    def validate_levy_c_amount(levy_c: Decimal, 
                              expected_levy_c: Decimal) -> Tuple[bool, Optional[str]]:
        """
        Validates: B33 - Levy C amount discrepancy
        """
        if abs(levy_c - expected_levy_c) > GRAErrorValidator.DECIMAL_TOLERANCE:
            return False, f"B33: Levy C amount discrepancy. Expected {expected_levy_c}, got {levy_c}"
        return True, None
    
    @staticmethod
    def validate_levy_d_amount(levy_d: Decimal, 
                              expected_levy_d: Decimal) -> Tuple[bool, Optional[str]]:
        """
        Validates: B34 - Levy D amount discrepancy
        """
        if abs(levy_d - expected_levy_d) > GRAErrorValidator.DECIMAL_TOLERANCE:
            return False, f"B34: Levy D amount discrepancy. Expected {expected_levy_d}, got {levy_d}"
        return True, None
    
    @staticmethod
    def validate_total_levy_amount(total_levy: Decimal, 
                                  expected_total_levy: Decimal) -> Tuple[bool, Optional[str]]:
        """
        Validates: B35 - Total levy amount discrepancy
        """
        if abs(total_levy - expected_total_levy) > GRAErrorValidator.DECIMAL_TOLERANCE:
            return False, f"B35: Total levy amount discrepancy. Expected {expected_total_levy}, got {total_levy}"
        return True, None
    
    @staticmethod
    def validate_unit_price_present(unit_price: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validates: A06 - Invalid unit price
        """
        if unit_price is None or unit_price == "":
            return False, "A06: Invalid unit price (missing)"
        
        try:
            price = Decimal(unit_price)
            if price < 0:
                return False, f"A06: Invalid unit price (negative: {price})"
            return True, None
        except:
            return False, f"A06: Invalid unit price (not numeric: {unit_price})"
    
    @staticmethod
    def validate_discount_valid(discount: Decimal) -> Tuple[bool, Optional[str]]:
        """
        Validates: A07 - Invalid discount
        """
        if discount < 0:
            return False, f"A07: Invalid discount (negative: {discount})"
        return True, None
    
    @staticmethod
    def validate_tax_code_valid(tax_code: str) -> Tuple[bool, Optional[str]]:
        """
        Validates: A08 - Invalid tax code
        """
        valid_codes = ["A", "B", "C", "D", "E"]
        if tax_code not in valid_codes:
            return False, f"A08: Invalid tax code ({tax_code}). Must be one of {valid_codes}"
        return True, None
    
    @staticmethod
    def validate_tax_rate_value(tax_rate: str) -> Tuple[bool, Optional[str]]:
        """
        Validates: A09 - Invalid tax rate
        """
        valid_rates = [Decimal("0"), Decimal("3"), Decimal("15")]
        try:
            rate = Decimal(tax_rate)
            if rate not in valid_rates:
                return False, f"A09: Invalid tax rate ({rate}). Must be one of {valid_rates}"
            return True, None
        except:
            return False, f"A09: Invalid tax rate (not numeric: {tax_rate})"
    
    @staticmethod
    def validate_item_count_numeric(item_count: str) -> Tuple[bool, Optional[str]]:
        """
        Validates: A11 - Item count not a number
        """
        try:
            int(item_count)
            return True, None
        except:
            return False, f"A11: Item count not a number ({item_count})"
    
    @staticmethod
    def validate_tin_valid(tin: str) -> Tuple[bool, Optional[str]]:
        """
        Validates: T01 - Invalid TIN number
        """
        if not tin or len(tin) not in [11, 15]:
            return False, f"T01: Invalid TIN number ({tin})"
        if not tin.isalnum():
            return False, f"T01: Invalid TIN number (non-alphanumeric: {tin})"
        return True, None
    
    @staticmethod
    def validate_tin_found(tin_exists: bool) -> Tuple[bool, Optional[str]]:
        """
        Validates: T03 - TIN number not found
        """
        if not tin_exists:
            return False, "T03: TIN number not found"
        return True, None
    
    @staticmethod
    def validate_tin_not_stopped(tin_stopped: bool) -> Tuple[bool, Optional[str]]:
        """
        Validates: T04 - TIN stopped
        """
        if tin_stopped:
            return False, "T04: TIN stopped"
        return True, None
    
    @staticmethod
    def validate_tin_not_protected(tin_protected: bool) -> Tuple[bool, Optional[str]]:
        """
        Validates: T05 - TIN protected
        """
        if tin_protected:
            return False, "T05: TIN protected"
        return True, None
    
    @staticmethod
    def validate_tin_pin_correct(tin_pin_correct: bool) -> Tuple[bool, Optional[str]]:
        """
        Validates: T06 - Incorrect client TIN PIN
        """
        if not tin_pin_correct:
            return False, "T06: Incorrect client TIN PIN"
        return True, None
    
    @staticmethod
    def validate_invoice_not_exists(invoice_exists: bool) -> Tuple[bool, Optional[str]]:
        """
        Validates: D01 - Invoice already exists
        """
        if invoice_exists:
            return False, "D01: Invoice already exists"
        return True, None
    
    @staticmethod
    def validate_invoice_not_stamping(invoice_stamping: bool) -> Tuple[bool, Optional[str]]:
        """
        Validates: D05 - Invoice under stamping
        """
        if invoice_stamping:
            return False, "D05: Invoice under stamping"
        return True, None
    
    @staticmethod
    def validate_stamping_engine_available(engine_available: bool) -> Tuple[bool, Optional[str]]:
        """
        Validates: D06 - Stamping engine is down
        """
        if not engine_available:
            return False, "D06: Stamping engine is down"
        return True, None
    
    @staticmethod
    def validate_no_internal_error(error_occurred: bool) -> Tuple[bool, Optional[str]]:
        """
        Validates: IS100 - Internal error
        """
        if error_occurred:
            return False, "IS100: Internal error"
        return True, None
    
    @staticmethod
    def validate_database_available(db_available: bool) -> Tuple[bool, Optional[str]]:
        """
        Validates: A13 - E-VAT unable to reach database
        """
        if not db_available:
            return False, "A13: E-VAT unable to reach database"
        return True, None
    
    @staticmethod
    def get_error_code_description(error_code: str) -> str:
        """Get human-readable description for an error code"""
        try:
            return GRAErrorCode[error_code].value
        except KeyError:
            return f"Unknown error code: {error_code}"
    
    @staticmethod
    def get_all_error_codes() -> Dict[str, str]:
        """Get all error codes and their descriptions"""
        return {code.name: code.value for code in GRAErrorCode}

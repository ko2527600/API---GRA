"""Business logic validation for GRA submissions"""
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class BusinessLogicValidator:
    """Validates business logic rules for invoices, refunds, and purchases"""
    
    @staticmethod
    def validate_invoice_totals(
        header: Dict,
        items: List[Dict]
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate invoice totals match item calculations
        
        Returns: (is_valid, error_code, error_message)
        """
        try:
            # Parse header totals
            total_vat = Decimal(str(header.get("TOTAL_VAT", "0")))
            total_levy = Decimal(str(header.get("TOTAL_LEVY", "0")))
            total_amount = Decimal(str(header.get("TOTAL_AMOUNT", "0")))
            
            # Calculate from items
            calculated_vat = Decimal("0")
            calculated_levy = Decimal("0")
            calculated_total = Decimal("0")
            
            for item in items:
                item_vat = Decimal(str(item.get("vat", 0)))
                item_levy_a = Decimal(str(item.get("LEVY_AMOUNT_A", 0)))
                item_levy_b = Decimal(str(item.get("LEVY_AMOUNT_B", 0)))
                item_levy_c = Decimal(str(item.get("LEVY_AMOUNT_C", 0)))
                item_levy_d = Decimal(str(item.get("LEVY_AMOUNT_D", 0)))
                item_total = Decimal(str(item.get("item_total", 0)))
                
                calculated_vat += item_vat
                calculated_levy += item_levy_a + item_levy_b + item_levy_c + item_levy_d
                calculated_total += item_total
            
            # Round for comparison
            calculated_vat = calculated_vat.quantize(Decimal("0.01"))
            calculated_levy = calculated_levy.quantize(Decimal("0.01"))
            calculated_total = calculated_total.quantize(Decimal("0.01"))
            
            tolerance = Decimal("0.01")
            
            # Check VAT
            if abs(calculated_vat - total_vat) > tolerance:
                return False, "B18", f"Total VAT mismatch: expected {calculated_vat}, got {total_vat}"
            
            # Check Levy
            if abs(calculated_levy - total_levy) > tolerance:
                return False, "B34", f"Total levy mismatch: expected {calculated_levy}, got {total_levy}"
            
            # Check Total Amount
            if abs(calculated_total - total_amount) > tolerance:
                return False, "B16", f"Total amount mismatch: expected {calculated_total}, got {total_amount}"
            
            return True, None, None
        except (ValueError, TypeError) as e:
            return False, "B16", f"Error calculating totals: {str(e)}"
    
    @staticmethod
    def validate_items_count(
        header: Dict,
        items: List[Dict]
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate that ITEMS_COUNTS matches actual item list length
        
        Returns: (is_valid, error_code, error_message)
        """
        try:
            expected_count = int(header.get("ITEMS_COUNTS", 0))
            actual_count = len(items)
            
            if expected_count != actual_count:
                return False, "B15", f"Item count mismatch: expected {expected_count}, got {actual_count}"
            
            return True, None, None
        except (ValueError, TypeError) as e:
            return False, "B15", f"Error validating item count: {str(e)}"
    
    @staticmethod
    def validate_item_quantities(items: List[Dict]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate that all item quantities are positive
        
        Returns: (is_valid, error_code, error_message)
        """
        for idx, item in enumerate(items):
            try:
                quantity = Decimal(str(item.get("QUANTITY", 0)))
                
                if quantity <= 0:
                    return False, "B11", f"Item {idx}: Quantity must be positive, got {quantity}"
                
            except Exception:
                return False, "B12", f"Item {idx}: Quantity must be numeric"
        
        return True, None, None
    
    @staticmethod
    def validate_item_prices(items: List[Dict]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate that all item unit prices are positive
        
        Returns: (is_valid, error_code, error_message)
        """
        for idx, item in enumerate(items):
            try:
                unit_price = Decimal(str(item.get("UNITYPRICE", 0)))
                
                if unit_price <= 0:
                    return False, "B21", f"Item {idx}: Unit price must be positive, got {unit_price}"
                
            except Exception:
                return False, "A06", f"Item {idx}: Unit price must be numeric"
        
        return True, None, None
    
    @staticmethod
    def validate_client_name(header: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate that CLIENT_NAME is provided
        
        Returns: (is_valid, error_code, error_message)
        """
        client_name = header.get("CLIENT_NAME", "").strip()
        
        if not client_name:
            return False, "B05", "CLIENT_NAME is required"
        
        return True, None, None
    
    @staticmethod
    def validate_client_tin_format(header: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate CLIENT_TIN format (11 or 15 characters)
        
        Returns: (is_valid, error_code, error_message)
        """
        client_tin = header.get("CLIENT_TIN")
        
        if client_tin is None:
            # CLIENT_TIN is optional
            return True, None, None
        
        if len(str(client_tin)) not in [11, 15]:
            return False, "B051", f"CLIENT_TIN must be 11 or 15 characters, got {len(str(client_tin))}"
        
        return True, None, None
    
    @staticmethod
    def validate_currency(header: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate CURRENCY is GHS
        
        Returns: (is_valid, error_code, error_message)
        """
        currency = header.get("CURRENCY", "").upper()
        
        if currency != "GHS":
            return False, "B70", f"CURRENCY must be GHS, got {currency}"
        
        return True, None, None
    
    @staticmethod
    def validate_exchange_rate(header: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate EXCHANGE_RATE is 1 for GHS
        
        Returns: (is_valid, error_code, error_message)
        """
        try:
            exchange_rate = Decimal(str(header.get("EXCHANGE_RATE", "1")))
            
            if exchange_rate != Decimal("1"):
                return False, "B70", f"EXCHANGE_RATE must be 1 for GHS, got {exchange_rate}"
            
            return True, None, None
        except (ValueError, TypeError):
            return False, "B70", "EXCHANGE_RATE must be numeric"
    
    @staticmethod
    def validate_invoice_date_format(header: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate INVOICE_DATE format (YYYY-MM-DD)
        
        Returns: (is_valid, error_code, error_message)
        """
        invoice_date = header.get("INVOICE_DATE", "")
        
        try:
            datetime.strptime(invoice_date, "%Y-%m-%d")
            return True, None, None
        except ValueError:
            return False, "B19", f"INVOICE_DATE must be YYYY-MM-DD format, got {invoice_date}"
    
    @staticmethod
    def validate_tax_codes(items: List[Dict]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate all TAXCODE values are valid (A, B, C, D, E)
        
        Returns: (is_valid, error_code, error_message)
        """
        valid_codes = ["A", "B", "C", "D", "E"]
        
        for idx, item in enumerate(items):
            tax_code = item.get("TAXCODE", "").upper()
            
            if tax_code not in valid_codes:
                return False, "A08", f"Item {idx}: TAXCODE must be one of {valid_codes}, got {tax_code}"
        
        return True, None, None
    
    @staticmethod
    def validate_tax_rates(items: List[Dict]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate all TAXRATE values are valid (0, 15, 3)
        
        Returns: (is_valid, error_code, error_message)
        """
        valid_rates = ["0", "15", "3"]
        
        for idx, item in enumerate(items):
            tax_rate = str(item.get("TAXRATE", "")).strip()
            
            if tax_rate not in valid_rates:
                return False, "A09", f"Item {idx}: TAXRATE must be one of {valid_rates}, got {tax_rate}"
        
        return True, None, None
    
    @staticmethod
    def validate_levy_amounts(items: List[Dict]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate all levy amounts are non-negative
        
        Returns: (is_valid, error_code, error_message)
        """
        levy_fields = ["LEVY_AMOUNT_A", "LEVY_AMOUNT_B", "LEVY_AMOUNT_D"]
        
        for idx, item in enumerate(items):
            for levy_field in levy_fields:
                try:
                    levy_amount = Decimal(str(item.get(levy_field, "0")))
                    
                    if levy_amount < 0:
                        error_code = {
                            "LEVY_AMOUNT_A": "B31",
                            "LEVY_AMOUNT_B": "B32",
                            "LEVY_AMOUNT_D": "B35",
                        }.get(levy_field, "B34")
                        
                        return False, error_code, f"Item {idx}: {levy_field} cannot be negative, got {levy_amount}"
                
                except (ValueError, TypeError):
                    return False, "B34", f"Item {idx}: {levy_field} must be numeric"
        
        return True, None, None
    
    @staticmethod
    def validate_refund_id_provided(header: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate REFUND_ID is provided for refund submissions
        
        Returns: (is_valid, error_code, error_message)
        """
        flag = header.get("FLAG", "").upper()
        
        # Only validate for REFUND and PARTIAL_REFUND flags
        if flag not in ["REFUND", "PARTIAL_REFUND"]:
            return True, None, None
        
        refund_id = header.get("REFUND_ID", "").strip()
        
        if not refund_id:
            return False, "A05", "REFUND_ID is required for refund submissions"
        
        return True, None, None
    
    @staticmethod
    def validate_computation_type(header: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate COMPUTATION_TYPE is INCLUSIVE or EXCLUSIVE
        
        Returns: (is_valid, error_code, error_message)
        """
        computation_type = header.get("COMPUTATION_TYPE", "").upper()
        
        if computation_type not in ["INCLUSIVE", "EXCLUSIVE"]:
            return False, "B70", f"COMPUTATION_TYPE must be INCLUSIVE or EXCLUSIVE, got {computation_type}"
        
        return True, None, None
    
    @staticmethod
    def validate_flag_type(header: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate FLAG is valid (INVOICE, REFUND, PROFORMA, PARTIAL_REFUND, PURCHASE)
        
        Returns: (is_valid, error_code, error_message)
        """
        valid_flags = ["INVOICE", "REFUND", "PROFORMA", "PARTIAL_REFUND", "PURCHASE"]
        flag = header.get("FLAG", "").upper()
        
        if flag not in valid_flags:
            return False, "B70", f"FLAG must be one of {valid_flags}, got {flag}"
        
        return True, None, None
    
    @staticmethod
    def validate_item_discounts(items: List[Dict]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate all item discounts are non-negative
        
        Returns: (is_valid, error_code, error_message)
        """
        for idx, item in enumerate(items):
            try:
                discount = Decimal(str(item.get("ITMDISCOUNT", "0")))
                
                if discount < 0:
                    return False, "A07", f"Item {idx}: Discount cannot be negative, got {discount}"
                
            except Exception:
                return False, "A07", f"Item {idx}: Discount must be numeric"
        
        return True, None, None
    
    @staticmethod
    def validate_header_discount(header: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate header-level discount is non-negative
        
        Returns: (is_valid, error_code, error_message)
        """
        discount_amount = header.get("DISCOUNT_AMOUNT", "0")
        
        try:
            discount = Decimal(str(discount_amount))
            
            if discount < 0:
                return False, "A07", f"Header discount cannot be negative, got {discount}"
            
            return True, None, None
        except Exception:
            return False, "A07", "Header discount must be numeric"
    
    @staticmethod
    def validate_all_invoice_business_logic(
        header: Dict,
        items: List[Dict]
    ) -> Tuple[bool, List[Dict]]:
        """
        Run all business logic validations for an invoice
        
        Returns: (is_valid, list_of_errors)
        where each error is: {"field": str, "error_code": str, "message": str}
        """
        errors = []
        
        # Define validation functions to run
        validations = [
            ("header", BusinessLogicValidator.validate_computation_type, (header,)),
            ("header", BusinessLogicValidator.validate_flag_type, (header,)),
            ("header", BusinessLogicValidator.validate_client_name, (header,)),
            ("header", BusinessLogicValidator.validate_client_tin_format, (header,)),
            ("header", BusinessLogicValidator.validate_currency, (header,)),
            ("header", BusinessLogicValidator.validate_exchange_rate, (header,)),
            ("header", BusinessLogicValidator.validate_invoice_date_format, (header,)),
            ("header", BusinessLogicValidator.validate_header_discount, (header,)),
            ("items", BusinessLogicValidator.validate_items_count, (header, items)),
            ("items", BusinessLogicValidator.validate_item_quantities, (items,)),
            ("items", BusinessLogicValidator.validate_item_prices, (items,)),
            ("items", BusinessLogicValidator.validate_item_discounts, (items,)),
            ("items", BusinessLogicValidator.validate_tax_codes, (items,)),
            ("items", BusinessLogicValidator.validate_tax_rates, (items,)),
            ("items", BusinessLogicValidator.validate_levy_amounts, (items,)),
            ("totals", BusinessLogicValidator.validate_invoice_totals, (header, items)),
        ]
        
        # Run all validations
        for field_type, validation_func, args in validations:
            is_valid, error_code, error_message = validation_func(*args)
            
            if not is_valid:
                errors.append({
                    "field": field_type,
                    "error_code": error_code,
                    "message": error_message
                })
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_all_refund_business_logic(
        header: Dict,
        items: List[Dict]
    ) -> Tuple[bool, List[Dict]]:
        """
        Run all business logic validations for a refund
        
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate REFUND_ID is provided
        is_valid, error_code, error_message = BusinessLogicValidator.validate_refund_id_provided(header)
        if not is_valid:
            errors.append({
                "field": "header",
                "error_code": error_code,
                "message": error_message
            })
        
        # Run same validations as invoice (except FLAG validation)
        validations = [
            ("header", BusinessLogicValidator.validate_computation_type, (header,)),
            ("header", BusinessLogicValidator.validate_client_name, (header,)),
            ("header", BusinessLogicValidator.validate_client_tin_format, (header,)),
            ("header", BusinessLogicValidator.validate_currency, (header,)),
            ("header", BusinessLogicValidator.validate_exchange_rate, (header,)),
            ("header", BusinessLogicValidator.validate_invoice_date_format, (header,)),
            ("header", BusinessLogicValidator.validate_header_discount, (header,)),
            ("items", BusinessLogicValidator.validate_items_count, (header, items)),
            ("items", BusinessLogicValidator.validate_item_quantities, (items,)),
            ("items", BusinessLogicValidator.validate_item_prices, (items,)),
            ("items", BusinessLogicValidator.validate_item_discounts, (items,)),
            ("items", BusinessLogicValidator.validate_tax_codes, (items,)),
            ("items", BusinessLogicValidator.validate_tax_rates, (items,)),
            ("items", BusinessLogicValidator.validate_levy_amounts, (items,)),
            ("totals", BusinessLogicValidator.validate_invoice_totals, (header, items)),
        ]
        
        for field_type, validation_func, args in validations:
            is_valid, error_code, error_message = validation_func(*args)
            
            if not is_valid:
                errors.append({
                    "field": field_type,
                    "error_code": error_code,
                    "message": error_message
                })
        
        return len(errors) == 0, errors

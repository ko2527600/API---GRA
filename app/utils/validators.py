"""Validation utilities for GRA compliance"""
import re
from datetime import datetime
from typing import Tuple, Optional

class GRAValidator:
    """Validates data against GRA specifications"""
    
    @staticmethod
    def validate_tin_format(tin: str) -> Tuple[bool, Optional[str]]:
        """Validate TIN format (11 or 15 characters)"""
        if not tin:
            return False, "TIN cannot be empty"
        
        if len(tin) not in [11, 15]:
            return False, f"TIN must be 11 or 15 characters, got {len(tin)}"
        
        if not tin.isalnum():
            return False, "TIN must contain only alphanumeric characters"
        
        return True, None
    
    @staticmethod
    def validate_date_format(date_str: str) -> Tuple[bool, Optional[str]]:
        """Validate date format (YYYY-MM-DD)"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True, None
        except ValueError:
            return False, f"Date must be in YYYY-MM-DD format, got {date_str}"
    
    @staticmethod
    def validate_currency(currency: str) -> Tuple[bool, Optional[str]]:
        """Validate currency (must be GHS)"""
        if currency != "GHS":
            return False, f"Currency must be GHS, got {currency}"
        return True, None
    
    @staticmethod
    def validate_exchange_rate(rate: str) -> Tuple[bool, Optional[str]]:
        """Validate exchange rate (must be 1 for GHS)"""
        try:
            rate_float = float(rate)
            if rate_float != 1.0:
                return False, f"Exchange rate must be 1 for GHS, got {rate}"
            return True, None
        except ValueError:
            return False, f"Exchange rate must be numeric, got {rate}"
    
    @staticmethod
    def validate_tax_code(code: str) -> Tuple[bool, Optional[str]]:
        """Validate tax code (A, B, C, D, E)"""
        valid_codes = ["A", "B", "C", "D", "E"]
        if code not in valid_codes:
            return False, f"Tax code must be one of {valid_codes}, got {code}"
        return True, None
    
    @staticmethod
    def validate_tax_rate(rate: str, tax_code: str) -> Tuple[bool, Optional[str]]:
        """Validate tax rate matches tax code"""
        valid_rates = {
            "A": [0],
            "B": [15],
            "C": [0],
            "D": [0],
            "E": [3],
        }
        
        try:
            rate_float = float(rate)
            if tax_code not in valid_rates:
                return False, f"Unknown tax code: {tax_code}"
            
            if rate_float not in valid_rates[tax_code]:
                return False, f"Tax rate {rate} not valid for tax code {tax_code}"
            
            return True, None
        except ValueError:
            return False, f"Tax rate must be numeric, got {rate}"
    
    @staticmethod
    def validate_positive_number(value: str, field_name: str) -> Tuple[bool, Optional[str]]:
        """Validate that a value is a positive number"""
        try:
            num = float(value)
            if num < 0:
                return False, f"{field_name} cannot be negative, got {value}"
            return True, None
        except ValueError:
            return False, f"{field_name} must be numeric, got {value}"
    
    @staticmethod
    def validate_non_negative_number(value: str, field_name: str) -> Tuple[bool, Optional[str]]:
        """Validate that a value is a non-negative number"""
        try:
            num = float(value)
            if num < 0:
                return False, f"{field_name} cannot be negative, got {value}"
            return True, None
        except ValueError:
            return False, f"{field_name} must be numeric, got {value}"

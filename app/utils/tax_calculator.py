"""Tax and levy calculation utilities"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Tuple

class TaxCalculator:
    """Calculates taxes and levies according to GRA rules"""
    
    # Tax rates by code
    TAX_RATES = {
        "A": Decimal("0"),      # Exempted
        "B": Decimal("15"),     # Taxable
        "C": Decimal("0"),      # Export
        "D": Decimal("0"),      # Non-Taxable
        "E": Decimal("3"),      # Non-VAT
    }
    
    # Levy rates
    LEVY_A_RATE = Decimal("2.5")   # NHIL
    LEVY_B_RATE = Decimal("2.5")   # GETFund
    LEVY_D_RATE = Decimal("1.0")   # Tourism/CST (1% or 5% depending on service)
    
    @staticmethod
    def round_amount(amount: Decimal) -> Decimal:
        """Round amount to 2 decimal places using standard rounding"""
        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @classmethod
    def calculate_item_taxes(
        cls,
        unit_price: Decimal,
        quantity: Decimal,
        tax_code: str,
        computation_type: str = "EXCLUSIVE",
        item_discount: Decimal = Decimal("0")
    ) -> Dict[str, Decimal]:
        """
        Calculate taxes and levies for an item
        
        Args:
            unit_price: Unit price of the item
            quantity: Quantity of the item
            tax_code: Tax code (A, B, C, D, E)
            computation_type: INCLUSIVE or EXCLUSIVE
            item_discount: Item-level discount amount
        
        Returns dict with:
        - levy_a, levy_b, levy_d
        - vat
        - total
        """
        
        # Handle INCLUSIVE vs EXCLUSIVE computation type
        if computation_type == "INCLUSIVE":
            # For INCLUSIVE, unit_price includes VAT and levies
            # We need to extract the net price
            # This is complex, so for now we treat it as the base
            base_amount = unit_price
        else:
            # For EXCLUSIVE, unit_price is net
            base_amount = unit_price
        
        # Apply item-level discount to base amount
        base_after_discount = base_amount - item_discount
        if base_after_discount < Decimal("0"):
            base_after_discount = Decimal("0")
        
        # Calculate levies on discounted base amount
        levy_a = cls.round_amount(base_after_discount * cls.LEVY_A_RATE / 100)
        levy_b = cls.round_amount(base_after_discount * cls.LEVY_B_RATE / 100)
        levy_d = Decimal("0")  # Default to 0, can be overridden per item
        
        total_levies = levy_a + levy_b + levy_d
        
        # Calculate VAT on (base + levies)
        taxable_base = base_after_discount + total_levies
        tax_rate = cls.TAX_RATES.get(tax_code, Decimal("0"))
        vat = cls.round_amount(taxable_base * tax_rate / 100)
        
        # Calculate total per item
        item_total = cls.round_amount(base_after_discount + total_levies + vat)
        
        return {
            "levy_a": levy_a,
            "levy_b": levy_b,
            "levy_d": levy_d,
            "total_levies": total_levies,
            "vat": vat,
            "item_total": item_total,
        }
    
    @staticmethod
    def verify_totals(
        items: list,
        total_vat: Decimal,
        total_levy: Decimal,
        total_amount: Decimal,
        header_discount: Decimal = Decimal("0")
    ) -> Tuple[bool, str]:
        """
        Verify that totals match item calculations
        
        Args:
            items: List of calculated items
            total_vat: Total VAT from header
            total_levy: Total levy from header
            total_amount: Total amount from header
            header_discount: Header-level discount amount
        
        Returns (is_valid, error_message)
        """
        
        calculated_vat = Decimal("0")
        calculated_levy = Decimal("0")
        calculated_total = Decimal("0")
        
        for item in items:
            calculated_vat += item.get("vat", Decimal("0"))
            calculated_levy += item.get("total_levies", Decimal("0"))
            calculated_total += item.get("item_total", Decimal("0"))
        
        # Apply header-level discount to total
        calculated_total = calculated_total - header_discount
        if calculated_total < Decimal("0"):
            calculated_total = Decimal("0")
        
        # Round for comparison
        calculated_vat = TaxCalculator.round_amount(calculated_vat)
        calculated_levy = TaxCalculator.round_amount(calculated_levy)
        calculated_total = TaxCalculator.round_amount(calculated_total)
        
        # Allow for small rounding differences (±0.01)
        tolerance = Decimal("0.01")
        
        if abs(calculated_vat - total_vat) > tolerance:
            return False, f"VAT mismatch: expected {calculated_vat}, got {total_vat}"
        
        if abs(calculated_levy - total_levy) > tolerance:
            return False, f"Levy mismatch: expected {calculated_levy}, got {total_levy}"
        
        if abs(calculated_total - total_amount) > tolerance:
            return False, f"Total amount mismatch: expected {calculated_total}, got {total_amount}"
        
        return True, ""

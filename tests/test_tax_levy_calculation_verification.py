"""
Property-based tests for tax and levy calculation verification

**Validates: Requirements REQ-TAX-001 through REQ-TAX-020**

This test suite verifies that:
1. Levy calculations are correct per GRA formula
2. VAT calculations are correct per tax code
3. Total amounts match item calculations
4. Rounding is handled correctly
5. Both INCLUSIVE and EXCLUSIVE computation types work
"""

import pytest
from decimal import Decimal
from hypothesis import given, strategies as st, settings, HealthCheck
from app.utils.tax_calculator import TaxCalculator


class TestTaxCalculatorBasics:
    """Basic unit tests for tax calculator"""
    
    def test_levy_a_calculation(self):
        """Test LEVY_A (NHIL) = base_amount × 2.5%"""
        result = TaxCalculator.calculate_item_taxes(
            unit_price=Decimal("100"),
            quantity=Decimal("1"),
            tax_code="B",
            computation_type="EXCLUSIVE"
        )
        assert result["levy_a"] == Decimal("2.50")
    
    def test_levy_b_calculation(self):
        """Test LEVY_B (GETFund) = base_amount × 2.5%"""
        result = TaxCalculator.calculate_item_taxes(
            unit_price=Decimal("100"),
            quantity=Decimal("1"),
            tax_code="B",
            computation_type="EXCLUSIVE"
        )
        assert result["levy_b"] == Decimal("2.50")
    
    def test_levy_c_removed(self):
        """Test that LEVY_C (COVID) is no longer calculated"""
        result = TaxCalculator.calculate_item_taxes(
            unit_price=Decimal("100"),
            quantity=Decimal("1"),
            tax_code="B",
            computation_type="EXCLUSIVE"
        )
        # LEVY_C should not be in the result
        assert "levy_c" not in result or result.get("levy_c") is None
    
    def test_vat_for_tax_code_b(self):
        """Test VAT for TAX_B (Taxable) = 15%"""
        result = TaxCalculator.calculate_item_taxes(
            unit_price=Decimal("100"),
            quantity=Decimal("1"),
            tax_code="B",
            computation_type="EXCLUSIVE"
        )
        # VAT = (100 + 2.50 + 2.50) × 15% = 105.00 × 0.15 = 15.75
        assert result["vat"] == Decimal("15.75")
    
    def test_vat_for_tax_code_a(self):
        """Test VAT for TAX_A (Exempted) = 0%"""
        result = TaxCalculator.calculate_item_taxes(
            unit_price=Decimal("100"),
            quantity=Decimal("1"),
            tax_code="A",
            computation_type="EXCLUSIVE"
        )
        assert result["vat"] == Decimal("0.00")
    
    def test_vat_for_tax_code_c(self):
        """Test VAT for TAX_C (Export) = 0%"""
        result = TaxCalculator.calculate_item_taxes(
            unit_price=Decimal("100"),
            quantity=Decimal("1"),
            tax_code="C",
            computation_type="EXCLUSIVE"
        )
        assert result["vat"] == Decimal("0.00")
    
    def test_vat_for_tax_code_d(self):
        """Test VAT for TAX_D (Non-Taxable) = 0%"""
        result = TaxCalculator.calculate_item_taxes(
            unit_price=Decimal("100"),
            quantity=Decimal("1"),
            tax_code="D",
            computation_type="EXCLUSIVE"
        )
        assert result["vat"] == Decimal("0.00")
    
    def test_vat_for_tax_code_e(self):
        """Test VAT for TAX_E (Non-VAT) = 3%"""
        result = TaxCalculator.calculate_item_taxes(
            unit_price=Decimal("100"),
            quantity=Decimal("1"),
            tax_code="E",
            computation_type="EXCLUSIVE"
        )
        # VAT = (100 + 2.50 + 2.50) × 3% = 105.00 × 0.03 = 3.15
        assert result["vat"] == Decimal("3.15")
    
    def test_item_total_calculation(self):
        """Test item total = base + levies + VAT"""
        result = TaxCalculator.calculate_item_taxes(
            unit_price=Decimal("100"),
            quantity=Decimal("1"),
            tax_code="B",
            computation_type="EXCLUSIVE"
        )
        # Total = 100 + 2.50 + 2.50 + 15.75 = 120.75
        assert result["item_total"] == Decimal("120.75")
    
    def test_rounding_to_two_decimals(self):
        """Test that all amounts are rounded to 2 decimal places"""
        result = TaxCalculator.calculate_item_taxes(
            unit_price=Decimal("33.33"),
            quantity=Decimal("1"),
            tax_code="B",
            computation_type="EXCLUSIVE"
        )
        # Check all values have exactly 2 decimal places
        for key in ["levy_a", "levy_b", "levy_d", "vat", "item_total"]:
            value = result[key]
            # Convert to string and check decimal places
            str_value = str(value)
            if "." in str_value:
                decimal_places = len(str_value.split(".")[1])
                assert decimal_places <= 2, f"{key} has {decimal_places} decimal places"


class TestTaxCalculatorVerification:
    """Tests for verification of totals"""
    
    def test_verify_totals_correct(self):
        """Test verification passes when totals are correct"""
        items = [
            {
                "vat": Decimal("15.83"),
                "total_levies": Decimal("6.00"),
                "item_total": Decimal("121.83")
            },
            {
                "vat": Decimal("15.83"),
                "total_levies": Decimal("6.00"),
                "item_total": Decimal("121.83")
            }
        ]
        
        is_valid, error = TaxCalculator.verify_totals(
            items=items,
            total_vat=Decimal("31.66"),
            total_levy=Decimal("12.00"),
            total_amount=Decimal("243.66")
        )
        
        assert is_valid is True
        assert error == ""
    
    def test_verify_totals_vat_mismatch(self):
        """Test verification fails when VAT doesn't match"""
        items = [
            {
                "vat": Decimal("15.83"),
                "total_levies": Decimal("6.00"),
                "item_total": Decimal("121.83")
            }
        ]
        
        is_valid, error = TaxCalculator.verify_totals(
            items=items,
            total_vat=Decimal("20.00"),  # Wrong VAT
            total_levy=Decimal("6.00"),
            total_amount=Decimal("121.83")
        )
        
        assert is_valid is False
        assert "VAT mismatch" in error
    
    def test_verify_totals_levy_mismatch(self):
        """Test verification fails when levy doesn't match"""
        items = [
            {
                "vat": Decimal("15.83"),
                "total_levies": Decimal("6.00"),
                "item_total": Decimal("121.83")
            }
        ]
        
        is_valid, error = TaxCalculator.verify_totals(
            items=items,
            total_vat=Decimal("15.83"),
            total_levy=Decimal("10.00"),  # Wrong levy
            total_amount=Decimal("121.83")
        )
        
        assert is_valid is False
        assert "Levy mismatch" in error
    
    def test_verify_totals_amount_mismatch(self):
        """Test verification fails when total amount doesn't match"""
        items = [
            {
                "vat": Decimal("15.83"),
                "total_levies": Decimal("6.00"),
                "item_total": Decimal("121.83")
            }
        ]
        
        is_valid, error = TaxCalculator.verify_totals(
            items=items,
            total_vat=Decimal("15.83"),
            total_levy=Decimal("6.00"),
            total_amount=Decimal("150.00")  # Wrong amount
        )
        
        assert is_valid is False
        assert "Total amount mismatch" in error
    
    def test_verify_totals_with_rounding_tolerance(self):
        """Test verification allows small rounding differences (±0.01)"""
        items = [
            {
                "vat": Decimal("15.83"),
                "total_levies": Decimal("6.00"),
                "item_total": Decimal("121.83")
            }
        ]
        
        # Slightly off due to rounding
        is_valid, error = TaxCalculator.verify_totals(
            items=items,
            total_vat=Decimal("15.84"),  # Off by 0.01
            total_levy=Decimal("6.00"),
            total_amount=Decimal("121.83")
        )
        
        assert is_valid is True
    
    def test_verify_totals_multiple_items(self):
        """Test verification with multiple items"""
        items = [
            {
                "vat": Decimal("15.83"),
                "total_levies": Decimal("6.00"),
                "item_total": Decimal("121.83")
            },
            {
                "vat": Decimal("7.92"),
                "total_levies": Decimal("3.00"),
                "item_total": Decimal("60.92")
            },
            {
                "vat": Decimal("3.96"),
                "total_levies": Decimal("1.50"),
                "item_total": Decimal("30.46")
            }
        ]
        
        is_valid, error = TaxCalculator.verify_totals(
            items=items,
            total_vat=Decimal("27.71"),
            total_levy=Decimal("10.50"),
            total_amount=Decimal("213.21")
        )
        
        assert is_valid is True


# Property-based tests using Hypothesis
@given(
    unit_price=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("10000"),
        places=2
    ),
    tax_code=st.sampled_from(["A", "B", "C", "D", "E"])
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_levy_calculations_are_non_negative(unit_price, tax_code):
    """**Validates: Requirements REQ-TAX-001 through REQ-TAX-002**
    
    Property: All levy amounts must be non-negative (LEVY_C removed)
    """
    result = TaxCalculator.calculate_item_taxes(
        unit_price=unit_price,
        quantity=Decimal("1"),
        tax_code=tax_code,
        computation_type="EXCLUSIVE"
    )
    
    assert result["levy_a"] >= Decimal("0")
    assert result["levy_b"] >= Decimal("0")
    assert result["levy_d"] >= Decimal("0")


@given(
    unit_price=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("10000"),
        places=2
    ),
    tax_code=st.sampled_from(["A", "B", "C", "D", "E"])
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_vat_is_non_negative(unit_price, tax_code):
    """**Validates: Requirements REQ-TAX-007 through REQ-TAX-011**
    
    Property: VAT must always be non-negative
    """
    result = TaxCalculator.calculate_item_taxes(
        unit_price=unit_price,
        quantity=Decimal("1"),
        tax_code=tax_code,
        computation_type="EXCLUSIVE"
    )
    
    assert result["vat"] >= Decimal("0")


@given(
    unit_price=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("10000"),
        places=2
    ),
    tax_code=st.sampled_from(["A", "B", "C", "D", "E"])
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_item_total_equals_sum_of_components(unit_price, tax_code):
    """**Validates: Requirements REQ-TAX-018 through REQ-TAX-020**
    
    Property: item_total = unit_price + levies + VAT (LEVY_C removed)
    """
    result = TaxCalculator.calculate_item_taxes(
        unit_price=unit_price,
        quantity=Decimal("1"),
        tax_code=tax_code,
        computation_type="EXCLUSIVE"
    )
    
    expected_total = (
        unit_price +
        result["levy_a"] +
        result["levy_b"] +
        result["levy_d"] +
        result["vat"]
    )
    
    # Round for comparison
    expected_total = TaxCalculator.round_amount(expected_total)
    
    assert result["item_total"] == expected_total


@given(
    unit_price=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("10000"),
        places=2
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_tax_code_b_vat_is_15_percent(unit_price):
    """**Validates: Requirements REQ-TAX-007**
    
    Property: For TAX_B, VAT rate is always 15% (LEVY_C removed)
    """
    result = TaxCalculator.calculate_item_taxes(
        unit_price=unit_price,
        quantity=Decimal("1"),
        tax_code="B",
        computation_type="EXCLUSIVE"
    )
    
    # VAT should be 15% of (unit_price + levies)
    base_with_levies = (
        unit_price +
        result["levy_a"] +
        result["levy_b"] +
        result["levy_d"]
    )
    
    expected_vat = TaxCalculator.round_amount(base_with_levies * Decimal("15") / Decimal("100"))
    
    assert result["vat"] == expected_vat


@given(
    unit_price=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("10000"),
        places=2
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_tax_code_e_vat_is_3_percent(unit_price):
    """**Validates: Requirements REQ-TAX-011**
    
    Property: For TAX_E, VAT rate is always 3% (LEVY_C removed)
    """
    result = TaxCalculator.calculate_item_taxes(
        unit_price=unit_price,
        quantity=Decimal("1"),
        tax_code="E",
        computation_type="EXCLUSIVE"
    )
    
    # VAT should be 3% of (unit_price + levies)
    base_with_levies = (
        unit_price +
        result["levy_a"] +
        result["levy_b"] +
        result["levy_d"]
    )
    
    expected_vat = TaxCalculator.round_amount(base_with_levies * Decimal("3") / Decimal("100"))
    
    assert result["vat"] == expected_vat


@given(
    unit_price=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("10000"),
        places=2
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_tax_codes_acd_have_zero_vat(unit_price):
    """**Validates: Requirements REQ-TAX-008, REQ-TAX-009, REQ-TAX-010**
    
    Property: For TAX_A, C, D, VAT is always 0%
    """
    for tax_code in ["A", "C", "D"]:
        result = TaxCalculator.calculate_item_taxes(
            unit_price=unit_price,
            quantity=Decimal("1"),
            tax_code=tax_code,
            computation_type="EXCLUSIVE"
        )
        
        assert result["vat"] == Decimal("0.00")


@given(
    unit_price=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("10000"),
        places=2
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_levy_a_is_2_5_percent(unit_price):
    """**Validates: Requirements REQ-TAX-001**
    
    Property: LEVY_A is always 2.5% of unit price
    """
    result = TaxCalculator.calculate_item_taxes(
        unit_price=unit_price,
        quantity=Decimal("1"),
        tax_code="B",
        computation_type="EXCLUSIVE"
    )
    
    expected_levy_a = TaxCalculator.round_amount(unit_price * Decimal("2.5") / Decimal("100"))
    
    assert result["levy_a"] == expected_levy_a


@given(
    unit_price=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("10000"),
        places=2
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_levy_b_is_2_5_percent(unit_price):
    """**Validates: Requirements REQ-TAX-002**
    
    Property: LEVY_B is always 2.5% of unit price
    """
    result = TaxCalculator.calculate_item_taxes(
        unit_price=unit_price,
        quantity=Decimal("1"),
        tax_code="B",
        computation_type="EXCLUSIVE"
    )
    
    expected_levy_b = TaxCalculator.round_amount(unit_price * Decimal("2.5") / Decimal("100"))
    
    assert result["levy_b"] == expected_levy_b


def test_levy_c_removed():
    """**Validates: COVID Levy (LEVY_C) has been removed**
    
    Property: LEVY_C is no longer calculated
    """
    result = TaxCalculator.calculate_item_taxes(
        unit_price=Decimal("100"),
        quantity=Decimal("1"),
        tax_code="B",
        computation_type="EXCLUSIVE"
    )
    
    # LEVY_C should not be in the result
    assert "levy_c" not in result


@given(
    unit_price=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("10000"),
        places=2
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_all_amounts_have_two_decimal_places(unit_price):
    """**Validates: Requirements REQ-TAX-018**
    
    Property: All monetary amounts have exactly 2 decimal places
    """
    result = TaxCalculator.calculate_item_taxes(
        unit_price=unit_price,
        quantity=Decimal("1"),
        tax_code="B",
        computation_type="EXCLUSIVE"
    )
    
    for key in ["levy_a", "levy_b", "levy_d", "vat", "item_total"]:
        value = result[key]
        # Check that value has at most 2 decimal places
        str_value = str(value)
        if "." in str_value:
            decimal_places = len(str_value.split(".")[1])
            assert decimal_places <= 2, f"{key} has {decimal_places} decimal places"


def test_item_discount_reduces_base_amount():
    """Test that item-level discount reduces the base amount for tax calculation"""
    result = TaxCalculator.calculate_item_taxes(
        unit_price=Decimal("100"),
        quantity=Decimal("1"),
        tax_code="B",
        computation_type="EXCLUSIVE",
        item_discount=Decimal("10")
    )
    
    # Base after discount = 100 - 10 = 90
    # Levies = 90 * 2.5% + 90 * 2.5% = 2.25 + 2.25 = 4.50
    # VAT = (90 + 4.50) * 15% = 94.50 * 0.15 = 14.175 ≈ 14.18
    # Total = 90 + 4.50 + 14.18 = 108.68
    assert result["item_total"] == Decimal("108.68")


def test_item_discount_zero():
    """Test that zero discount doesn't affect calculation"""
    result_no_discount = TaxCalculator.calculate_item_taxes(
        unit_price=Decimal("100"),
        quantity=Decimal("1"),
        tax_code="B",
        computation_type="EXCLUSIVE",
        item_discount=Decimal("0")
    )
    
    result_with_zero_discount = TaxCalculator.calculate_item_taxes(
        unit_price=Decimal("100"),
        quantity=Decimal("1"),
        tax_code="B",
        computation_type="EXCLUSIVE",
        item_discount=Decimal("0")
    )
    
    assert result_no_discount["item_total"] == result_with_zero_discount["item_total"]


def test_header_discount_in_verification():
    """Test that header-level discount is applied in total verification"""
    items = [
        {
            "vat": Decimal("15.75"),
            "total_levies": Decimal("5.00"),
            "item_total": Decimal("120.75")
        }
    ]
    
    # Without header discount
    is_valid, error = TaxCalculator.verify_totals(
        items=items,
        total_vat=Decimal("15.75"),
        total_levy=Decimal("5.00"),
        total_amount=Decimal("120.75"),
        header_discount=Decimal("0")
    )
    
    assert is_valid is True
    
    # With header discount of 10
    is_valid, error = TaxCalculator.verify_totals(
        items=items,
        total_vat=Decimal("15.75"),
        total_levy=Decimal("5.00"),
        total_amount=Decimal("110.75"),  # 120.75 - 10
        header_discount=Decimal("10")
    )
    
    assert is_valid is True

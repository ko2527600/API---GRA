"""Tests for InvoiceSubmissionSchema"""
import pytest
from pydantic import ValidationError
from app.schemas.invoice import (
    InvoiceSubmissionSchema,
    CompanySchema,
    InvoiceHeaderSchema,
    InvoiceItemSchema
)


class TestCompanySchema:
    """Test CompanySchema validation"""
    
    def test_valid_company_schema(self):
        """Test creating a valid company schema"""
        data = {
            "COMPANY_NAMES": "ABC COMPANY LTD",
            "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
            "COMPANY_TIN": "C00XXXXXXXX"
        }
        schema = CompanySchema(**data)
        assert schema.COMPANY_NAMES == "ABC COMPANY LTD"
        assert schema.COMPANY_SECURITY_KEY == "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
        assert schema.COMPANY_TIN == "C00XXXXXXXX"
    
    def test_valid_company_schema_11_char_tin(self):
        """Test company schema with 11-character TIN"""
        data = {
            "COMPANY_NAMES": "TEST COMPANY",
            "COMPANY_SECURITY_KEY": "SECURITY_KEY_32_CHARS_LONG_HERE",
            "COMPANY_TIN": "P0012345678"
        }
        schema = CompanySchema(**data)
        assert len(schema.COMPANY_TIN) == 11
    
    def test_valid_company_schema_15_char_tin(self):
        """Test company schema with 15-character TIN"""
        data = {
            "COMPANY_NAMES": "TEST COMPANY",
            "COMPANY_SECURITY_KEY": "SECURITY_KEY_32_CHARS_LONG_HERE",
            "COMPANY_TIN": "C00228254051234"
        }
        schema = CompanySchema(**data)
        assert len(schema.COMPANY_TIN) == 15
    
    def test_invalid_company_tin_too_short(self):
        """Test invalid company TIN (too short)"""
        data = {
            "COMPANY_NAMES": "TEST COMPANY",
            "COMPANY_SECURITY_KEY": "SECURITY_KEY_32_CHARS_LONG_HERE",
            "COMPANY_TIN": "C0022825"
        }
        with pytest.raises(ValidationError) as exc_info:
            CompanySchema(**data)
        assert "COMPANY_TIN" in str(exc_info.value)
    
    def test_invalid_company_tin_too_long(self):
        """Test invalid company TIN (too long)"""
        data = {
            "COMPANY_NAMES": "TEST COMPANY",
            "COMPANY_SECURITY_KEY": "SECURITY_KEY_32_CHARS_LONG_HERE",
            "COMPANY_TIN": "C002282540512345678"
        }
        with pytest.raises(ValidationError) as exc_info:
            CompanySchema(**data)
        assert "COMPANY_TIN" in str(exc_info.value)
    
    def test_missing_company_names(self):
        """Test missing COMPANY_NAMES"""
        data = {
            "COMPANY_SECURITY_KEY": "SECURITY_KEY_32_CHARS_LONG_HERE",
            "COMPANY_TIN": "C00XXXXXXXX"
        }
        with pytest.raises(ValidationError) as exc_info:
            CompanySchema(**data)
        assert "COMPANY_NAMES" in str(exc_info.value)
    
    def test_missing_company_security_key(self):
        """Test missing COMPANY_SECURITY_KEY"""
        data = {
            "COMPANY_NAMES": "TEST COMPANY",
            "COMPANY_TIN": "C00XXXXXXXX"
        }
        with pytest.raises(ValidationError) as exc_info:
            CompanySchema(**data)
        assert "COMPANY_SECURITY_KEY" in str(exc_info.value)
    
    def test_missing_company_tin(self):
        """Test missing COMPANY_TIN"""
        data = {
            "COMPANY_NAMES": "TEST COMPANY",
            "COMPANY_SECURITY_KEY": "SECURITY_KEY_32_CHARS_LONG_HERE"
        }
        with pytest.raises(ValidationError) as exc_info:
            CompanySchema(**data)
        assert "COMPANY_TIN" in str(exc_info.value)


class TestInvoiceSubmissionSchema:
    """Test InvoiceSubmissionSchema validation"""
    
    def test_valid_invoice_submission_minimal(self):
        """Test creating a valid invoice submission with minimal fields"""
        data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
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
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
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
            ]
        }
        schema = InvoiceSubmissionSchema(**data)
        assert schema.company.COMPANY_NAMES == "ABC COMPANY LTD"
        assert schema.header.NUM == "INV-2026-001"
        assert len(schema.item_list) == 1
    
    def test_valid_invoice_submission_multiple_items(self):
        """Test invoice submission with multiple items"""
        data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
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
            },
            "item_list": [
                {
                    "ITMREF": "PROD001",
                    "ITMDES": "Product 1",
                    "QUANTITY": "10",
                    "UNITYPRICE": "100",
                    "TAXCODE": "B",
                    "TAXRATE": "15",
                    "LEVY_AMOUNT_A": "2.50",
                    "LEVY_AMOUNT_B": "2.50",
                    "LEVY_AMOUNT_C": "0",
                    "LEVY_AMOUNT_D": "0"
                },
                {
                    "ITMREF": "PROD002",
                    "ITMDES": "Product 2",
                    "QUANTITY": "5",
                    "UNITYPRICE": "200",
                    "TAXCODE": "B",
                    "TAXRATE": "15",
                    "LEVY_AMOUNT_A": "5.00",
                    "LEVY_AMOUNT_B": "5.00",
                    "LEVY_AMOUNT_C": "0",
                    "LEVY_AMOUNT_D": "0"
                }
            ]
        }
        schema = InvoiceSubmissionSchema(**data)
        assert len(schema.item_list) == 2
        assert schema.item_list[0].ITMREF == "PROD001"
        assert schema.item_list[1].ITMREF == "PROD002"
    
    def test_valid_invoice_submission_refund_flag(self):
        """Test invoice submission with REFUND flag"""
        data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
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
            },
            "item_list": [
                {
                    "ITMREF": "PROD001",
                    "ITMDES": "Product Description",
                    "QUANTITY": "5",
                    "UNITYPRICE": "50",
                    "TAXCODE": "B",
                    "TAXRATE": "15",
                    "LEVY_AMOUNT_A": "1.25",
                    "LEVY_AMOUNT_B": "1.25",
                    "LEVY_AMOUNT_C": "0",
                    "LEVY_AMOUNT_D": "0"
                }
            ]
        }
        schema = InvoiceSubmissionSchema(**data)
        assert schema.header.FLAG == "REFUND"
    
    def test_valid_invoice_submission_purchase_flag(self):
        """Test invoice submission with PURCHASE flag"""
        data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
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
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
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
            ]
        }
        schema = InvoiceSubmissionSchema(**data)
        assert schema.header.FLAG == "PURCHASE"
    
    def test_valid_invoice_submission_exclusive_computation(self):
        """Test invoice submission with EXCLUSIVE computation type"""
        data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
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
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
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
            ]
        }
        schema = InvoiceSubmissionSchema(**data)
        assert schema.header.COMPUTATION_TYPE == "EXCLUSIVE"
    
    def test_valid_invoice_submission_with_client_tin(self):
        """Test invoice submission with client TIN"""
        data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
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
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
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
            ]
        }
        schema = InvoiceSubmissionSchema(**data)
        assert schema.header.CLIENT_TIN == "C0022825405"
    
    def test_invalid_item_count_mismatch(self):
        """Test invalid item count mismatch"""
        data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
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
                "ITEMS_COUNTS": "2"  # Says 2 items
            },
            "item_list": [
                {
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
                # Only 1 item provided
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceSubmissionSchema(**data)
        assert "item_list" in str(exc_info.value).lower()
    
    def test_invalid_empty_item_list(self):
        """Test invalid empty item list"""
        data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
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
                "ITEMS_COUNTS": "1"
            },
            "item_list": []
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceSubmissionSchema(**data)
        assert "item_list" in str(exc_info.value).lower()
    
    def test_missing_company(self):
        """Test missing company section"""
        data = {
            "header": {
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
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
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
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceSubmissionSchema(**data)
        assert "company" in str(exc_info.value).lower()
    
    def test_missing_header(self):
        """Test missing header section"""
        data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "item_list": [
                {
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
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceSubmissionSchema(**data)
        assert "header" in str(exc_info.value).lower()
    
    def test_missing_item_list(self):
        """Test missing item_list section"""
        data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
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
                "ITEMS_COUNTS": "1"
            }
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceSubmissionSchema(**data)
        assert "item_list" in str(exc_info.value).lower()
    
    def test_invalid_company_data(self):
        """Test invalid company data"""
        data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "INVALID"  # Invalid TIN
            },
            "header": {
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
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
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
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceSubmissionSchema(**data)
        assert "company" in str(exc_info.value).lower() or "tin" in str(exc_info.value).lower()
    
    def test_invalid_header_data(self):
        """Test invalid header data"""
        data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
                "COMPUTATION_TYPE": "INVALID",  # Invalid computation type
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
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
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
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceSubmissionSchema(**data)
        assert "header" in str(exc_info.value).lower() or "computation" in str(exc_info.value).lower()
    
    def test_invalid_item_data(self):
        """Test invalid item data"""
        data = {
            "company": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            },
            "header": {
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
                "ITEMS_COUNTS": "1"
            },
            "item_list": [
                {
                    "ITMREF": "PROD001",
                    "ITMDES": "Product Description",
                    "QUANTITY": "-10",  # Invalid negative quantity
                    "UNITYPRICE": "100",
                    "TAXCODE": "B",
                    "TAXRATE": "15",
                    "LEVY_AMOUNT_A": "2.50",
                    "LEVY_AMOUNT_B": "2.50",
                    "LEVY_AMOUNT_C": "0",
                    "LEVY_AMOUNT_D": "0"
                }
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            InvoiceSubmissionSchema(**data)
        assert "item_list" in str(exc_info.value).lower() or "quantity" in str(exc_info.value).lower()

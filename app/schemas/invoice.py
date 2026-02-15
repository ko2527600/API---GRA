"""Schemas for Invoice submission and responses"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class InvoiceHeaderSchema(BaseModel):
    """Invoice header schema for client info, dates, and totals"""
    
    # Computation and submission type
    COMPUTATION_TYPE: str = Field(
        ..., 
        description="Computation type: INCLUSIVE or EXCLUSIVE",
        pattern="^(INCLUSIVE|EXCLUSIVE)$"
    )
    FLAG: str = Field(
        ..., 
        description="Submission flag type: INVOICE, REFUND, PROFORMA, PARTIAL_REFUND, PURCHASE",
        pattern="^(INVOICE|REFUND|PROFORMA|PARTIAL_REFUND|PURCHASE)$"
    )
    SALE_TYPE: str = Field(
        ..., 
        description="Sale type: NORMAL or CREDIT_SALE",
        pattern="^(NORMAL|CREDIT_SALE)$"
    )
    
    # User and invoice identification
    USER_NAME: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="User name submitting the invoice"
    )
    NUM: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Invoice number (unique per business)"
    )
    
    # Dates
    INVOICE_DATE: str = Field(
        ..., 
        description="Invoice date in YYYY-MM-DD format",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    
    # Currency
    CURRENCY: str = Field(
        default="GHS",
        description="Currency code (must be GHS)",
        pattern="^GHS$"
    )
    EXCHANGE_RATE: str = Field(
        default="1",
        description="Exchange rate (must be 1 for GHS)",
        pattern="^1$"
    )
    
    # Client information
    CLIENT_NAME: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Client/customer name"
    )
    CLIENT_TIN: Optional[str] = Field(
        None,
        description="Client TIN (11 or 15 characters)"
    )
    
    # Totals
    TOTAL_VAT: str = Field(
        ..., 
        description="Total VAT amount",
        pattern=r"^\d+(\.\d{1,2})?$"
    )
    TOTAL_LEVY: str = Field(
        ..., 
        description="Total levy amount",
        pattern=r"^\d+(\.\d{1,2})?$"
    )
    TOTAL_AMOUNT: str = Field(
        ..., 
        description="Total invoice amount",
        pattern=r"^\d+(\.\d{1,2})?$"
    )
    
    # Item count
    ITEMS_COUNTS: str = Field(
        ..., 
        description="Number of items in the invoice",
        pattern=r"^\d+$"
    )
    
    @field_validator("COMPUTATION_TYPE")
    @classmethod
    def validate_computation_type(cls, v):
        """Validate computation type"""
        if v not in ["INCLUSIVE", "EXCLUSIVE"]:
            raise ValueError("COMPUTATION_TYPE must be INCLUSIVE or EXCLUSIVE")
        return v
    
    @field_validator("FLAG")
    @classmethod
    def validate_flag(cls, v):
        """Validate flag"""
        if v not in ["INVOICE", "REFUND", "PROFORMA", "PARTIAL_REFUND", "PURCHASE"]:
            raise ValueError("FLAG must be one of: INVOICE, REFUND, PROFORMA, PARTIAL_REFUND, PURCHASE")
        return v
    
    @field_validator("SALE_TYPE")
    @classmethod
    def validate_sale_type(cls, v):
        """Validate sale type"""
        if v not in ["NORMAL", "CREDIT_SALE"]:
            raise ValueError("SALE_TYPE must be NORMAL or CREDIT_SALE")
        return v
    
    @field_validator("CURRENCY")
    @classmethod
    def validate_currency(cls, v):
        """Validate currency is GHS"""
        if v != "GHS":
            raise ValueError("CURRENCY must be GHS")
        return v
    
    @field_validator("EXCHANGE_RATE")
    @classmethod
    def validate_exchange_rate(cls, v):
        """Validate exchange rate is 1 for GHS"""
        if v != "1":
            raise ValueError("EXCHANGE_RATE must be 1 for GHS currency")
        return v
    
    @field_validator("TOTAL_VAT", "TOTAL_LEVY", "TOTAL_AMOUNT")
    @classmethod
    def validate_numeric_strings(cls, v):
        """Validate numeric string fields"""
        try:
            float_val = float(v)
            if float_val < 0:
                raise ValueError("Value must be non-negative")
        except ValueError:
            raise ValueError("Must be a valid numeric value")
        return v
    
    @field_validator("ITEMS_COUNTS")
    @classmethod
    def validate_items_count(cls, v):
        """Validate items count is positive integer"""
        try:
            count = int(v)
            if count <= 0:
                raise ValueError("ITEMS_COUNTS must be greater than 0")
        except ValueError:
            raise ValueError("ITEMS_COUNTS must be a valid positive integer")
        return v
    
    @field_validator("CLIENT_TIN")
    @classmethod
    def validate_client_tin(cls, v):
        """Validate client TIN format"""
        if v is not None:
            if len(v) not in [11, 15]:
                raise ValueError("CLIENT_TIN must be 11 or 15 characters")
        return v
    
    class Config:
        """Pydantic config"""
        json_schema_extra = {
            "example": {
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
        }


class InvoiceItemSchema(BaseModel):
    """Invoice item schema for item details, taxes, and levies"""
    
    # Item identification
    ITMREF: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Item reference code"
    )
    ITMDES: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Item description"
    )
    
    # Quantity and pricing
    QUANTITY: str = Field(
        ..., 
        description="Item quantity",
        pattern=r"^\d+(\.\d{1,2})?$"
    )
    UNITYPRICE: str = Field(
        ..., 
        description="Unit price of the item",
        pattern=r"^\d+(\.\d{1,2})?$"
    )
    
    # Tax information
    TAXCODE: str = Field(
        ..., 
        description="Tax code (A, B, C, D, E)",
        pattern="^[A-E]$"
    )
    TAXRATE: str = Field(
        ..., 
        description="Tax rate (0, 15, or 3)",
        pattern="^(0|15|3)$"
    )
    
    # Levy amounts
    LEVY_AMOUNT_A: str = Field(
        ..., 
        description="Levy A amount (NHIL - 2.5%)",
        pattern=r"^\d+(\.\d{1,2})?$"
    )
    LEVY_AMOUNT_B: str = Field(
        ..., 
        description="Levy B amount (GETFund - 2.5%)",
        pattern=r"^\d+(\.\d{1,2})?$"
    )
    LEVY_AMOUNT_C: str = Field(
        ..., 
        description="Levy C amount (COVID - 1%)",
        pattern=r"^\d+(\.\d{1,2})?$"
    )
    LEVY_AMOUNT_D: str = Field(
        ..., 
        description="Levy D amount (Tourism/CST - 1-5%)",
        pattern=r"^\d+(\.\d{1,2})?$"
    )
    
    # Optional fields
    ITMDISCOUNT: Optional[str] = Field(
        default="0",
        description="Item-specific discount amount",
        pattern=r"^\d+(\.\d{1,2})?$"
    )
    ITEM_CATEGORY: Optional[str] = Field(
        None,
        max_length=255,
        description="Item category"
    )
    BATCH: Optional[str] = Field(
        None,
        max_length=255,
        description="Batch number"
    )
    EXPIRE: Optional[str] = Field(
        None,
        description="Expiry date (YYYY-MM-DD format)",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )
    
    @field_validator("QUANTITY", "UNITYPRICE")
    @classmethod
    def validate_positive_numeric(cls, v):
        """Validate quantity and unit price are positive"""
        try:
            float_val = float(v)
            if float_val <= 0:
                raise ValueError("Value must be positive")
        except ValueError:
            raise ValueError("Must be a valid positive numeric value")
        return v
    
    @field_validator("LEVY_AMOUNT_A", "LEVY_AMOUNT_B", "LEVY_AMOUNT_C", "LEVY_AMOUNT_D", "ITMDISCOUNT")
    @classmethod
    def validate_non_negative_numeric(cls, v):
        """Validate levy amounts and discount are non-negative"""
        try:
            float_val = float(v)
            if float_val < 0:
                raise ValueError("Value must be non-negative")
        except ValueError:
            raise ValueError("Must be a valid non-negative numeric value")
        return v
    
    @field_validator("TAXCODE")
    @classmethod
    def validate_tax_code(cls, v):
        """Validate tax code is valid"""
        if v not in ["A", "B", "C", "D", "E"]:
            raise ValueError("TAXCODE must be one of: A, B, C, D, E")
        return v
    
    @field_validator("TAXRATE")
    @classmethod
    def validate_tax_rate(cls, v):
        """Validate tax rate is valid"""
        if v not in ["0", "15", "3"]:
            raise ValueError("TAXRATE must be one of: 0, 15, 3")
        return v
    
    class Config:
        """Pydantic config"""
        json_schema_extra = {
            "example": {
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
                "ITMDISCOUNT": "0",
                "ITEM_CATEGORY": "GOODS"
            }
        }


class InvoiceItemResponseSchema(BaseModel):
    """Response schema for invoice item"""
    
    itmref: str = Field(..., description="Item reference code")
    itmdes: str = Field(..., description="Item description")
    quantity: float = Field(..., description="Item quantity")
    unityprice: float = Field(..., description="Unit price")
    taxcode: str = Field(..., description="Tax code")
    taxrate: float = Field(..., description="Tax rate")
    levy_amount_a: float = Field(..., description="Levy A amount")
    levy_amount_b: float = Field(..., description="Levy B amount")
    levy_amount_c: float = Field(..., description="Levy C amount")
    levy_amount_d: float = Field(..., description="Levy D amount")
    itmdiscount: float = Field(..., description="Item discount")
    item_total: float = Field(..., description="Item total amount")
    item_category: Optional[str] = Field(None, description="Item category")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        """Pydantic config"""
        from_attributes = True


class InvoiceHeaderResponseSchema(BaseModel):
    """Response schema for invoice header"""
    
    invoice_num: str = Field(..., description="Invoice number")
    client_name: str = Field(..., description="Client name")
    client_tin: Optional[str] = Field(None, description="Client TIN")
    invoice_date: str = Field(..., description="Invoice date (YYYY-MM-DD)")
    computation_type: str = Field(..., description="Computation type")
    total_vat: float = Field(..., description="Total VAT")
    total_levy: float = Field(..., description="Total levy")
    total_amount: float = Field(..., description="Total amount")
    items_count: int = Field(..., description="Number of items")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        """Pydantic config"""
        from_attributes = True


class CompanySchema(BaseModel):
    """Company authentication schema for GRA submission"""
    
    COMPANY_NAMES: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Company legal name as registered with GRA"
    )
    COMPANY_SECURITY_KEY: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Company security key provided by GRA"
    )
    COMPANY_TIN: str = Field(
        ...,
        description="Company TIN (11 or 15 characters)"
    )
    
    @field_validator("COMPANY_TIN")
    @classmethod
    def validate_company_tin(cls, v):
        """Validate company TIN format"""
        if len(v) not in [11, 15]:
            raise ValueError("COMPANY_TIN must be 11 or 15 characters")
        return v
    
    class Config:
        """Pydantic config"""
        json_schema_extra = {
            "example": {
                "COMPANY_NAMES": "ABC COMPANY LTD",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
                "COMPANY_TIN": "C00XXXXXXXX"
            }
        }


class InvoiceSubmissionSchema(BaseModel):
    """Complete invoice submission schema combining company, header, and items"""
    
    company: CompanySchema = Field(
        ...,
        description="Company authentication details"
    )
    header: InvoiceHeaderSchema = Field(
        ...,
        description="Invoice header with client info and totals"
    )
    item_list: List[InvoiceItemSchema] = Field(
        ...,
        min_items=1,
        description="List of invoice items"
    )
    
    @field_validator("item_list")
    @classmethod
    def validate_item_count_matches(cls, v, info):
        """Validate that item_list count matches ITEMS_COUNTS in header"""
        if "header" in info.data:
            header = info.data["header"]
            expected_count = int(header.ITEMS_COUNTS)
            if len(v) != expected_count:
                raise ValueError(
                    f"item_list length ({len(v)}) must match ITEMS_COUNTS ({expected_count})"
                )
        return v
    
    class Config:
        """Pydantic config"""
        json_schema_extra = {
            "example": {
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
                    "ITEMS_COUNTS": "2"
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
                        "LEVY_AMOUNT_D": "0",
                        "ITMDISCOUNT": "0",
                        "ITEM_CATEGORY": "GOODS"
                    },
                    {
                        "ITMREF": "PROD002",
                        "ITMDES": "Another Product",
                        "QUANTITY": "5",
                        "UNITYPRICE": "200",
                        "TAXCODE": "B",
                        "TAXRATE": "15",
                        "LEVY_AMOUNT_A": "5.00",
                        "LEVY_AMOUNT_B": "5.00",
                        "LEVY_AMOUNT_C": "0",
                        "LEVY_AMOUNT_D": "0",
                        "ITMDISCOUNT": "0",
                        "ITEM_CATEGORY": "GOODS"
                    }
                ]
            }
        }


class ValidationErrorSchema(BaseModel):
    """Schema for validation error details"""
    
    field: str = Field(..., description="Field name that failed validation")
    error: str = Field(..., description="Error code and message")
    expected: Optional[str] = Field(None, description="Expected value")
    actual: Optional[str] = Field(None, description="Actual value")
    
    class Config:
        """Pydantic config"""
        from_attributes = True


class InvoiceResponseSchema(BaseModel):
    """Response schema for successful invoice submission (200 OK)"""
    
    submission_id: str = Field(
        ...,
        description="Unique submission ID for tracking"
    )
    invoice_num: str = Field(
        ...,
        description="Invoice number from the submission"
    )
    status: str = Field(
        ...,
        description="Submission status: RECEIVED, PROCESSING, PENDING_GRA, SUCCESS, FAILED",
        pattern="^(RECEIVED|PROCESSING|PENDING_GRA|SUCCESS|FAILED)$"
    )
    gra_response_code: Optional[str] = Field(
        None,
        description="GRA response code (null if successful)"
    )
    gra_response_message: Optional[str] = Field(
        None,
        description="GRA response message (null if successful)"
    )
    gra_invoice_id: Optional[str] = Field(
        None,
        description="GRA-issued invoice ID upon success"
    )
    gra_qr_code: Optional[str] = Field(
        None,
        description="GRA QR code URL for printing"
    )
    gra_receipt_num: Optional[str] = Field(
        None,
        description="GRA receipt number upon success"
    )
    ysdcid: Optional[str] = Field(
        None,
        description="VSDC ID from GRA stamping"
    )
    ysdcrecnum: Optional[str] = Field(
        None,
        description="VSDC receipt number from GRA stamping"
    )
    ysdcintdata: Optional[str] = Field(
        None,
        description="VSDC internal data from GRA stamping"
    )
    ysdcnrc: Optional[str] = Field(
        None,
        description="VSDC NRC from GRA stamping"
    )
    submitted_at: datetime = Field(
        ...,
        description="Timestamp when submission was received"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when GRA processing completed"
    )
    processing_time_ms: Optional[int] = Field(
        None,
        description="Processing time in milliseconds"
    )
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        """Validate status is one of allowed values"""
        if v not in ["RECEIVED", "PROCESSING", "PENDING_GRA", "SUCCESS", "FAILED"]:
            raise ValueError("status must be one of: RECEIVED, PROCESSING, PENDING_GRA, SUCCESS, FAILED")
        return v
    
    class Config:
        """Pydantic config"""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "submission_id": "550e8400-e29b-41d4-a716-446655440000",
                "invoice_num": "INV-2026-001",
                "status": "SUCCESS",
                "gra_response_code": None,
                "gra_response_message": None,
                "gra_invoice_id": "GRA-INV-2026-001",
                "gra_qr_code": "https://gra.gov.gh/qr/abc123def456",
                "gra_receipt_num": "VSDC-REC-12345",
                "ysdcid": "VSDC-ID-001",
                "ysdcrecnum": "VSDC-REC-12345",
                "ysdcintdata": "internal-data-string",
                "ysdcnrc": "NRC-12345",
                "submitted_at": "2026-02-10T10:00:00Z",
                "completed_at": "2026-02-10T10:05:00Z",
                "processing_time_ms": 5000
            }
        }


class InvoiceAcceptedResponseSchema(BaseModel):
    """Response schema for invoice submission acceptance (202 Accepted)"""
    
    submission_id: str = Field(
        ...,
        description="Unique submission ID for tracking"
    )
    status: str = Field(
        default="RECEIVED",
        description="Submission status (always RECEIVED for 202 response)"
    )
    message: str = Field(
        default="Invoice received and queued for GRA processing",
        description="Status message"
    )
    validation_passed: bool = Field(
        default=True,
        description="Whether initial validation passed"
    )
    invoice_num: str = Field(
        ...,
        description="Invoice number from the submission"
    )
    next_action: str = Field(
        default="Check status using submission_id",
        description="Guidance on next action"
    )
    
    class Config:
        """Pydantic config"""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "submission_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "RECEIVED",
                "message": "Invoice received and queued for GRA processing",
                "validation_passed": True,
                "invoice_num": "INV-2026-001",
                "next_action": "Check status using submission_id"
            }
        }


class InvoiceErrorResponseSchema(BaseModel):
    """Response schema for invoice submission errors (400, 401, 500)"""
    
    error_code: str = Field(
        ...,
        description="Error code: VALIDATION_FAILED, AUTH_FAILED, SERVER_ERROR, etc"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    submission_id: Optional[str] = Field(
        None,
        description="Submission ID if available"
    )
    gra_response_code: Optional[str] = Field(
        None,
        description="GRA error code if from GRA"
    )
    gra_response_message: Optional[str] = Field(
        None,
        description="GRA error message if from GRA"
    )
    validation_errors: Optional[List[ValidationErrorSchema]] = Field(
        None,
        description="List of validation errors with field details"
    )
    timestamp: datetime = Field(
        ...,
        description="Timestamp of error"
    )
    
    class Config:
        """Pydantic config"""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "error_code": "VALIDATION_FAILED",
                "message": "Validation failed: TOTAL_AMOUNT mismatch",
                "submission_id": "550e8400-e29b-41d4-a716-446655440000",
                "gra_response_code": "B16",
                "gra_response_message": "INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
                "validation_errors": [
                    {
                        "field": "TOTAL_AMOUNT",
                        "error": "B16 - INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
                        "expected": "3438",
                        "actual": "3400"
                    }
                ],
                "timestamp": "2026-02-10T10:00:00Z"
            }
        }


class InvoiceSignatureResponseSchema(BaseModel):
    """Response schema for invoice signature/stamping details"""
    
    submission_id: str = Field(
        ...,
        description="Unique submission ID"
    )
    invoice_num: str = Field(
        ...,
        description="Invoice number"
    )
    status: str = Field(
        ...,
        description="Submission status",
        pattern="^(RECEIVED|PROCESSING|PENDING_GRA|SUCCESS|FAILED)$"
    )
    ysdcid: Optional[str] = Field(
        None,
        description="VSDC ID - unique identifier of the VSDC that processed the transaction"
    )
    ysdcrecnum: Optional[str] = Field(
        None,
        description="VSDC receipt number - receipt number from the VSDC"
    )
    ysdcintdata: Optional[str] = Field(
        None,
        description="VSDC internal data - integrated data from the VSDC"
    )
    ysdcnrc: Optional[str] = Field(
        None,
        description="VSDC NRC - VSDC serial number"
    )
    gra_qr_code: Optional[str] = Field(
        None,
        description="GRA QR code URL for printing on invoice"
    )
    gra_invoice_id: Optional[str] = Field(
        None,
        description="GRA-issued invoice ID"
    )
    gra_receipt_num: Optional[str] = Field(
        None,
        description="GRA receipt number"
    )
    gra_response_code: Optional[str] = Field(
        None,
        description="GRA response code (null if successful)"
    )
    gra_response_message: Optional[str] = Field(
        None,
        description="GRA response message (null if successful)"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when GRA processing completed"
    )
    
    class Config:
        """Pydantic config"""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "submission_id": "550e8400-e29b-41d4-a716-446655440000",
                "invoice_num": "INV-2026-001",
                "status": "SUCCESS",
                "ysdcid": "VSDC-ID-001",
                "ysdcrecnum": "VSDC-REC-12345",
                "ysdcintdata": "internal-data-string",
                "ysdcnrc": "NRC-12345",
                "gra_qr_code": "https://gra.gov.gh/qr/abc123def456",
                "gra_invoice_id": "GRA-INV-2026-001",
                "gra_receipt_num": "VSDC-REC-12345",
                "gra_response_code": None,
                "gra_response_message": None,
                "completed_at": "2026-02-10T10:05:00Z"
            }
        }

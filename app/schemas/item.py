"""Schemas for Item registration, inventory, TIN validation, and tag descriptions"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class ItemRegistrationSchema(BaseModel):
    """Schema for item registration with GRA"""
    
    ITEM_REF: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Unique item reference code"
    )
    ITEM_DESCRIPTION: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Item description"
    )
    ITEM_CATEGORY: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Item category (GOODS, SERVICES, etc)"
    )
    UNIT_OF_MEASURE: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unit of measure (PIECES, KG, LITERS, etc)"
    )
    TAX_CODE: str = Field(
        ...,
        description="Tax code (A, B, C, D, E)",
        pattern="^[A-E]$"
    )
    TAX_RATE: str = Field(
        ...,
        description="Tax rate (0, 15, or 3)",
        pattern="^(0|15|3)$"
    )
    STANDARD_PRICE: str = Field(
        ...,
        description="Standard price for the item",
        pattern=r"^\d+(\.\d{1,2})?$"
    )
    COMPANY_TIN: str = Field(
        ...,
        description="Company TIN (11 or 15 characters)"
    )
    COMPANY_SECURITY_KEY: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Company security key for GRA"
    )
    
    @field_validator("TAX_CODE")
    @classmethod
    def validate_tax_code(cls, v):
        """Validate tax code"""
        if v not in ["A", "B", "C", "D", "E"]:
            raise ValueError("TAX_CODE must be one of: A, B, C, D, E")
        return v
    
    @field_validator("TAX_RATE")
    @classmethod
    def validate_tax_rate(cls, v):
        """Validate tax rate"""
        if v not in ["0", "15", "3"]:
            raise ValueError("TAX_RATE must be one of: 0, 15, 3")
        return v
    
    @field_validator("STANDARD_PRICE")
    @classmethod
    def validate_price(cls, v):
        """Validate price is positive"""
        try:
            price = float(v)
            if price <= 0:
                raise ValueError("Price must be positive")
        except ValueError:
            raise ValueError("STANDARD_PRICE must be a valid positive numeric value")
        return v
    
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
                "ITEM_REF": "PROD001",
                "ITEM_DESCRIPTION": "Office Chair",
                "ITEM_CATEGORY": "GOODS",
                "UNIT_OF_MEASURE": "PIECES",
                "TAX_CODE": "B",
                "TAX_RATE": "15",
                "STANDARD_PRICE": "250.00",
                "COMPANY_TIN": "C00XXXXXXXX",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
            }
        }


class ItemRegistrationResponseSchema(BaseModel):
    """Response schema for item registration"""
    
    submission_id: str = Field(
        ...,
        description="Unique submission ID for tracking"
    )
    item_ref: str = Field(
        ...,
        description="Item reference from submission"
    )
    status: str = Field(
        ...,
        description="Registration status: RECEIVED, PROCESSING, SUCCESS, FAILED",
        pattern="^(RECEIVED|PROCESSING|SUCCESS|FAILED)$"
    )
    gra_item_id: Optional[str] = Field(
        None,
        description="GRA-issued item ID upon success"
    )
    gra_response_code: Optional[str] = Field(
        None,
        description="GRA response code"
    )
    gra_response_message: Optional[str] = Field(
        None,
        description="GRA response message"
    )
    submitted_at: datetime = Field(
        ...,
        description="Timestamp when submission was received"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when GRA processing completed"
    )
    
    class Config:
        """Pydantic config"""
        from_attributes = True


class InventoryUpdateSchema(BaseModel):
    """Schema for inventory quantity updates"""
    
    ITEM_REF: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Item reference code"
    )
    QUANTITY_CHANGE: str = Field(
        ...,
        description="Quantity change (positive for increase, negative for decrease)",
        pattern=r"^-?\d+(\.\d{1,2})?$"
    )
    OPERATION_TYPE: str = Field(
        ...,
        description="Operation type: IN, OUT, ADJUSTMENT, RETURN",
        pattern="^(IN|OUT|ADJUSTMENT|RETURN)$"
    )
    REFERENCE_NUM: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Reference number (invoice, PO, etc)"
    )
    NOTES: Optional[str] = Field(
        None,
        max_length=500,
        description="Additional notes about the update"
    )
    COMPANY_TIN: str = Field(
        ...,
        description="Company TIN"
    )
    
    @field_validator("OPERATION_TYPE")
    @classmethod
    def validate_operation_type(cls, v):
        """Validate operation type"""
        if v not in ["IN", "OUT", "ADJUSTMENT", "RETURN"]:
            raise ValueError("OPERATION_TYPE must be one of: IN, OUT, ADJUSTMENT, RETURN")
        return v
    
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
                "ITEM_REF": "PROD001",
                "QUANTITY_CHANGE": "50",
                "OPERATION_TYPE": "IN",
                "REFERENCE_NUM": "PO-2026-001",
                "NOTES": "Stock received from supplier",
                "COMPANY_TIN": "C00XXXXXXXX"
            }
        }


class InventoryUpdateResponseSchema(BaseModel):
    """Response schema for inventory update"""
    
    submission_id: str = Field(
        ...,
        description="Unique submission ID for tracking"
    )
    item_ref: str = Field(
        ...,
        description="Item reference"
    )
    status: str = Field(
        ...,
        description="Update status: SUCCESS, FAILED",
        pattern="^(SUCCESS|FAILED)$"
    )
    previous_quantity: Optional[str] = Field(
        None,
        description="Previous quantity before update"
    )
    new_quantity: Optional[str] = Field(
        None,
        description="New quantity after update"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if update failed"
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp of update"
    )
    
    class Config:
        """Pydantic config"""
        from_attributes = True


class TINValidationSchema(BaseModel):
    """Schema for TIN validation"""
    
    TIN: str = Field(
        ...,
        description="TIN to validate (11 or 15 characters)"
    )
    TIN_TYPE: str = Field(
        ...,
        description="TIN type: COMPANY or INDIVIDUAL",
        pattern="^(COMPANY|INDIVIDUAL)$"
    )
    
    @field_validator("TIN")
    @classmethod
    def validate_tin(cls, v):
        """Validate TIN format"""
        if len(v) not in [11, 15]:
            raise ValueError("TIN must be 11 or 15 characters")
        return v
    
    @field_validator("TIN_TYPE")
    @classmethod
    def validate_tin_type(cls, v):
        """Validate TIN type"""
        if v not in ["COMPANY", "INDIVIDUAL"]:
            raise ValueError("TIN_TYPE must be COMPANY or INDIVIDUAL")
        return v
    
    class Config:
        """Pydantic config"""
        json_schema_extra = {
            "example": {
                "TIN": "C0022825405",
                "TIN_TYPE": "COMPANY"
            }
        }


class TINValidationResponseSchema(BaseModel):
    """Response schema for TIN validation"""
    
    tin: str = Field(
        ...,
        description="TIN that was validated"
    )
    is_valid: bool = Field(
        ...,
        description="Whether TIN is valid"
    )
    tin_type: str = Field(
        ...,
        description="TIN type: COMPANY or INDIVIDUAL"
    )
    entity_name: Optional[str] = Field(
        None,
        description="Entity name if valid"
    )
    registration_status: Optional[str] = Field(
        None,
        description="Registration status if valid"
    )
    gra_response_code: Optional[str] = Field(
        None,
        description="GRA response code"
    )
    gra_response_message: Optional[str] = Field(
        None,
        description="GRA response message"
    )
    cached: bool = Field(
        default=False,
        description="Whether result was from cache"
    )
    cache_expires_at: Optional[datetime] = Field(
        None,
        description="When cache expires"
    )
    validated_at: datetime = Field(
        ...,
        description="Timestamp of validation"
    )
    
    class Config:
        """Pydantic config"""
        from_attributes = True


class TagDescriptionSchema(BaseModel):
    """Schema for tag description registration"""
    
    TAG_CODE: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Tag code"
    )
    TAG_DESCRIPTION: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Tag description"
    )
    TAG_CATEGORY: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Tag category"
    )
    COMPANY_TIN: str = Field(
        ...,
        description="Company TIN"
    )
    COMPANY_SECURITY_KEY: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Company security key"
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
                "TAG_CODE": "TAG001",
                "TAG_DESCRIPTION": "Premium Product",
                "TAG_CATEGORY": "PRODUCT_TYPE",
                "COMPANY_TIN": "C00XXXXXXXX",
                "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
            }
        }


class TagDescriptionResponseSchema(BaseModel):
    """Response schema for tag description registration"""
    
    submission_id: str = Field(
        ...,
        description="Unique submission ID for tracking"
    )
    tag_code: str = Field(
        ...,
        description="Tag code from submission"
    )
    status: str = Field(
        ...,
        description="Registration status: RECEIVED, PROCESSING, SUCCESS, FAILED",
        pattern="^(RECEIVED|PROCESSING|SUCCESS|FAILED)$"
    )
    gra_tag_id: Optional[str] = Field(
        None,
        description="GRA-issued tag ID upon success"
    )
    gra_response_code: Optional[str] = Field(
        None,
        description="GRA response code"
    )
    gra_response_message: Optional[str] = Field(
        None,
        description="GRA response message"
    )
    submitted_at: datetime = Field(
        ...,
        description="Timestamp when submission was received"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when GRA processing completed"
    )
    
    class Config:
        """Pydantic config"""
        from_attributes = True


class ItemErrorResponseSchema(BaseModel):
    """Response schema for item operation errors"""
    
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
    timestamp: datetime = Field(
        ...,
        description="Timestamp of error"
    )
    
    class Config:
        """Pydantic config"""
        from_attributes = True

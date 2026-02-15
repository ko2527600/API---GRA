"""Z-Report request and response schemas"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class ZReportRequestSchema(BaseModel):
    """Z-Report request schema"""
    zd_date: str = Field(..., description="Date for Z-Report (YYYY-MM-DD format)")
    
    @validator('zd_date')
    def validate_date_format(cls, v):
        """Validate date format is YYYY-MM-DD"""
        if not v or len(v) != 10:
            raise ValueError("Date must be in YYYY-MM-DD format")
        parts = v.split('-')
        if len(parts) != 3:
            raise ValueError("Date must be in YYYY-MM-DD format")
        try:
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            if not (1 <= month <= 12 and 1 <= day <= 31):
                raise ValueError("Invalid month or day")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format with valid numbers")
        return v


class ZReportDataSchema(BaseModel):
    """Z-Report data schema"""
    inv_close: Optional[int] = Field(None, description="Closed invoices count")
    inv_count: Optional[int] = Field(None, description="Total invoice count")
    inv_open: Optional[int] = Field(None, description="Open invoices count")
    inv_vat: Optional[float] = Field(None, description="Total VAT amount")
    inv_total: Optional[float] = Field(None, description="Grand total amount")
    inv_levy: Optional[float] = Field(None, description="Total levies amount")


class ZReportResponseSchema(BaseModel):
    """Z-Report response schema"""
    submission_id: str = Field(..., description="Unique submission ID")
    report_date: str = Field(..., description="Report date (YYYY-MM-DD)")
    status: str = Field(..., description="Submission status")
    data: Optional[ZReportDataSchema] = Field(None, description="Z-Report data")
    gra_response_code: Optional[str] = Field(None, description="GRA response code")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(..., description="Response timestamp")
    
    class Config:
        from_attributes = True


class ZReportRetrievalSchema(BaseModel):
    """Z-Report retrieval response schema"""
    report_date: str = Field(..., description="Report date (YYYY-MM-DD)")
    inv_close: Optional[int] = Field(None, description="Closed invoices count")
    inv_count: Optional[int] = Field(None, description="Total invoice count")
    inv_open: Optional[int] = Field(None, description="Open invoices count")
    inv_vat: Optional[float] = Field(None, description="Total VAT amount")
    inv_total: Optional[float] = Field(None, description="Grand total amount")
    inv_levy: Optional[float] = Field(None, description="Total levies amount")
    gra_response_code: Optional[str] = Field(None, description="GRA response code")
    created_at: datetime = Field(..., description="Record creation timestamp")
    
    class Config:
        from_attributes = True


class ZReportErrorResponseSchema(BaseModel):
    """Z-Report error response schema"""
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    submission_id: Optional[str] = Field(None, description="Submission ID if available")
    gra_response_code: Optional[str] = Field(None, description="GRA response code if available")
    timestamp: datetime = Field(..., description="Error timestamp")

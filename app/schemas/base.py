"""Base schemas for common response structures"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ErrorDetail(BaseModel):
    """Error detail for validation errors"""
    field: str
    error: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None

class ErrorResponse(BaseModel):
    """Standard error response format"""
    error_code: str
    message: str
    submission_id: Optional[str] = None
    gra_response_code: Optional[str] = None
    gra_response_message: Optional[str] = None
    validation_errors: Optional[List[ErrorDetail]] = None
    timestamp: datetime

class SuccessResponse(BaseModel):
    """Standard success response format"""
    submission_id: str
    status: str
    message: str
    timestamp: datetime

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    environment: str

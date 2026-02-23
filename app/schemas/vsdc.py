"""VSDC health check schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VSDCHealthCheckRequestSchema(BaseModel):
    """VSDC health check request schema"""
    pass


class VSDCHealthCheckResponseSchema(BaseModel):
    """VSDC health check response schema"""
    status: str
    sdc_id: Optional[str] = None
    gra_response_code: Optional[str] = None
    checked_at: datetime
    expires_at: datetime
    message: str


class VSDCStatusRetrievalSchema(BaseModel):
    """VSDC status retrieval schema"""
    status: str
    sdc_id: Optional[str] = None
    last_checked_at: datetime
    uptime_percentage: float
    is_cached: bool

"""Schemas for API Key management"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class APIKeyGenerateRequest(BaseModel):
    """Request to generate new API credentials"""
    business_name: str = Field(..., min_length=1, max_length=255, description="Business name", example="ABC Company Ltd")
    gra_tin: str = Field(..., min_length=11, max_length=15, description="GRA TIN (11 or 15 characters)", example="C00XXXXXXXX")
    gra_company_name: str = Field(..., min_length=1, max_length=255, description="GRA company name", example="ABC COMPANY LTD")
    gra_security_key: str = Field(..., min_length=1, description="GRA security key", example="UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH")


class APIKeyResponse(BaseModel):
    """Response containing generated API credentials"""
    api_key: str = Field(..., description="API Key for authentication")
    api_secret: str = Field(..., description="API Secret for HMAC signature (store securely)")
    business_id: str = Field(..., description="Business ID")
    business_name: str = Field(..., description="Business name")
    created_at: datetime = Field(..., description="Timestamp when credentials were created")
    
    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """Response containing list of API keys for a business"""
    business_id: str = Field(..., description="Business ID")
    business_name: str = Field(..., description="Business name")
    api_key: str = Field(..., description="API Key")
    status: str = Field(..., description="Status (active, inactive)")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_used_at: Optional[datetime] = Field(None, description="Last used timestamp")
    
    class Config:
        from_attributes = True


class APIKeyRevokeRequest(BaseModel):
    """Request to revoke an API key"""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for revocation")


class APIKeyRevokeResponse(BaseModel):
    """Response for API key revocation"""
    api_key: str = Field(..., description="Revoked API key")
    status: str = Field(..., description="New status (should be 'inactive')")
    revoked_at: datetime = Field(..., description="Revocation timestamp")
    
    class Config:
        from_attributes = True

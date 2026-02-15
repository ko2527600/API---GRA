"""API Key management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.schemas.api_key import (
    APIKeyGenerateRequest,
    APIKeyResponse,
    APIKeyListResponse,
    APIKeyRevokeRequest,
    APIKeyRevokeResponse
)
from app.services.business_service import BusinessService
from app.logger import logger

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("/generate", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def generate_api_key(
    request: APIKeyGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate new API credentials for a business.
    
    The API secret is only returned once. Store it securely.
    """
    try:
        business, api_secret = BusinessService.create_business(
            db=db,
            business_name=request.business_name,
            gra_tin=request.gra_tin,
            gra_company_name=request.gra_company_name,
            gra_security_key=request.gra_security_key
        )
        
        return APIKeyResponse(
            api_key=business.api_key,
            api_secret=api_secret,
            business_id=str(business.id),
            business_name=business.name,
            created_at=business.created_at
        )
        
    except IntegrityError as e:
        logger.error(f"Business creation failed - duplicate entry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Business with this TIN already exists"
        )
    except Exception as e:
        logger.error(f"Error generating API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate API credentials"
        )


@router.get("/{business_id}", response_model=APIKeyListResponse)
async def get_api_key(
    business_id: str,
    db: Session = Depends(get_db)
):
    """
    Get API key information for a business.
    
    Note: API secret is not returned for security reasons.
    """
    try:
        from uuid import UUID
        business = BusinessService.get_business_by_id(db, UUID(business_id))
        
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        
        return APIKeyListResponse(
            business_id=str(business.id),
            business_name=business.name,
            api_key=business.api_key,
            status=business.status,
            created_at=business.created_at,
            last_used_at=None  # TODO: Track last used timestamp
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business ID format"
        )
    except Exception as e:
        logger.error(f"Error retrieving API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API key"
        )


@router.post("/{business_id}/revoke", response_model=APIKeyRevokeResponse)
async def revoke_api_key(
    business_id: str,
    request: APIKeyRevokeRequest,
    db: Session = Depends(get_db)
):
    """
    Revoke API credentials for a business.
    """
    try:
        from uuid import UUID
        business = BusinessService.deactivate_business(db, UUID(business_id))
        
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        
        return APIKeyRevokeResponse(
            api_key=business.api_key,
            status=business.status,
            revoked_at=business.updated_at
        )
        
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business not found"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business ID format"
        )
    except Exception as e:
        logger.error(f"Error revoking API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )

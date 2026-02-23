"""VSDC health check endpoints for checking GRA VSDC operational status"""
import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db
from app.models.models import VSDCHealthCheck, Business
from app.middleware.auth_dependency import verify_api_key
from app.logger import logger
from app.services.gra_client import get_gra_client


# Define schemas inline to avoid import issues
class VSDCHealthCheckRequestSchema(BaseModel):
    """VSDC health check request schema"""
    pass


class VSDCHealthCheckResponseSchema(BaseModel):
    """VSDC health check response schema"""
    status: str = Field(..., description="VSDC status: UP, DOWN, DEGRADED")
    sdc_id: Optional[str] = Field(None, description="SDC ID from GRA")
    gra_response_code: Optional[str] = Field(None, description="GRA response code if error")
    checked_at: datetime = Field(..., description="Timestamp of health check")
    expires_at: datetime = Field(..., description="Cache expiration time")
    message: str = Field(..., description="Status message")


class VSDCStatusRetrievalSchema(BaseModel):
    """VSDC status retrieval schema"""
    status: str = Field(..., description="Last known VSDC status")
    sdc_id: Optional[str] = Field(None, description="SDC ID from last check")
    last_checked_at: datetime = Field(..., description="Timestamp of last check")
    uptime_percentage: float = Field(..., description="Uptime percentage")
    is_cached: bool = Field(..., description="Whether status is from cache")


router = APIRouter(prefix="/vsdc", tags=["vsdc"])


@router.post("/health-check", response_model=VSDCHealthCheckResponseSchema, status_code=200)
async def check_vsdc_health(
    request_data: VSDCHealthCheckRequestSchema,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Check GRA VSDC operational status
    
    - Submits health check request to GRA
    - Returns VSDC status: UP, DOWN, DEGRADED
    - Caches result for 5 minutes
    - Handles GRA unavailability gracefully
    
    **REQ-HEALTH-001**: Accept health check requests in JSON or XML format
    **REQ-HEALTH-002**: Submit health check to GRA VSDC
    **REQ-HEALTH-003**: Return VSDC status (UP, DOWN, DEGRADED)
    """
    try:
        submission_id = str(uuid.uuid4())
        
        # Get business from API key
        business_obj = db.query(Business).filter(Business.api_key == api_key).first()
        if not business_obj:
            logger.error(f"Invalid API key: {api_key}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Check for cached health check (not expired)
        cached_check = db.query(VSDCHealthCheck).filter(
            VSDCHealthCheck.business_id == business_obj.id,
            VSDCHealthCheck.expires_at > datetime.utcnow()
        ).order_by(VSDCHealthCheck.checked_at.desc()).first()
        
        if cached_check:
            logger.info(
                f"VSDC health check retrieved from cache",
                extra={
                    "business_id": str(business_obj.id),
                    "status": cached_check.status
                }
            )
            
            return VSDCHealthCheckResponseSchema(
                status=cached_check.status,
                sdc_id=cached_check.sdc_id,
                gra_response_code=cached_check.gra_response_code,
                checked_at=cached_check.checked_at,
                expires_at=cached_check.expires_at,
                message=f"VSDC is {cached_check.status.lower()} (cached)"
            )
        
        # No cached result, submit new health check to GRA
        gra_client = get_gra_client()
        
        # Prepare health check request
        health_check_request = {
            "company": {
                "COMPANY_NAMES": business_obj.gra_company_name,
                "COMPANY_SECURITY_KEY": business_obj.gra_security_key,
                "COMPANY_TIN": business_obj.gra_tin
            }
        }
        
        try:
            # Submit health check to GRA
            gra_response = await gra_client.submit_json("/api/v1/vsdc/health-check", health_check_request)
            
            # Parse GRA response
            status_value = "UP"
            sdc_id = None
            gra_response_code = None
            
            if isinstance(gra_response, dict):
                # Check for error in response
                if "error_code" in gra_response or "error" in gra_response:
                    error_code = gra_response.get("error_code") or gra_response.get("error")
                    gra_response_code = error_code
                    
                    # Map error codes to status
                    if error_code in ["D06", "A13", "IS100"]:
                        status_value = "DOWN"
                    else:
                        status_value = "DEGRADED"
                else:
                    # Successful response
                    status_value = "UP"
                    sdc_id = gra_response.get("sdc_id") or gra_response.get("SDC_ID")
            
            # Cache the result for 5 minutes
            expires_at = datetime.utcnow() + timedelta(minutes=5)
            vsdc_check = VSDCHealthCheck(
                business_id=business_obj.id,
                status=status_value,
                sdc_id=sdc_id,
                gra_response_code=gra_response_code,
                expires_at=expires_at
            )
            db.add(vsdc_check)
            db.commit()
            
            logger.info(
                f"VSDC health check completed",
                extra={
                    "business_id": str(business_obj.id),
                    "status": status_value,
                    "sdc_id": sdc_id
                }
            )
            
            return VSDCHealthCheckResponseSchema(
                status=status_value,
                sdc_id=sdc_id,
                gra_response_code=gra_response_code,
                checked_at=vsdc_check.checked_at,
                expires_at=expires_at,
                message=f"VSDC is {status_value.lower()}"
            )
        
        except Exception as gra_error:
            # Handle GRA unavailability gracefully
            logger.warning(
                f"GRA health check failed: {str(gra_error)}",
                extra={
                    "business_id": str(business_obj.id),
                    "error": str(gra_error)
                }
            )
            
            # Cache DOWN status for 5 minutes
            expires_at = datetime.utcnow() + timedelta(minutes=5)
            vsdc_check = VSDCHealthCheck(
                business_id=business_obj.id,
                status="DOWN",
                sdc_id=None,
                gra_response_code="D06",  # Stamping engine is down
                expires_at=expires_at
            )
            db.add(vsdc_check)
            db.commit()
            
            return VSDCHealthCheckResponseSchema(
                status="DOWN",
                sdc_id=None,
                gra_response_code="D06",
                checked_at=vsdc_check.checked_at,
                expires_at=expires_at,
                message="VSDC is unavailable"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking VSDC health: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while checking VSDC health"
        )


@router.get("/status", response_model=VSDCStatusRetrievalSchema, status_code=200)
async def get_vsdc_status(
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve cached VSDC health status
    
    - Returns last check status and uptime metrics
    - Returns cached status if available
    - Handles no cached status with appropriate response
    
    **REQ-HEALTH-004**: Return cached VSDC health status
    **REQ-HEALTH-005**: Return last check status and uptime metrics
    **REQ-HEALTH-006**: Provide endpoint to retrieve cached health status
    """
    try:
        # Get business from API key
        business_obj = db.query(Business).filter(Business.api_key == api_key).first()
        if not business_obj:
            logger.error(f"Invalid API key: {api_key}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Get latest health check
        latest_check = db.query(VSDCHealthCheck).filter(
            VSDCHealthCheck.business_id == business_obj.id
        ).order_by(VSDCHealthCheck.checked_at.desc()).first()
        
        if not latest_check:
            logger.warning(
                f"No VSDC health check found",
                extra={"business_id": str(business_obj.id)}
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No VSDC health check data available. Please run a health check first."
            )
        
        # Calculate uptime percentage (simplified: 100% if UP, 0% if DOWN)
        uptime_percentage = 100.0 if latest_check.status == "UP" else 0.0
        if latest_check.status == "DEGRADED":
            uptime_percentage = 50.0
        
        # Check if status is still cached (not expired)
        is_cached = latest_check.expires_at > datetime.utcnow()
        
        logger.info(
            f"VSDC status retrieved",
            extra={
                "business_id": str(business_obj.id),
                "status": latest_check.status,
                "is_cached": is_cached
            }
        )
        
        return VSDCStatusRetrievalSchema(
            status=latest_check.status,
            sdc_id=latest_check.sdc_id,
            last_checked_at=latest_check.checked_at,
            uptime_percentage=uptime_percentage,
            is_cached=is_cached
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving VSDC status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving VSDC status"
        )

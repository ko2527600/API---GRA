"""Z-Report endpoints for requesting and retrieving daily summary reports"""
import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.schemas.z_report import (
    ZReportRequestSchema,
    ZReportResponseSchema,
    ZReportRetrievalSchema,
    ZReportErrorResponseSchema,
    ZReportDataSchema
)
from app.models.models import ZReport, Business, Submission
from app.middleware.auth_dependency import verify_api_key
from app.logger import logger


router = APIRouter(prefix="/reports", tags=["z-reports"])


@router.post("/z-report", response_model=ZReportResponseSchema, status_code=202)
async def request_z_report(
    request_data: ZReportRequestSchema,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Request a Z-Report from GRA for a specific date
    
    - Validates date format (YYYY-MM-DD)
    - Creates submission record
    - Queues for GRA processing
    - Returns submission ID for tracking
    
    **REQ-ZREP-001**: Accept Z-Report requests in JSON format
    **REQ-ZREP-002**: Validate ZD_DATE format (YYYY-MM-DD)
    **REQ-ZREP-003**: Submit Z-Report request to GRA
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
        
        # Validate date format
        try:
            parts = request_data.zd_date.split('-')
            if len(parts) != 3:
                raise ValueError("Invalid date format")
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            if not (1 <= month <= 12 and 1 <= day <= 31):
                raise ValueError("Invalid month or day")
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid date format: {request_data.zd_date}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # Create submission record
        submission = Submission(
            id=submission_id,
            business_id=business_obj.id,
            submission_type="Z_REPORT",
            submission_status="RECEIVED",
            raw_request={
                "zd_date": request_data.zd_date,
                "company_tin": business_obj.gra_tin
            }
        )
        db.add(submission)
        
        # Create or update Z-Report record
        z_report = db.query(ZReport).filter(
            ZReport.business_id == business_obj.id,
            ZReport.report_date == request_data.zd_date
        ).first()
        
        if not z_report:
            z_report = ZReport(
                business_id=business_obj.id,
                report_date=request_data.zd_date
            )
            db.add(z_report)
        
        db.commit()
        
        logger.info(
            f"Z-Report request received",
            extra={
                "submission_id": submission_id,
                "business_id": str(business_obj.id),
                "report_date": request_data.zd_date
            }
        )
        
        return ZReportResponseSchema(
            submission_id=submission_id,
            report_date=request_data.zd_date,
            status="RECEIVED",
            data=None,
            gra_response_code=None,
            message="Z-Report request received and queued for GRA processing",
            timestamp=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting Z-Report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the Z-Report request"
        )


@router.get("/z-report/{date}", response_model=ZReportRetrievalSchema, status_code=200)
async def get_z_report(
    date: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve Z-Report data for a specific date
    
    - Validates date format (YYYY-MM-DD)
    - Retrieves Z-Report from database
    - Returns aggregated sales data
    
    **REQ-ZREP-004**: Return aggregated data: inv_close, inv_count, inv_open, inv_vat, inv_total, inv_levy
    **REQ-ZREP-005**: Store Z-Report in database for historical tracking
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
        
        # Validate date format
        try:
            parts = date.split('-')
            if len(parts) != 3:
                raise ValueError("Invalid date format")
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            if not (1 <= month <= 12 and 1 <= day <= 31):
                raise ValueError("Invalid month or day")
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid date format: {date}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
        
        # Retrieve Z-Report
        z_report = db.query(ZReport).filter(
            ZReport.business_id == business_obj.id,
            ZReport.report_date == date
        ).first()
        
        if not z_report:
            logger.warning(
                f"Z-Report not found",
                extra={
                    "business_id": str(business_obj.id),
                    "report_date": date
                }
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Z-Report not found for date {date}"
            )
        
        logger.info(
            f"Z-Report retrieved",
            extra={
                "business_id": str(business_obj.id),
                "report_date": date
            }
        )
        
        return ZReportRetrievalSchema(
            report_date=z_report.report_date,
            inv_close=z_report.inv_close,
            inv_count=z_report.inv_count,
            inv_open=z_report.inv_open,
            inv_vat=z_report.inv_vat,
            inv_total=z_report.inv_total,
            inv_levy=z_report.inv_levy,
            gra_response_code=z_report.gra_response_code,
            created_at=z_report.created_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving Z-Report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the Z-Report"
        )

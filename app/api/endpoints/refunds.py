"""Refund submission and tracking endpoints"""
import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.schemas.refund import (
    RefundSubmissionSchema,
    RefundResponseSchema,
    RefundAcceptedResponseSchema
)
from app.models.models import Submission, Refund, RefundItem
from app.middleware.auth_dependency import verify_api_key
from app.logger import logger


router = APIRouter(prefix="/refunds", tags=["refunds"])


@router.post("/submit", response_model=RefundAcceptedResponseSchema, status_code=202)
async def submit_refund(
    submission_data: RefundSubmissionSchema,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Submit a refund for GRA processing
    
    - Accepts JSON refund submission
    - Validates all fields
    - Stores submission in database
    - Returns submission ID for tracking
    """
    try:
        submission_id = str(uuid.uuid4())
        
        # Create submission record
        submission = Submission(
            id=submission_id,
            submission_type="REFUND",
            status="RECEIVED",
            company_tin=submission_data.company.COMPANY_TIN,
            submitted_at=datetime.utcnow(),
            raw_data=submission_data.model_dump_json()
        )
        
        # Create refund record
        refund = Refund(
            id=str(uuid.uuid4()),
            submission_id=submission_id,
            refund_num=submission_data.header.NUM,
            original_invoice_num=submission_data.header.ORIGINAL_INVOICE_NUM,
            refund_date=submission_data.header.REFUND_DATE,
            client_name=submission_data.header.CLIENT_NAME,
            client_tin=submission_data.header.CLIENT_TIN,
            total_amount=submission_data.header.TOTAL_AMOUNT,
            total_vat=submission_data.header.TOTAL_VAT,
            total_levy=submission_data.header.TOTAL_LEVY,
            refund_reason=submission_data.header.REFUND_REASON,
            status="RECEIVED"
        )
        
        # Create refund items
        refund_items = []
        for item_data in submission_data.item_list:
            item = RefundItem(
                id=str(uuid.uuid4()),
                refund_id=refund.id,
                item_ref=item_data.ITMREF,
                item_description=item_data.ITMDES,
                quantity=item_data.QUANTITY,
                unit_price=item_data.UNITYPRICE,
                tax_code=item_data.TAXCODE,
                tax_rate=item_data.TAXRATE,
                levy_a=item_data.LEVY_AMOUNT_A,
                levy_b=item_data.LEVY_AMOUNT_B,
                levy_c=item_data.LEVY_AMOUNT_C,
                levy_d=item_data.LEVY_AMOUNT_D
            )
            refund_items.append(item)
        
        # Save to database
        db.add(submission)
        db.add(refund)
        db.add_all(refund_items)
        db.commit()
        
        logger.info(f"Refund submission received: {submission_id}")
        
        return RefundAcceptedResponseSchema(
            submission_id=submission_id,
            refund_num=submission_data.header.NUM
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting refund: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process refund submission"
        )


@router.get("/{submission_id}/status", response_model=RefundResponseSchema)
async def get_refund_status(
    submission_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get current status of a refund submission
    
    - Returns submission status
    - Shows GRA response if available
    - Includes processing time
    """
    try:
        submission = db.query(Submission).filter(
            Submission.id == submission_id,
            Submission.submission_type == "REFUND"
        ).first()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund submission not found"
            )
        
        refund = db.query(Refund).filter(
            Refund.submission_id == submission_id
        ).first()
        
        if not refund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund not found"
            )
        
        # Calculate processing time
        processing_time_ms = None
        if submission.completed_at:
            delta = submission.completed_at - submission.submitted_at
            processing_time_ms = int(delta.total_seconds() * 1000)
        
        logger.info(f"Refund status retrieved: {submission_id}")
        
        return RefundResponseSchema(
            submission_id=submission_id,
            refund_num=refund.refund_num,
            original_invoice_num=refund.original_invoice_num,
            status=submission.status,
            gra_response_code=submission.gra_response_code,
            gra_response_message=submission.gra_response_message,
            gra_refund_id=submission.gra_refund_id,
            gra_qr_code=submission.gra_qr_code,
            gra_receipt_num=submission.gra_receipt_num,
            submitted_at=submission.submitted_at,
            completed_at=submission.completed_at,
            processing_time_ms=processing_time_ms
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving refund status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve refund status"
        )


@router.get("/{submission_id}/details", response_model=dict)
async def get_refund_details(
    submission_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get full refund details with all items and GRA response
    
    - Returns complete refund information
    - Includes all line items
    - Shows GRA response and signature
    """
    try:
        submission = db.query(Submission).filter(
            Submission.id == submission_id,
            Submission.submission_type == "REFUND"
        ).first()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund submission not found"
            )
        
        refund = db.query(Refund).filter(
            Refund.submission_id == submission_id
        ).first()
        
        if not refund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refund not found"
            )
        
        # Get refund items
        items = db.query(RefundItem).filter(
            RefundItem.refund_id == refund.id
        ).all()
        
        # Build response
        refund_details = {
            "submission_id": submission_id,
            "refund_num": refund.refund_num,
            "original_invoice_num": refund.original_invoice_num,
            "refund_date": refund.refund_date,
            "client_name": refund.client_name,
            "client_tin": refund.client_tin,
            "total_amount": refund.total_amount,
            "total_vat": refund.total_vat,
            "total_levy": refund.total_levy,
            "refund_reason": refund.refund_reason,
            "status": submission.status,
            "items": [
                {
                    "item_ref": item.item_ref,
                    "item_description": item.item_description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "tax_code": item.tax_code,
                    "tax_rate": item.tax_rate,
                    "levy_a": item.levy_a,
                    "levy_b": item.levy_b,
                    "levy_c": item.levy_c,
                    "levy_d": item.levy_d
                }
                for item in items
            ],
            "gra_response": {
                "gra_refund_id": submission.gra_refund_id,
                "gra_qr_code": submission.gra_qr_code,
                "gra_receipt_num": submission.gra_receipt_num,
                "gra_response_code": submission.gra_response_code,
                "gra_response_message": submission.gra_response_message
            },
            "submitted_at": submission.submitted_at,
            "completed_at": submission.completed_at
        }
        
        logger.info(f"Refund details retrieved: {submission_id}")
        
        return refund_details
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving refund details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve refund details"
        )

"""Purchase submission and tracking endpoints"""
import uuid
import asyncio
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.schemas.purchase import (
    PurchaseSubmissionSchema,
    PurchaseResponseSchema,
    PurchaseAcceptedResponseSchema,
    PurchaseCancellationRequestSchema,
    PurchaseCancellationResponseSchema
)
from app.models.models import Submission, Purchase, PurchaseItem
from app.middleware.auth_dependency import verify_api_key
from app.logger import logger


router = APIRouter(prefix="/purchases", tags=["purchases"])


@router.post("/submit", response_model=PurchaseAcceptedResponseSchema, status_code=202)
async def submit_purchase(
    submission_data: PurchaseSubmissionSchema,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Submit a purchase for GRA processing
    
    - Accepts JSON purchase submission
    - Validates all fields
    - Stores submission in database
    - Returns submission ID for tracking
    """
    try:
        # Get business from API key
        from app.models.models import Business
        business = db.query(Business).filter(Business.api_key == api_key).first()
        
        if not business:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        submission_id = uuid.uuid4()
        
        # Create submission record
        submission = Submission(
            id=submission_id,
            business_id=business.id,
            submission_type="PURCHASE",
            submission_status="RECEIVED",
            submitted_at=datetime.utcnow(),
            raw_request=submission_data.model_dump()
        )
        
        # Create purchase record
        purchase = Purchase(
            id=uuid.uuid4(),
            submission_id=submission_id,
            business_id=business.id,
            purchase_num=submission_data.header.NUM,
            supplier_name=submission_data.header.SUPPLIER_NAME,
            supplier_tin=submission_data.header.SUPPLIER_TIN,
            purchase_date=submission_data.header.PURCHASE_DATE,
            total_amount=float(submission_data.header.TOTAL_AMOUNT),
            total_vat=float(submission_data.header.TOTAL_VAT),
            total_levy=float(submission_data.header.TOTAL_LEVY),
            items_count=len(submission_data.item_list)
        )
        
        # Create purchase items
        purchase_items = []
        for item_data in submission_data.item_list:
            # Calculate item total
            quantity = float(item_data.QUANTITY)
            unit_price = float(item_data.UNITYPRICE)
            item_total = quantity * unit_price
            
            item = PurchaseItem(
                id=uuid.uuid4(),
                purchase_id=purchase.id,
                itmref=item_data.ITMREF,
                itmdes=item_data.ITMDES,
                quantity=quantity,
                unityprice=unit_price,
                taxcode=item_data.TAXCODE,
                taxrate=float(item_data.TAXRATE),
                item_total=item_total
            )
            purchase_items.append(item)
        
        # Save to database
        db.add(submission)
        db.add(purchase)
        db.add_all(purchase_items)
        db.commit()
        
        logger.info(f"Purchase submission received: {submission_id}")
        
        # Queue for GRA processing (async)
        try:
            from app.services.submission_processor import SubmissionProcessor
            # Process asynchronously without blocking the response
            asyncio.create_task(
                SubmissionProcessor.process_json_submission(
                    db=db,
                    submission_id=submission_id,
                    business_id=business.id,
                    request_data=submission_data.model_dump()
                )
            )
        except Exception as e:
            logger.warning(f"Failed to queue GRA processing: {str(e)}")
        
        return PurchaseAcceptedResponseSchema(
            submission_id=str(submission_id),
            purchase_num=submission_data.header.NUM,
            message="Purchase received and queued for GRA processing"
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting purchase: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process purchase submission"
        )


@router.get("/{submission_id}/status", response_model=PurchaseResponseSchema)
async def get_purchase_status(
    submission_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get current status of a purchase submission
    
    - Returns submission status
    - Shows GRA response if available
    - Includes processing time
    """
    try:
        # Convert submission_id to UUID
        try:
            submission_uuid = uuid.UUID(submission_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid submission ID format"
            )
        
        submission = db.query(Submission).filter(
            Submission.id == submission_uuid,
            Submission.submission_type == "PURCHASE"
        ).first()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase submission not found"
            )
        
        purchase = db.query(Purchase).filter(
            Purchase.submission_id == submission_uuid
        ).first()
        
        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase not found"
            )
        
        # Calculate processing time
        processing_time_ms = None
        if submission.completed_at:
            delta = submission.completed_at - submission.submitted_at
            processing_time_ms = int(delta.total_seconds() * 1000)
        
        logger.info(f"Purchase status retrieved: {submission_id}")
        
        return PurchaseResponseSchema(
            submission_id=submission_id,
            purchase_num=purchase.purchase_num,
            status=submission.submission_status,
            gra_response_code=submission.gra_response_code,
            gra_response_message=submission.gra_response_message,
            gra_purchase_id=submission.gra_invoice_id,
            gra_qr_code=submission.gra_qr_code,
            gra_receipt_num=submission.gra_receipt_num,
            submitted_at=submission.submitted_at,
            completed_at=submission.completed_at,
            processing_time_ms=processing_time_ms
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving purchase status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve purchase status"
        )


@router.get("/{submission_id}/details", response_model=dict)
async def get_purchase_details(
    submission_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get full purchase details with all items and GRA response
    
    - Returns complete purchase information
    - Includes all line items
    - Shows GRA response and signature
    """
    try:
        # Convert submission_id to UUID
        try:
            submission_uuid = uuid.UUID(submission_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid submission ID format"
            )
        
        submission = db.query(Submission).filter(
            Submission.id == submission_uuid,
            Submission.submission_type == "PURCHASE"
        ).first()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase submission not found"
            )
        
        purchase = db.query(Purchase).filter(
            Purchase.submission_id == submission_uuid
        ).first()
        
        if not purchase:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Purchase not found"
            )
        
        # Get purchase items
        items = db.query(PurchaseItem).filter(
            PurchaseItem.purchase_id == purchase.id
        ).all()
        
        # Build response
        purchase_details = {
            "submission_id": submission_id,
            "purchase_num": purchase.purchase_num,
            "supplier_name": purchase.supplier_name,
            "supplier_tin": purchase.supplier_tin,
            "purchase_date": purchase.purchase_date,
            "total_amount": purchase.total_amount,
            "total_vat": purchase.total_vat,
            "total_levy": purchase.total_levy,
            "status": submission.submission_status,
            "items": [
                {
                    "itmref": item.itmref,
                    "itmdes": item.itmdes,
                    "quantity": item.quantity,
                    "unityprice": item.unityprice,
                    "taxcode": item.taxcode,
                    "taxrate": item.taxrate,
                    "item_total": item.item_total
                }
                for item in items
            ],
            "gra_response": {
                "gra_invoice_id": submission.gra_invoice_id,
                "gra_qr_code": submission.gra_qr_code,
                "gra_receipt_num": submission.gra_receipt_num,
                "gra_response_code": submission.gra_response_code,
                "gra_response_message": submission.gra_response_message
            },
            "submitted_at": submission.submitted_at,
            "completed_at": submission.completed_at
        }
        
        logger.info(f"Purchase details retrieved: {submission_id}")
        
        return purchase_details
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving purchase details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve purchase details"
        )


@router.post("/cancel", response_model=PurchaseCancellationResponseSchema, status_code=202)
async def cancel_purchase(
    cancellation_data: PurchaseCancellationRequestSchema,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Cancel a previously submitted purchase
    
    - Accepts purchase cancellation request with FLAG=CANCEL
    - Validates purchase exists and belongs to business
    - Stores cancellation submission in database
    - Returns submission ID for tracking
    """
    try:
        # Get business from API key
        from app.models.models import Business
        business = db.query(Business).filter(Business.api_key == api_key).first()
        
        if not business:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        submission_id = uuid.uuid4()
        
        # Create cancellation submission record with all required fields
        submission = Submission(
            id=submission_id,
            business_id=business.id,
            submission_type="PURCHASE_CANCELLATION",
            submission_status="RECEIVED",
            submitted_at=datetime.utcnow(),
            raw_request=cancellation_data.model_dump()
        )
        
        # Save to database
        db.add(submission)
        db.commit()
        
        logger.info(f"Purchase cancellation received: {submission_id} for purchase {cancellation_data.header.NUM}")
        
        return PurchaseCancellationResponseSchema(
            submission_id=str(submission_id),
            purchase_num=cancellation_data.header.NUM,
            status="RECEIVED",
            message="Purchase cancellation received and queued for GRA processing",
            submitted_at=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling purchase: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process purchase cancellation"
        )

"""Invoice submission and tracking endpoints"""
import uuid
import asyncio
from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import xml.etree.ElementTree as ET

from app.database import get_db
from app.schemas.invoice import (
    InvoiceSubmissionSchema,
    InvoiceResponseSchema,
    InvoiceAcceptedResponseSchema,
    InvoiceErrorResponseSchema,
    InvoiceSignatureResponseSchema
)
from app.models.models import Submission, Invoice, InvoiceItem
from app.middleware.auth_dependency import verify_api_key
from app.services.submission_processor import SubmissionProcessor
from app.logger import logger


router = APIRouter(prefix="/invoices", tags=["invoices"])


def parse_xml_to_dict(xml_string: str) -> dict:
    """Parse XML string to dictionary"""
    try:
        root = ET.fromstring(xml_string)
        
        def xml_to_dict(element):
            result = {}
            for child in element:
                if len(child) == 0:
                    result[child.tag] = child.text
                else:
                    if child.tag not in result:
                        result[child.tag] = []
                    result[child.tag].append(xml_to_dict(child))
            return result
        
        return xml_to_dict(root)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {str(e)}")


def _process_submission_async(
    submission_id: str,
    business_id: str,
    request_data: dict,
    db_session: Session
):
    """
    Process submission asynchronously in background
    
    Args:
        submission_id: Submission ID
        business_id: Business ID
        request_data: Request data to submit
        db_session: Database session
    """
    try:
        # Run async submission processor
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            SubmissionProcessor.process_json_submission(
                db_session,
                submission_id,
                business_id,
                request_data
            )
        )
    except Exception as e:
        logger.error(f"Background submission processing failed: {str(e)}")
    finally:
        db_session.close()


@router.post("/submit", response_model=InvoiceAcceptedResponseSchema, status_code=202)
async def submit_invoice(
    submission_data: InvoiceSubmissionSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Submit an invoice for GRA processing
    
    - Accepts JSON invoice submission
    - Validates all fields
    - Stores submission in database
    - Queues for GRA submission
    - Returns submission ID for tracking
    """
    try:
        submission_id = str(uuid.uuid4())
        
        # Get business from API key
        from app.services.business_service import BusinessService
        business = BusinessService.get_business_by_api_key(db, api_key)
        if not business:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Create submission record
        submission = Submission(
            id=submission_id,
            business_id=business.id,
            submission_type="INVOICE",
            submission_status="RECEIVED",
            submitted_at=datetime.utcnow(),
            raw_request=submission_data.model_dump_json()
        )
        
        # Create invoice record
        invoice = Invoice(
            id=str(uuid.uuid4()),
            submission_id=submission_id,
            invoice_num=submission_data.header.NUM,
            invoice_date=submission_data.header.INVOICE_DATE,
            client_name=submission_data.header.CLIENT_NAME,
            client_tin=submission_data.header.CLIENT_TIN,
            total_amount=submission_data.header.TOTAL_AMOUNT,
            total_vat=submission_data.header.TOTAL_VAT,
            total_levy=submission_data.header.TOTAL_LEVY,
            computation_type=submission_data.header.COMPUTATION_TYPE,
            items_count=len(submission_data.item_list)
        )
        
        # Create invoice items
        invoice_items = []
        for item_data in submission_data.item_list:
            item = InvoiceItem(
                id=str(uuid.uuid4()),
                invoice_id=invoice.id,
                itmref=item_data.ITMREF,
                itmdes=item_data.ITMDES,
                quantity=item_data.QUANTITY,
                unityprice=item_data.UNITYPRICE,
                taxcode=item_data.TAXCODE,
                taxrate=item_data.TAXRATE,
                levy_amount_a=item_data.LEVY_AMOUNT_A,
                levy_amount_b=item_data.LEVY_AMOUNT_B,
                levy_amount_c=item_data.LEVY_AMOUNT_C,
                levy_amount_d=item_data.LEVY_AMOUNT_D,
                item_category=item_data.ITEM_CATEGORY if hasattr(item_data, 'ITEM_CATEGORY') else None
            )
            invoice_items.append(item)
        
        # Save to database
        db.add(submission)
        db.add(invoice)
        db.add_all(invoice_items)
        db.commit()
        
        logger.info(
            f"Invoice submission received: {submission_id}",
            extra={"business_id": str(business.id)}
        )
        
        # Queue for background processing to GRA
        background_tasks.add_task(
            _process_submission_async,
            submission_id,
            str(business.id),
            submission_data.model_dump(),
            db
        )
        
        return InvoiceAcceptedResponseSchema(
            submission_id=submission_id,
            invoice_num=submission_data.header.NUM,
            status="RECEIVED",
            message="Invoice received and queued for GRA processing",
            validation_passed=True,
            next_action="Check status using submission_id"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process invoice submission"
        )


@router.get("/{submission_id}/status", response_model=InvoiceResponseSchema)
async def get_invoice_status(
    submission_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get current status of an invoice submission
    
    - Returns submission status
    - Shows GRA response if available
    - Includes processing time
    """
    try:
        # Get business from API key
        from app.services.business_service import BusinessService
        business = BusinessService.get_business_by_api_key(db, api_key)
        if not business:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        submission = db.query(Submission).filter(
            Submission.id == submission_id,
            Submission.business_id == business.id,
            Submission.submission_type == "INVOICE"
        ).first()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice submission not found"
            )
        
        invoice = db.query(Invoice).filter(
            Invoice.submission_id == submission_id
        ).first()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        # Calculate processing time
        processing_time_ms = None
        if submission.completed_at:
            delta = submission.completed_at - submission.submitted_at
            processing_time_ms = int(delta.total_seconds() * 1000)
        
        logger.info(
            f"Invoice status retrieved: {submission_id}",
            extra={"business_id": str(business.id)}
        )
        
        return InvoiceResponseSchema(
            submission_id=submission_id,
            invoice_num=invoice.invoice_num,
            status=submission.submission_status,
            gra_response_code=submission.gra_response_code,
            gra_response_message=submission.gra_response_message,
            gra_invoice_id=submission.gra_invoice_id,
            gra_qr_code=submission.gra_qr_code,
            gra_receipt_num=submission.gra_receipt_num,
            submitted_at=submission.submitted_at,
            completed_at=submission.completed_at,
            processing_time_ms=processing_time_ms
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving invoice status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoice status"
        )


@router.get("/{submission_id}/details", response_model=dict)
async def get_invoice_details(
    submission_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get full invoice details with all items and GRA response
    
    - Returns complete invoice information
    - Includes all line items
    - Shows GRA response and signature
    """
    try:
        # Get business from API key
        from app.services.business_service import BusinessService
        business = BusinessService.get_business_by_api_key(db, api_key)
        if not business:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        submission = db.query(Submission).filter(
            Submission.id == submission_id,
            Submission.business_id == business.id,
            Submission.submission_type == "INVOICE"
        ).first()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice submission not found"
            )
        
        invoice = db.query(Invoice).filter(
            Invoice.submission_id == submission_id
        ).first()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        # Get invoice items
        items = db.query(InvoiceItem).filter(
            InvoiceItem.invoice_id == invoice.id
        ).all()
        
        # Build response
        invoice_details = {
            "submission_id": submission_id,
            "invoice_num": invoice.invoice_num,
            "invoice_date": invoice.invoice_date,
            "client_name": invoice.client_name,
            "client_tin": invoice.client_tin,
            "total_amount": invoice.total_amount,
            "total_vat": invoice.total_vat,
            "total_levy": invoice.total_levy,
            "status": submission.submission_status,
            "items": [
                {
                    "itmref": item.itmref,
                    "itmdes": item.itmdes,
                    "quantity": item.quantity,
                    "unityprice": item.unityprice,
                    "taxcode": item.taxcode,
                    "taxrate": item.taxrate,
                    "levy_amount_a": item.levy_amount_a,
                    "levy_amount_b": item.levy_amount_b,
                    "levy_amount_c": item.levy_amount_c,
                    "levy_amount_d": item.levy_amount_d
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
        
        logger.info(
            f"Invoice details retrieved: {submission_id}",
            extra={"business_id": str(business.id)}
        )
        
        return invoice_details
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving invoice details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoice details"
        )


@router.get("/{submission_id}/signature", response_model=InvoiceSignatureResponseSchema)
async def get_invoice_signature(
    submission_id: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Get invoice signature/stamping details from GRA
    
    - Returns VSDC signature details (ysdcid, ysdcrecnum, ysdcintdata, ysdcnrc)
    - Returns GRA QR code for printing
    - Returns GRA invoice ID and receipt number
    - Used for invoice stamping and compliance
    
    **Validates: Requirements REQ-INV-028, REQ-INV-029, REQ-INV-030**
    """
    try:
        # Get business from API key
        from app.services.business_service import BusinessService
        business = BusinessService.get_business_by_api_key(db, api_key)
        if not business:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Get submission
        submission = db.query(Submission).filter(
            Submission.id == submission_id,
            Submission.business_id == business.id,
            Submission.submission_type == "INVOICE"
        ).first()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice submission not found"
            )
        
        # Get invoice
        invoice = db.query(Invoice).filter(
            Invoice.submission_id == submission_id
        ).first()
        
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        logger.info(
            f"Invoice signature retrieved: {submission_id}",
            extra={"business_id": str(business.id)}
        )
        
        return InvoiceSignatureResponseSchema(
            submission_id=submission_id,
            invoice_num=invoice.invoice_num,
            status=submission.submission_status,
            ysdcid=submission.ysdcid,
            ysdcrecnum=submission.ysdcrecnum,
            ysdcintdata=submission.ysdcintdata,
            ysdcnrc=submission.ysdcnrc,
            gra_qr_code=submission.gra_qr_code,
            gra_invoice_id=submission.gra_invoice_id,
            gra_receipt_num=submission.gra_receipt_num,
            gra_response_code=submission.gra_response_code,
            gra_response_message=submission.gra_response_message,
            completed_at=submission.completed_at
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving invoice signature: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoice signature"
        )

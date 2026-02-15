"""Service for processing submissions to GRA"""
import asyncio
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID

from app.services.gra_client import get_gra_client, GRAClientError, ErrorType
from app.services.business_service import BusinessService
from app.services.gra_polling import GRAPollingService
from app.services.webhook_event_manager import WebhookEventManager
from app.models.models import Submission
from app.logger import get_logger

logger = get_logger(__name__)


class SubmissionProcessor:
    """Processes submissions and forwards them to GRA"""
    
    @staticmethod
    async def process_json_submission(
        db: Session,
        submission_id: str,
        business_id: UUID,
        request_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process a JSON submission and forward to GRA
        
        Args:
            db: Database session
            submission_id: Submission ID
            business_id: Business ID
            request_data: Request data to submit to GRA
            
        Returns:
            Response from GRA
            
        Raises:
            GRAClientError: If GRA submission fails
        """
        try:
            # Get business and decrypt GRA credentials
            business = BusinessService.get_business_by_id(db, business_id)
            if not business:
                raise ValueError(f"Business {business_id} not found")
            
            gra_credentials = BusinessService.get_decrypted_gra_credentials(db, business_id)
            
            # Inject GRA credentials into request
            submission_payload = SubmissionProcessor._inject_gra_credentials(
                request_data,
                gra_credentials
            )
            
            # Update submission status to PROCESSING
            submission = db.query(Submission).filter(
                Submission.id == submission_id
            ).first()
            
            if not submission:
                raise ValueError(f"Submission {submission_id} not found")
            
            submission.submission_status = "PROCESSING"
            db.commit()
            
            logger.info(
                f"Processing JSON submission to GRA: {submission_id}",
                extra={"business_id": str(business_id)}
            )
            
            # Submit to GRA
            gra_client = get_gra_client()
            
            # Determine endpoint based on submission type
            # All submissions (invoices, refunds, purchases) use the same endpoint
            # The FLAG field in the payload determines the type
            endpoint = "/post_receipt_Json.jsp"
            
            gra_response = await gra_client.submit_json(
                endpoint=endpoint,
                data=submission_payload
            )
            
            # Update submission with GRA response
            submission.submission_status = "PENDING_GRA"
            submission.raw_response = json.dumps(gra_response)
            submission.submitted_at = datetime.utcnow()
            
            # Extract GRA response details
            if "gra_response_code" in gra_response:
                submission.gra_response_code = gra_response.get("gra_response_code")
                submission.gra_response_message = gra_response.get("gra_response_message")
            
            # Extract signature/stamping details from VSDC
            if "ysdcid" in gra_response:
                submission.ysdcid = gra_response.get("ysdcid")
            if "ysdcrecnum" in gra_response:
                submission.ysdcrecnum = gra_response.get("ysdcrecnum")
            if "ysdcintdata" in gra_response:
                submission.ysdcintdata = gra_response.get("ysdcintdata")
            if "ysdcnrc" in gra_response:
                submission.ysdcnrc = gra_response.get("ysdcnrc")
            
            if "gra_invoice_id" in gra_response:
                submission.gra_invoice_id = gra_response.get("gra_invoice_id")
                submission.gra_qr_code = gra_response.get("gra_qr_code")
                submission.gra_receipt_num = gra_response.get("gra_receipt_num")
                submission.submission_status = "SUCCESS"
                submission.completed_at = datetime.utcnow()
            
            db.commit()
            
            # If submission is not yet complete, start polling for response
            if submission.submission_status == "PENDING_GRA":
                logger.info(
                    f"Starting polling for JSON submission: {submission_id}",
                    extra={"submission_id": submission_id}
                )
                
                try:
                    # Poll GRA for response (with timeout)
                    polling_result = await GRAPollingService.poll_for_response(
                        db=db,
                        submission_id=submission_id,
                        business_id=business_id,
                        poll_interval=5,  # Poll every 5 seconds
                        max_attempts=120,  # Max 10 minutes
                        timeout=600,  # 10 minute timeout
                    )
                    
                    logger.info(
                        f"Polling completed for JSON submission: {submission_id}",
                        extra={
                            "submission_id": submission_id,
                            "final_status": polling_result.get("status"),
                        }
                    )
                
                except TimeoutError as e:
                    logger.warning(
                        f"Polling timeout for JSON submission: {submission_id}",
                        extra={
                            "submission_id": submission_id,
                            "error": str(e),
                        }
                    )
                    # Submission remains in PENDING_GRA status
                
                except Exception as e:
                    logger.error(
                        f"Polling error for JSON submission: {submission_id}",
                        extra={
                            "submission_id": submission_id,
                            "error": str(e),
                        }
                    )
            
            logger.info(
                f"JSON submission processed successfully: {submission_id}",
                extra={
                    "business_id": str(business_id),
                    "gra_response_code": submission.gra_response_code
                }
            )
            
            # Trigger webhook event if submission is complete
            if submission.submission_status in ["SUCCESS", "FAILED"]:
                try:
                    WebhookEventManager.trigger_webhook_event(db, submission)
                except Exception as e:
                    logger.error(
                        f"Error triggering webhook event: {str(e)}",
                        extra={
                            "submission_id": submission_id,
                            "error": str(e),
                        }
                    )
            
            return gra_response
        
        except GRAClientError as e:
            logger.error(
                f"GRA client error processing submission: {submission_id}",
                extra={
                    "business_id": str(business_id),
                    "error": str(e),
                    "error_type": e.error_type.value if e.error_type else None
                }
            )
            
            # Update submission with error
            submission = db.query(Submission).filter(
                Submission.id == submission_id
            ).first()
            
            if submission:
                submission.submission_status = "FAILED"
                submission.gra_response_code = e.response_data.get("gra_response_code")
                submission.gra_response_message = e.response_data.get("gra_response_message")
                submission.error_details = json.dumps({
                    "error": str(e),
                    "error_type": e.error_type.value if e.error_type else None,
                    "response_data": e.response_data
                })
                submission.completed_at = datetime.utcnow()
                db.commit()
                
                # Trigger webhook event for failure
                try:
                    WebhookEventManager.trigger_webhook_event(db, submission)
                except Exception as webhook_error:
                    logger.error(
                        f"Error triggering webhook event: {str(webhook_error)}",
                        extra={
                            "submission_id": submission_id,
                            "error": str(webhook_error),
                        }
                    )
            
            raise
        
        except Exception as e:
            logger.error(
                f"Unexpected error processing submission: {submission_id}",
                extra={
                    "business_id": str(business_id),
                    "error": str(e)
                }
            )
            
            # Update submission with error
            submission = db.query(Submission).filter(
                Submission.id == submission_id
            ).first()
            
            if submission:
                submission.submission_status = "FAILED"
                submission.error_details = json.dumps({
                    "error": str(e),
                    "error_type": "UNKNOWN"
                })
                submission.completed_at = datetime.utcnow()
                db.commit()
                
                # Trigger webhook event for failure
                try:
                    WebhookEventManager.trigger_webhook_event(db, submission)
                except Exception as webhook_error:
                    logger.error(
                        f"Error triggering webhook event: {str(webhook_error)}",
                        extra={
                            "submission_id": submission_id,
                            "error": str(webhook_error),
                        }
                    )
            
            raise
    
    @staticmethod
    async def process_xml_submission(
        db: Session,
        submission_id: str,
        business_id: UUID,
        request_data: str,
    ) -> Dict[str, Any]:
        """
        Process an XML submission and forward to GRA
        
        Args:
            db: Database session
            submission_id: Submission ID
            business_id: Business ID
            request_data: XML request data to submit to GRA
            
        Returns:
            Response from GRA
            
        Raises:
            GRAClientError: If GRA submission fails
        """
        try:
            # Get business and decrypt GRA credentials
            business = BusinessService.get_business_by_id(db, business_id)
            if not business:
                raise ValueError(f"Business {business_id} not found")
            
            gra_credentials = BusinessService.get_decrypted_gra_credentials(db, business_id)
            
            # Inject GRA credentials into XML request
            submission_payload = SubmissionProcessor._inject_gra_credentials_xml(
                request_data,
                gra_credentials
            )
            
            # Update submission status to PROCESSING
            submission = db.query(Submission).filter(
                Submission.id == submission_id
            ).first()
            
            if not submission:
                raise ValueError(f"Submission {submission_id} not found")
            
            submission.submission_status = "PROCESSING"
            db.commit()
            
            logger.info(
                f"Processing XML submission to GRA: {submission_id}",
                extra={"business_id": str(business_id)}
            )
            
            # Submit to GRA
            gra_client = get_gra_client()
            gra_response = await gra_client.submit_xml(
                endpoint="/api/v1/invoices/submit",
                data=submission_payload
            )
            
            # Update submission with GRA response
            submission.submission_status = "PENDING_GRA"
            submission.raw_response = json.dumps(gra_response)
            submission.submitted_at = datetime.utcnow()
            
            # Extract GRA response details
            if "gra_response_code" in gra_response:
                submission.gra_response_code = gra_response.get("gra_response_code")
                submission.gra_response_message = gra_response.get("gra_response_message")
            
            # Extract signature/stamping details from VSDC
            if "ysdcid" in gra_response:
                submission.ysdcid = gra_response.get("ysdcid")
            if "ysdcrecnum" in gra_response:
                submission.ysdcrecnum = gra_response.get("ysdcrecnum")
            if "ysdcintdata" in gra_response:
                submission.ysdcintdata = gra_response.get("ysdcintdata")
            if "ysdcnrc" in gra_response:
                submission.ysdcnrc = gra_response.get("ysdcnrc")
            
            if "gra_invoice_id" in gra_response:
                submission.gra_invoice_id = gra_response.get("gra_invoice_id")
                submission.gra_qr_code = gra_response.get("gra_qr_code")
                submission.gra_receipt_num = gra_response.get("gra_receipt_num")
                submission.submission_status = "SUCCESS"
                submission.completed_at = datetime.utcnow()
            
            db.commit()
            
            # If submission is not yet complete, start polling for response
            if submission.submission_status == "PENDING_GRA":
                logger.info(
                    f"Starting polling for XML submission: {submission_id}",
                    extra={"submission_id": submission_id}
                )
                
                try:
                    # Poll GRA for response (with timeout)
                    polling_result = await GRAPollingService.poll_for_response(
                        db=db,
                        submission_id=submission_id,
                        business_id=business_id,
                        poll_interval=5,  # Poll every 5 seconds
                        max_attempts=120,  # Max 10 minutes
                        timeout=600,  # 10 minute timeout
                    )
                    
                    logger.info(
                        f"Polling completed for XML submission: {submission_id}",
                        extra={
                            "submission_id": submission_id,
                            "final_status": polling_result.get("status"),
                        }
                    )
                
                except TimeoutError as e:
                    logger.warning(
                        f"Polling timeout for XML submission: {submission_id}",
                        extra={
                            "submission_id": submission_id,
                            "error": str(e),
                        }
                    )
                    # Submission remains in PENDING_GRA status
                
                except Exception as e:
                    logger.error(
                        f"Polling error for XML submission: {submission_id}",
                        extra={
                            "submission_id": submission_id,
                            "error": str(e),
                        }
                    )
            
            logger.info(
                f"XML submission processed successfully: {submission_id}",
                extra={
                    "business_id": str(business_id),
                    "gra_response_code": submission.gra_response_code
                }
            )
            
            # Trigger webhook event if submission is complete
            if submission.submission_status in ["SUCCESS", "FAILED"]:
                try:
                    WebhookEventManager.trigger_webhook_event(db, submission)
                except Exception as e:
                    logger.error(
                        f"Error triggering webhook event: {str(e)}",
                        extra={
                            "submission_id": submission_id,
                            "error": str(e),
                        }
                    )
            
            return gra_response
        
        except GRAClientError as e:
            logger.error(
                f"GRA client error processing XML submission: {submission_id}",
                extra={
                    "business_id": str(business_id),
                    "error": str(e),
                    "error_type": e.error_type.value if e.error_type else None
                }
            )
            
            # Update submission with error
            submission = db.query(Submission).filter(
                Submission.id == submission_id
            ).first()
            
            if submission:
                submission.submission_status = "FAILED"
                submission.gra_response_code = e.response_data.get("gra_response_code")
                submission.gra_response_message = e.response_data.get("gra_response_message")
                submission.error_details = json.dumps({
                    "error": str(e),
                    "error_type": e.error_type.value if e.error_type else None,
                    "response_data": e.response_data
                })
                submission.completed_at = datetime.utcnow()
                db.commit()
                
                # Trigger webhook event for failure
                try:
                    WebhookEventManager.trigger_webhook_event(db, submission)
                except Exception as webhook_error:
                    logger.error(
                        f"Error triggering webhook event: {str(webhook_error)}",
                        extra={
                            "submission_id": submission_id,
                            "error": str(webhook_error),
                        }
                    )
            
            raise
        
        except Exception as e:
            logger.error(
                f"Unexpected error processing XML submission: {submission_id}",
                extra={
                    "business_id": str(business_id),
                    "error": str(e)
                }
            )
            
            # Update submission with error
            submission = db.query(Submission).filter(
                Submission.id == submission_id
            ).first()
            
            if submission:
                submission.submission_status = "FAILED"
                submission.error_details = json.dumps({
                    "error": str(e),
                    "error_type": "UNKNOWN"
                })
                submission.completed_at = datetime.utcnow()
                db.commit()
                
                # Trigger webhook event for failure
                try:
                    WebhookEventManager.trigger_webhook_event(db, submission)
                except Exception as webhook_error:
                    logger.error(
                        f"Error triggering webhook event: {str(webhook_error)}",
                        extra={
                            "submission_id": submission_id,
                            "error": str(webhook_error),
                        }
                    )
            
            raise
    
    @staticmethod
    def _inject_gra_credentials(
        request_data: Dict[str, Any],
        gra_credentials: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Inject GRA credentials into request payload
        
        Args:
            request_data: Original request data
            gra_credentials: Decrypted GRA credentials
            
        Returns:
            Request data with injected credentials
        """
        # Create a copy to avoid modifying original
        payload = json.loads(json.dumps(request_data))
        
        # Ensure company section exists
        if "company" not in payload:
            payload["company"] = {}
        
        # Inject GRA credentials
        payload["company"]["COMPANY_TIN"] = gra_credentials.get("gra_tin")
        payload["company"]["COMPANY_NAMES"] = gra_credentials.get("gra_company_name")
        payload["company"]["COMPANY_SECURITY_KEY"] = gra_credentials.get("gra_security_key")
        
        return payload
    
    @staticmethod
    def _inject_gra_credentials_xml(
        xml_string: str,
        gra_credentials: Dict[str, str]
    ) -> str:
        """
        Inject GRA credentials into XML request payload
        
        Args:
            xml_string: Original XML request data
            gra_credentials: Decrypted GRA credentials
            
        Returns:
            XML string with injected credentials
        """
        try:
            # Parse XML
            root = ET.fromstring(xml_string)
            
            # Find or create company section
            company_elem = root.find("company")
            if company_elem is None:
                company_elem = ET.Element("company")
                root.insert(0, company_elem)
            
            # Inject GRA credentials
            tin_elem = company_elem.find("COMPANY_TIN")
            if tin_elem is None:
                tin_elem = ET.SubElement(company_elem, "COMPANY_TIN")
            tin_elem.text = gra_credentials.get("gra_tin")
            
            names_elem = company_elem.find("COMPANY_NAMES")
            if names_elem is None:
                names_elem = ET.SubElement(company_elem, "COMPANY_NAMES")
            names_elem.text = gra_credentials.get("gra_company_name")
            
            key_elem = company_elem.find("COMPANY_SECURITY_KEY")
            if key_elem is None:
                key_elem = ET.SubElement(company_elem, "COMPANY_SECURITY_KEY")
            key_elem.text = gra_credentials.get("gra_security_key")
            
            # Convert back to string
            return ET.tostring(root, encoding="unicode")
        
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML: {str(e)}")

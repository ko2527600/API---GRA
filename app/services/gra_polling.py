"""Service for polling GRA responses and updating submission status"""
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from uuid import UUID
import time

from app.services.gra_client import get_gra_client, GRAClientError, ErrorType
from app.models.models import Submission, SubmissionStatus
from app.logger import get_logger

logger = get_logger(__name__)


class GRAPollingService:
    """Service for polling GRA responses and updating submission status"""
    
    # Default polling configuration
    DEFAULT_POLL_INTERVAL = 5  # seconds
    DEFAULT_MAX_POLL_ATTEMPTS = 120  # 10 minutes with 5s interval
    DEFAULT_POLL_TIMEOUT = 600  # 10 minutes total
    
    @staticmethod
    async def poll_for_response(
        db: Session,
        submission_id: str,
        business_id: UUID,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        max_attempts: int = DEFAULT_MAX_POLL_ATTEMPTS,
        timeout: int = DEFAULT_POLL_TIMEOUT,
    ) -> Dict[str, Any]:
        """
        Poll GRA for submission response until completion or timeout
        
        Args:
            db: Database session
            submission_id: Submission ID to poll for
            business_id: Business ID (for logging)
            poll_interval: Seconds between polls
            max_attempts: Maximum number of poll attempts
            timeout: Total timeout in seconds
            
        Returns:
            Final submission status and response
            
        Raises:
            TimeoutError: If polling times out
            ValueError: If submission not found
        """
        start_time = time.time()
        attempt = 0
        
        logger.info(
            f"Starting polling for submission: {submission_id}",
            extra={
                "submission_id": submission_id,
                "business_id": str(business_id),
                "poll_interval": poll_interval,
                "max_attempts": max_attempts,
                "timeout": timeout,
            }
        )
        
        while attempt < max_attempts:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logger.error(
                    f"Polling timeout for submission: {submission_id}",
                    extra={
                        "submission_id": submission_id,
                        "business_id": str(business_id),
                        "elapsed_seconds": elapsed,
                        "timeout": timeout,
                        "attempts": attempt,
                    }
                )
                raise TimeoutError(
                    f"Polling timeout after {elapsed:.1f}s and {attempt} attempts"
                )
            
            try:
                # Get submission from database
                submission = db.query(Submission).filter(
                    Submission.id == submission_id
                ).first()
                
                if not submission:
                    raise ValueError(f"Submission {submission_id} not found")
                
                # Check if submission is already completed
                if submission.submission_status in [
                    SubmissionStatus.SUCCESS.value,
                    SubmissionStatus.FAILED.value,
                ]:
                    logger.info(
                        f"Submission already completed: {submission_id}",
                        extra={
                            "submission_id": submission_id,
                            "status": submission.submission_status,
                            "attempts": attempt,
                        }
                    )
                    
                    return {
                        "submission_id": submission_id,
                        "status": submission.submission_status,
                        "gra_response_code": submission.gra_response_code,
                        "gra_invoice_id": submission.gra_invoice_id,
                        "gra_qr_code": submission.gra_qr_code,
                        "gra_receipt_num": submission.gra_receipt_num,
                        "completed_at": submission.completed_at,
                        "attempts": attempt,
                    }
                
                # Poll GRA for status
                logger.debug(
                    f"Polling GRA for submission status: {submission_id} (attempt {attempt + 1})",
                    extra={
                        "submission_id": submission_id,
                        "attempt": attempt + 1,
                    }
                )
                
                gra_response = await GRAPollingService._poll_gra_status(
                    submission_id=submission_id,
                    submission_type=submission.submission_type,
                )
                
                # Update submission with GRA response
                await GRAPollingService._update_submission_from_response(
                    db=db,
                    submission=submission,
                    gra_response=gra_response,
                )
                
                # Check if submission is now completed
                if submission.submission_status in [
                    SubmissionStatus.SUCCESS.value,
                    SubmissionStatus.FAILED.value,
                ]:
                    logger.info(
                        f"Submission completed after polling: {submission_id}",
                        extra={
                            "submission_id": submission_id,
                            "status": submission.submission_status,
                            "attempts": attempt,
                        }
                    )
                    
                    return {
                        "submission_id": submission_id,
                        "status": submission.submission_status,
                        "gra_response_code": submission.gra_response_code,
                        "gra_invoice_id": submission.gra_invoice_id,
                        "gra_qr_code": submission.gra_qr_code,
                        "gra_receipt_num": submission.gra_receipt_num,
                        "completed_at": submission.completed_at,
                        "attempts": attempt,
                    }
                
                # Wait before next poll
                logger.debug(
                    f"Waiting {poll_interval}s before next poll",
                    extra={
                        "submission_id": submission_id,
                        "poll_interval": poll_interval,
                    }
                )
                
                await asyncio.sleep(poll_interval)
                attempt += 1
            
            except GRAClientError as e:
                logger.warning(
                    f"GRA client error during polling: {submission_id}",
                    extra={
                        "submission_id": submission_id,
                        "error": str(e),
                        "error_type": e.error_type.value if e.error_type else None,
                        "attempt": attempt + 1,
                    }
                )
                
                # If error is not retryable, fail the submission
                if not e.is_retryable():
                    submission = db.query(Submission).filter(
                        Submission.id == submission_id
                    ).first()
                    
                    if submission:
                        submission.submission_status = SubmissionStatus.FAILED.value
                        submission.gra_response_code = e.response_data.get("gra_response_code")
                        submission.gra_response_message = e.response_data.get("gra_response_message")
                        submission.error_details = json.dumps({
                            "error": str(e),
                            "error_type": e.error_type.value if e.error_type else None,
                            "response_data": e.response_data,
                        })
                        submission.completed_at = datetime.utcnow()
                        db.commit()
                    
                    raise
                
                # Wait before retry
                await asyncio.sleep(poll_interval)
                attempt += 1
            
            except Exception as e:
                logger.error(
                    f"Unexpected error during polling: {submission_id}",
                    extra={
                        "submission_id": submission_id,
                        "error": str(e),
                        "attempt": attempt + 1,
                    }
                )
                
                # Wait before retry
                await asyncio.sleep(poll_interval)
                attempt += 1
        
        # Max attempts exceeded
        logger.error(
            f"Polling max attempts exceeded for submission: {submission_id}",
            extra={
                "submission_id": submission_id,
                "business_id": str(business_id),
                "max_attempts": max_attempts,
                "elapsed_seconds": time.time() - start_time,
            }
        )
        
        raise TimeoutError(
            f"Polling max attempts ({max_attempts}) exceeded for submission {submission_id}"
        )
    
    @staticmethod
    async def _poll_gra_status(
        submission_id: str,
        submission_type: str,
    ) -> Dict[str, Any]:
        """
        Poll GRA for submission status
        
        Args:
            submission_id: Submission ID
            submission_type: Type of submission (INVOICE, REFUND, etc)
            
        Returns:
            GRA response data
            
        Raises:
            GRAClientError: If GRA request fails
        """
        gra_client = get_gra_client()
        
        # Determine endpoint based on submission type
        if submission_type == "INVOICE":
            endpoint = f"/api/v1/invoices/{submission_id}/status"
        elif submission_type == "REFUND":
            endpoint = f"/api/v1/refunds/{submission_id}/status"
        elif submission_type == "PURCHASE":
            endpoint = f"/api/v1/purchases/{submission_id}/status"
        else:
            endpoint = f"/api/v1/submissions/{submission_id}/status"
        
        logger.debug(
            f"Polling GRA status endpoint: {endpoint}",
            extra={
                "submission_id": submission_id,
                "submission_type": submission_type,
                "endpoint": endpoint,
            }
        )
        
        # Get status from GRA
        response = await gra_client.get_status(endpoint)
        
        logger.debug(
            f"GRA status response received: {submission_id}",
            extra={
                "submission_id": submission_id,
                "response_keys": list(response.keys()),
            }
        )
        
        return response
    
    @staticmethod
    async def _update_submission_from_response(
        db: Session,
        submission: Submission,
        gra_response: Dict[str, Any],
    ) -> None:
        """
        Update submission with GRA response data
        
        Args:
            db: Database session
            submission: Submission model instance
            gra_response: GRA response data
        """
        # Store raw response
        submission.raw_response = json.dumps(gra_response)
        
        # Extract status from response
        status = gra_response.get("status") or gra_response.get("submission_status")
        
        # Map GRA status to our status
        if status == "SUCCESS" or status == "COMPLETED":
            submission.submission_status = SubmissionStatus.SUCCESS.value
            submission.completed_at = datetime.utcnow()
            
            # Extract GRA response details
            if "gra_invoice_id" in gra_response:
                submission.gra_invoice_id = gra_response.get("gra_invoice_id")
            if "gra_qr_code" in gra_response:
                submission.gra_qr_code = gra_response.get("gra_qr_code")
            if "gra_receipt_num" in gra_response:
                submission.gra_receipt_num = gra_response.get("gra_receipt_num")
            
            # Extract signature/stamping details from VSDC
            if "ysdcid" in gra_response:
                submission.ysdcid = gra_response.get("ysdcid")
            if "ysdcrecnum" in gra_response:
                submission.ysdcrecnum = gra_response.get("ysdcrecnum")
            if "ysdcintdata" in gra_response:
                submission.ysdcintdata = gra_response.get("ysdcintdata")
            if "ysdcnrc" in gra_response:
                submission.ysdcnrc = gra_response.get("ysdcnrc")
            
            logger.info(
                f"Submission marked as SUCCESS: {submission.id}",
                extra={
                    "submission_id": str(submission.id),
                    "gra_invoice_id": submission.gra_invoice_id,
                    "ysdcid": submission.ysdcid,
                }
            )
        
        elif status == "FAILED" or status == "REJECTED":
            submission.submission_status = SubmissionStatus.FAILED.value
            submission.completed_at = datetime.utcnow()
            
            # Extract error details
            if "gra_response_code" in gra_response:
                submission.gra_response_code = gra_response.get("gra_response_code")
            if "gra_response_message" in gra_response:
                submission.gra_response_message = gra_response.get("gra_response_message")
            if "error_details" in gra_response:
                submission.error_details = json.dumps(gra_response.get("error_details"))
            
            logger.warning(
                f"Submission marked as FAILED: {submission.id}",
                extra={
                    "submission_id": str(submission.id),
                    "gra_response_code": submission.gra_response_code,
                }
            )
        
        elif status == "PROCESSING" or status == "PENDING":
            # Still processing, keep current status
            submission.submission_status = SubmissionStatus.PENDING_GRA.value
            
            logger.debug(
                f"Submission still processing: {submission.id}",
                extra={"submission_id": str(submission.id)}
            )
        
        else:
            # Unknown status, log warning
            logger.warning(
                f"Unknown GRA status: {status}",
                extra={
                    "submission_id": str(submission.id),
                    "status": status,
                }
            )
        
        # Commit changes
        db.commit()
    
    @staticmethod
    async def poll_multiple_submissions(
        db: Session,
        submission_ids: List[str],
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        max_attempts: int = DEFAULT_MAX_POLL_ATTEMPTS,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Poll multiple submissions concurrently
        
        Args:
            db: Database session
            submission_ids: List of submission IDs to poll
            poll_interval: Seconds between polls
            max_attempts: Maximum number of poll attempts
            
        Returns:
            Dictionary mapping submission_id to final status
        """
        logger.info(
            f"Starting concurrent polling for {len(submission_ids)} submissions",
            extra={"submission_count": len(submission_ids)}
        )
        
        tasks = []
        for submission_id in submission_ids:
            # Get business_id for logging
            submission = db.query(Submission).filter(
                Submission.id == submission_id
            ).first()
            
            if submission:
                task = GRAPollingService.poll_for_response(
                    db=db,
                    submission_id=submission_id,
                    business_id=submission.business_id,
                    poll_interval=poll_interval,
                    max_attempts=max_attempts,
                )
                tasks.append(task)
        
        # Run all polling tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results to submission IDs
        response_map = {}
        for submission_id, result in zip(submission_ids, results):
            if isinstance(result, Exception):
                response_map[submission_id] = {
                    "error": str(result),
                    "status": "ERROR",
                }
            else:
                response_map[submission_id] = result
        
        logger.info(
            f"Concurrent polling completed for {len(submission_ids)} submissions",
            extra={"submission_count": len(submission_ids)}
        )
        
        return response_map


def get_gra_polling_service() -> GRAPollingService:
    """Get GRA polling service instance"""
    return GRAPollingService()

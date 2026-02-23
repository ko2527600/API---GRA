"""Tests for GRA polling service"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from app.services.gra_polling import GRAPollingService
from app.models.models import Submission, SubmissionStatus
from app.database import SessionLocal


class TestGRAPollingService:
    """Tests for GRA polling service"""
    
    @pytest.fixture
    def submission_id(self):
        """Create a test submission ID"""
        return uuid4()
    
    @pytest.mark.asyncio
    async def test_poll_for_response_success(self, db_session, submission_id, business_id):
        """Test successful polling for response"""
        # Create a test submission
        submission = Submission(
            id=submission_id,
            business_id=business_id,
            submission_type="INVOICE",
            submission_status=SubmissionStatus.PENDING_GRA.value,
            raw_request={"test": "data"},
        )
        db_session.add(submission)
        db_session.commit()
        
        # Mock GRA response
        gra_response = {
            "status": "SUCCESS",
            "gra_invoice_id": "GRA-INV-001",
            "gra_qr_code": "https://gra.gov.gh/qr/123",
            "gra_receipt_num": "VSDC-REC-001",
        }
        
        with patch.object(
            GRAPollingService,
            "_poll_gra_status",
            new_callable=AsyncMock,
            return_value=gra_response,
        ):
            result = await GRAPollingService.poll_for_response(
                db=db_session,
                submission_id=str(submission_id),
                business_id=business_id,
                poll_interval=0.1,  # Short interval for testing
                max_attempts=5,
            )
        
        # Verify result
        assert result["status"] == SubmissionStatus.SUCCESS.value
        assert result["gra_invoice_id"] == "GRA-INV-001"
        assert result["attempts"] == 0
        
        # Verify submission was updated
        updated_submission = db_session.query(Submission).filter(
            Submission.id == submission_id
        ).first()
        assert updated_submission.submission_status == SubmissionStatus.SUCCESS.value
        assert updated_submission.gra_invoice_id == "GRA-INV-001"
    
    @pytest.mark.asyncio
    async def test_poll_for_response_failure(self, db_session, submission_id, business_id):
        """Test polling for failed response"""
        # Create a test submission
        submission = Submission(
            id=submission_id,
            business_id=business_id,
            submission_type="INVOICE",
            submission_status=SubmissionStatus.PENDING_GRA.value,
            raw_request={"test": "data"},
        )
        db_session.add(submission)
        db_session.commit()
        
        # Mock GRA response with failure
        gra_response = {
            "status": "FAILED",
            "gra_response_code": "B16",
            "gra_response_message": "INVOICE TOTAL AMOUNT DIFFERENT",
            "error_details": {"field": "TOTAL_AMOUNT"},
        }
        
        with patch.object(
            GRAPollingService,
            "_poll_gra_status",
            new_callable=AsyncMock,
            return_value=gra_response,
        ):
            result = await GRAPollingService.poll_for_response(
                db=db_session,
                submission_id=str(submission_id),
                business_id=business_id,
                poll_interval=0.1,
                max_attempts=5,
            )
        
        # Verify result
        assert result["status"] == SubmissionStatus.FAILED.value
        assert result["gra_response_code"] == "B16"
        
        # Verify submission was updated
        updated_submission = db_session.query(Submission).filter(
            Submission.id == submission_id
        ).first()
        assert updated_submission.submission_status == SubmissionStatus.FAILED.value
        assert updated_submission.gra_response_code == "B16"
    
    @pytest.mark.asyncio
    async def test_poll_for_response_already_completed(self, db_session, submission_id, business_id):
        """Test polling when submission is already completed"""
        # Create a completed submission
        submission = Submission(
            id=submission_id,
            business_id=business_id,
            submission_type="INVOICE",
            submission_status=SubmissionStatus.SUCCESS.value,
            gra_invoice_id="GRA-INV-001",
            gra_qr_code="https://gra.gov.gh/qr/123",
            gra_receipt_num="VSDC-REC-001",
            raw_request={"test": "data"},
            completed_at=datetime.utcnow(),
        )
        db_session.add(submission)
        db_session.commit()
        
        # Poll should return immediately
        result = await GRAPollingService.poll_for_response(
            db=db_session,
            submission_id=str(submission_id),
            business_id=business_id,
            poll_interval=0.1,
            max_attempts=5,
        )
        
        # Verify result
        assert result["status"] == SubmissionStatus.SUCCESS.value
        assert result["gra_invoice_id"] == "GRA-INV-001"
        assert result["attempts"] == 0
    
    @pytest.mark.asyncio
    async def test_poll_for_response_multiple_attempts(self, db_session, submission_id, business_id):
        """Test polling with multiple attempts before success"""
        # Create a test submission
        submission = Submission(
            id=submission_id,
            business_id=business_id,
            submission_type="INVOICE",
            submission_status=SubmissionStatus.PENDING_GRA.value,
            raw_request={"test": "data"},
        )
        db_session.add(submission)
        db_session.commit()
        
        # Mock GRA responses: first two are processing, third is success
        processing_response = {"status": "PROCESSING"}
        success_response = {
            "status": "SUCCESS",
            "gra_invoice_id": "GRA-INV-001",
            "gra_qr_code": "https://gra.gov.gh/qr/123",
            "gra_receipt_num": "VSDC-REC-001",
        }
        
        with patch.object(
            GRAPollingService,
            "_poll_gra_status",
            new_callable=AsyncMock,
            side_effect=[processing_response, processing_response, success_response],
        ):
            result = await GRAPollingService.poll_for_response(
                db=db_session,
                submission_id=str(submission_id),
                business_id=business_id,
                poll_interval=0.01,  # Very short for testing
                max_attempts=10,
            )
        
        # Verify result
        assert result["status"] == SubmissionStatus.SUCCESS.value
        assert result["attempts"] == 2  # 2 processing attempts before success
    
    @pytest.mark.asyncio
    async def test_poll_for_response_timeout(self, db_session, submission_id, business_id):
        """Test polling timeout"""
        # Create a test submission
        submission = Submission(
            id=submission_id,
            business_id=business_id,
            submission_type="INVOICE",
            submission_status=SubmissionStatus.PENDING_GRA.value,
            raw_request={"test": "data"},
        )
        db_session.add(submission)
        db_session.commit()
        
        # Mock GRA response that always returns processing
        processing_response = {"status": "PROCESSING"}
        
        with patch.object(
            GRAPollingService,
            "_poll_gra_status",
            new_callable=AsyncMock,
            return_value=processing_response,
        ):
            with pytest.raises(TimeoutError):
                await GRAPollingService.poll_for_response(
                    db=db_session,
                    submission_id=str(submission_id),
                    business_id=business_id,
                    poll_interval=0.01,
                    max_attempts=3,
                    timeout=0.05,  # Very short timeout for testing
                )
    
    @pytest.mark.asyncio
    async def test_poll_for_response_submission_not_found(self, db_session, submission_id, business_id):
        """Test polling when submission is not found"""
        with pytest.raises((ValueError, TimeoutError)):
            await GRAPollingService.poll_for_response(
                db=db_session,
                submission_id=str(submission_id),
                business_id=business_id,
                poll_interval=0.1,
                max_attempts=5,
            )
    
    @pytest.mark.asyncio
    async def test_poll_gra_status_invoice(self, db_session):
        """Test polling GRA status for invoice"""
        submission_id = str(uuid4())
        
        with patch("app.services.gra_polling.get_gra_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_status.return_value = {"status": "SUCCESS"}
            mock_get_client.return_value = mock_client
            
            result = await GRAPollingService._poll_gra_status(
                submission_id=submission_id,
                submission_type="INVOICE",
            )
            
            # Verify correct endpoint was called
            mock_client.get_status.assert_called_once()
            call_args = mock_client.get_status.call_args
            assert f"/api/v1/invoices/{submission_id}/status" in call_args[0][0]
            assert result["status"] == "SUCCESS"
    
    @pytest.mark.asyncio
    async def test_poll_gra_status_refund(self, db_session):
        """Test polling GRA status for refund"""
        submission_id = str(uuid4())
        
        with patch("app.services.gra_polling.get_gra_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_status.return_value = {"status": "SUCCESS"}
            mock_get_client.return_value = mock_client
            
            result = await GRAPollingService._poll_gra_status(
                submission_id=submission_id,
                submission_type="REFUND",
            )
            
            # Verify correct endpoint was called
            mock_client.get_status.assert_called_once()
            call_args = mock_client.get_status.call_args
            assert f"/api/v1/refunds/{submission_id}/status" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_poll_gra_status_purchase(self, db_session):
        """Test polling GRA status for purchase"""
        submission_id = str(uuid4())
        
        with patch("app.services.gra_polling.get_gra_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_status.return_value = {"status": "SUCCESS"}
            mock_get_client.return_value = mock_client
            
            result = await GRAPollingService._poll_gra_status(
                submission_id=submission_id,
                submission_type="PURCHASE",
            )
            
            # Verify correct endpoint was called
            mock_client.get_status.assert_called_once()
            call_args = mock_client.get_status.call_args
            assert f"/api/v1/purchases/{submission_id}/status" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_update_submission_from_response_success(self, db_session, submission_id, business_id):
        """Test updating submission from successful GRA response"""
        # Create a test submission
        submission = Submission(
            id=submission_id,
            business_id=business_id,
            submission_type="INVOICE",
            submission_status=SubmissionStatus.PENDING_GRA.value,
            raw_request={"test": "data"},
        )
        db_session.add(submission)
        db_session.commit()
        
        # GRA response
        gra_response = {
            "status": "SUCCESS",
            "gra_invoice_id": "GRA-INV-001",
            "gra_qr_code": "https://gra.gov.gh/qr/123",
            "gra_receipt_num": "VSDC-REC-001",
        }
        
        # Update submission
        await GRAPollingService._update_submission_from_response(
            db=db_session,
            submission=submission,
            gra_response=gra_response,
        )
        
        # Verify submission was updated
        assert submission.submission_status == SubmissionStatus.SUCCESS.value
        assert submission.gra_invoice_id == "GRA-INV-001"
        assert submission.gra_qr_code == "https://gra.gov.gh/qr/123"
        assert submission.gra_receipt_num == "VSDC-REC-001"
        assert submission.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_update_submission_from_response_failure(self, db_session, submission_id, business_id):
        """Test updating submission from failed GRA response"""
        # Create a test submission
        submission = Submission(
            id=submission_id,
            business_id=business_id,
            submission_type="INVOICE",
            submission_status=SubmissionStatus.PENDING_GRA.value,
            raw_request={"test": "data"},
        )
        db_session.add(submission)
        db_session.commit()
        
        # GRA response with failure
        gra_response = {
            "status": "FAILED",
            "gra_response_code": "B16",
            "gra_response_message": "INVOICE TOTAL AMOUNT DIFFERENT",
            "error_details": {"field": "TOTAL_AMOUNT"},
        }
        
        # Update submission
        await GRAPollingService._update_submission_from_response(
            db=db_session,
            submission=submission,
            gra_response=gra_response,
        )
        
        # Verify submission was updated
        assert submission.submission_status == SubmissionStatus.FAILED.value
        assert submission.gra_response_code == "B16"
        assert submission.gra_response_message == "INVOICE TOTAL AMOUNT DIFFERENT"
        assert submission.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_update_submission_from_response_processing(self, db_session, submission_id, business_id):
        """Test updating submission from processing GRA response"""
        # Create a test submission
        submission = Submission(
            id=submission_id,
            business_id=business_id,
            submission_type="INVOICE",
            submission_status=SubmissionStatus.PENDING_GRA.value,
            raw_request={"test": "data"},
        )
        db_session.add(submission)
        db_session.commit()
        
        # GRA response still processing
        gra_response = {"status": "PROCESSING"}
        
        # Update submission
        await GRAPollingService._update_submission_from_response(
            db=db_session,
            submission=submission,
            gra_response=gra_response,
        )
        
        # Verify submission status remains PENDING_GRA
        assert submission.submission_status == SubmissionStatus.PENDING_GRA.value
        assert submission.completed_at is None
    
    @pytest.mark.asyncio
    async def test_poll_multiple_submissions(self, db_session, business_id):
        """Test polling multiple submissions concurrently"""
        # Create multiple test submissions
        submission_ids = []
        for i in range(3):
            submission_id = uuid4()
            submission = Submission(
                id=submission_id,
                business_id=business_id,
                submission_type="INVOICE",
                submission_status=SubmissionStatus.PENDING_GRA.value,
                raw_request={"test": f"data{i}"},
            )
            db_session.add(submission)
            submission_ids.append(str(submission_id))
        db_session.commit()
        
        # Mock GRA responses
        gra_response = {
            "status": "SUCCESS",
            "gra_invoice_id": "GRA-INV-001",
            "gra_qr_code": "https://gra.gov.gh/qr/123",
            "gra_receipt_num": "VSDC-REC-001",
        }
        
        with patch.object(
            GRAPollingService,
            "_poll_gra_status",
            new_callable=AsyncMock,
            return_value=gra_response,
        ):
            results = await GRAPollingService.poll_multiple_submissions(
                db=db_session,
                submission_ids=submission_ids,
                poll_interval=0.01,
                max_attempts=5,
            )
        
        # Verify all submissions were polled
        assert len(results) == 3
        for submission_id in submission_ids:
            assert submission_id in results
            assert results[submission_id]["status"] == SubmissionStatus.SUCCESS.value
    
    @pytest.mark.asyncio
    async def test_poll_multiple_submissions_with_errors(self, db_session, business_id):
        """Test polling multiple submissions with some errors"""
        # Create multiple test submissions
        submission_ids = []
        for i in range(2):
            submission_id = uuid4()
            submission = Submission(
                id=submission_id,
                business_id=business_id,
                submission_type="INVOICE",
                submission_status=SubmissionStatus.PENDING_GRA.value,
                raw_request={"test": f"data{i}"},
            )
            db_session.add(submission)
            submission_ids.append(str(submission_id))
        db_session.commit()
        
        # Mock GRA responses: first succeeds, second fails
        success_response = {
            "status": "SUCCESS",
            "gra_invoice_id": "GRA-INV-001",
        }
        
        with patch.object(
            GRAPollingService,
            "_poll_gra_status",
            new_callable=AsyncMock,
            side_effect=[success_response, TimeoutError("Polling timeout")],
        ):
            results = await GRAPollingService.poll_multiple_submissions(
                db=db_session,
                submission_ids=submission_ids,
                poll_interval=0.01,
                max_attempts=2,
            )
        
        # Verify results
        assert len(results) == 2
        assert results[submission_ids[0]]["status"] == SubmissionStatus.SUCCESS.value
        assert "error" in results[submission_ids[1]]

    @pytest.mark.asyncio
    async def test_update_submission_stores_signature_details(self, db_session, submission_id, business_id):
        """Test that signature/stamping details are stored from GRA response"""
        # Create a test submission
        submission = Submission(
            id=submission_id,
            business_id=business_id,
            submission_type="INVOICE",
            submission_status=SubmissionStatus.PENDING_GRA.value,
            raw_request={"test": "data"},
        )
        db_session.add(submission)
        db_session.commit()
        
        # GRA response with signature details
        gra_response = {
            "status": "SUCCESS",
            "gra_invoice_id": "GRA-INV-001",
            "gra_qr_code": "https://gra.gov.gh/qr/123",
            "gra_receipt_num": "VSDC-REC-001",
            "ysdcid": "VSDC-ID-12345",
            "ysdcrecnum": "VSDC-REC-NUM-67890",
            "ysdcintdata": "INTEGRATED-DATA-ABC123",
            "ysdcnrc": "VSDC-NRC-XYZ789",
        }
        
        # Update submission
        await GRAPollingService._update_submission_from_response(
            db=db_session,
            submission=submission,
            gra_response=gra_response,
        )
        
        # Verify signature details were stored
        assert submission.ysdcid == "VSDC-ID-12345"
        assert submission.ysdcrecnum == "VSDC-REC-NUM-67890"
        assert submission.ysdcintdata == "INTEGRATED-DATA-ABC123"
        assert submission.ysdcnrc == "VSDC-NRC-XYZ789"
        
        # Verify submission was persisted
        db_session.refresh(submission)
        assert submission.ysdcid == "VSDC-ID-12345"
        assert submission.ysdcrecnum == "VSDC-REC-NUM-67890"
        assert submission.ysdcintdata == "INTEGRATED-DATA-ABC123"
        assert submission.ysdcnrc == "VSDC-NRC-XYZ789"
    
    @pytest.mark.asyncio
    async def test_update_submission_partial_signature_details(self, db_session, submission_id, business_id):
        """Test storing partial signature details when not all fields are present"""
        # Create a test submission
        submission = Submission(
            id=submission_id,
            business_id=business_id,
            submission_type="INVOICE",
            submission_status=SubmissionStatus.PENDING_GRA.value,
            raw_request={"test": "data"},
        )
        db_session.add(submission)
        db_session.commit()
        
        # GRA response with only some signature details
        gra_response = {
            "status": "SUCCESS",
            "gra_invoice_id": "GRA-INV-001",
            "ysdcid": "VSDC-ID-12345",
            "ysdcrecnum": "VSDC-REC-NUM-67890",
        }
        
        # Update submission
        await GRAPollingService._update_submission_from_response(
            db=db_session,
            submission=submission,
            gra_response=gra_response,
        )
        
        # Verify available signature details were stored
        assert submission.ysdcid == "VSDC-ID-12345"
        assert submission.ysdcrecnum == "VSDC-REC-NUM-67890"
        assert submission.ysdcintdata is None
        assert submission.ysdcnrc is None
    
    @pytest.mark.asyncio
    async def test_poll_for_response_stores_signature_details(self, db_session, submission_id, business_id):
        """Test that polling stores signature details in the database"""
        # Create a test submission
        submission = Submission(
            id=submission_id,
            business_id=business_id,
            submission_type="INVOICE",
            submission_status=SubmissionStatus.PENDING_GRA.value,
            raw_request={"test": "data"},
        )
        db_session.add(submission)
        db_session.commit()
        
        # GRA response with signature details
        gra_response = {
            "status": "SUCCESS",
            "gra_invoice_id": "GRA-INV-001",
            "gra_qr_code": "https://gra.gov.gh/qr/123",
            "gra_receipt_num": "VSDC-REC-001",
            "ysdcid": "VSDC-ID-12345",
            "ysdcrecnum": "VSDC-REC-NUM-67890",
            "ysdcintdata": "INTEGRATED-DATA-ABC123",
            "ysdcnrc": "VSDC-NRC-XYZ789",
        }
        
        # Update submission directly (simulating what polling does)
        await GRAPollingService._update_submission_from_response(
            db=db_session,
            submission=submission,
            gra_response=gra_response,
        )
        
        # Verify submission was updated with signature details
        updated_submission = db_session.query(Submission).filter(
            Submission.id == submission_id
        ).first()
        assert updated_submission.ysdcid == "VSDC-ID-12345"
        assert updated_submission.ysdcrecnum == "VSDC-REC-NUM-67890"
        assert updated_submission.ysdcintdata == "INTEGRATED-DATA-ABC123"
        assert updated_submission.ysdcnrc == "VSDC-NRC-XYZ789"
        assert updated_submission.submission_status == SubmissionStatus.SUCCESS.value

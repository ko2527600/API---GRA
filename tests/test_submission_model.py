"""Comprehensive tests for Submission model"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch


def create_test_db():
    """Create an in-memory test database"""
    from app.models.base import Base
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)


@patch('app.services.api_key_service.pwd_context.hash')
def test_submission_creation(mock_hash):
    """Test creating a submission"""
    from app.models.models import Submission, SubmissionStatus, SubmissionType
    from app.services.business_service import BusinessService
    
    mock_hash.return_value = "hashed_secret"
    engine, SessionLocal = create_test_db()
    db = SessionLocal()
    try:
        business, _ = BusinessService.create_business(
            db,
            business_name="Test Business",
            gra_tin="P00123456789",
            gra_company_name="Test Company",
            gra_security_key="test-key"
        )
        
        submission = Submission(
            business_id=business.id,
            submission_type=SubmissionType.INVOICE.value,
            submission_status=SubmissionStatus.RECEIVED.value,
            raw_request={"test": "data"}
        )
        db.add(submission)
        db.commit()
        
        assert submission.id is not None
        assert submission.business_id == business.id
        assert submission.submission_type == SubmissionType.INVOICE.value
        assert submission.submission_status == SubmissionStatus.RECEIVED.value
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_submission_default_status(mock_hash):
    """Test submission defaults to RECEIVED status"""
    from app.models.models import Submission, SubmissionStatus, SubmissionType
    from app.services.business_service import BusinessService
    
    mock_hash.return_value = "hashed_secret"
    engine, SessionLocal = create_test_db()
    db = SessionLocal()
    try:
        business, _ = BusinessService.create_business(
            db,
            business_name="Test Business",
            gra_tin="P00123456789",
            gra_company_name="Test Company",
            gra_security_key="test-key"
        )
        
        submission = Submission(
            business_id=business.id,
            submission_type=SubmissionType.INVOICE.value,
            raw_request={"test": "data"}
        )
        db.add(submission)
        db.commit()
        
        assert submission.submission_status == SubmissionStatus.RECEIVED.value
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_submission_timestamps(mock_hash):
    """Test submission has created_at and updated_at timestamps"""
    from app.models.models import Submission, SubmissionType
    from app.services.business_service import BusinessService
    
    mock_hash.return_value = "hashed_secret"
    engine, SessionLocal = create_test_db()
    db = SessionLocal()
    try:
        business, _ = BusinessService.create_business(
            db,
            business_name="Test Business",
            gra_tin="P00123456789",
            gra_company_name="Test Company",
            gra_security_key="test-key"
        )
        
        submission = Submission(
            business_id=business.id,
            submission_type=SubmissionType.INVOICE.value,
            raw_request={"test": "data"}
        )
        db.add(submission)
        db.commit()
        
        assert submission.created_at is not None
        assert submission.updated_at is not None
        assert isinstance(submission.created_at, datetime)
        assert isinstance(submission.updated_at, datetime)
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_submission_status_transitions(mock_hash):
    """Test submission can transition through different statuses"""
    from app.models.models import Submission, SubmissionStatus, SubmissionType
    from app.services.business_service import BusinessService
    
    mock_hash.return_value = "hashed_secret"
    engine, SessionLocal = create_test_db()
    db = SessionLocal()
    try:
        business, _ = BusinessService.create_business(
            db,
            business_name="Test Business",
            gra_tin="P00123456789",
            gra_company_name="Test Company",
            gra_security_key="test-key"
        )
        
        submission = Submission(
            business_id=business.id,
            submission_type=SubmissionType.INVOICE.value,
            raw_request={"test": "data"}
        )
        db.add(submission)
        db.commit()
        
        assert submission.submission_status == SubmissionStatus.RECEIVED.value
        submission.submission_status = SubmissionStatus.PROCESSING.value
        db.commit()
        assert submission.submission_status == SubmissionStatus.PROCESSING.value
        submission.submission_status = SubmissionStatus.SUCCESS.value
        db.commit()
        assert submission.submission_status == SubmissionStatus.SUCCESS.value
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_submission_failed_status(mock_hash):
    """Test submission can be marked as failed"""
    from app.models.models import Submission, SubmissionStatus, SubmissionType
    from app.services.business_service import BusinessService
    
    mock_hash.return_value = "hashed_secret"
    engine, SessionLocal = create_test_db()
    db = SessionLocal()
    try:
        business, _ = BusinessService.create_business(
            db,
            business_name="Test Business",
            gra_tin="P00123456789",
            gra_company_name="Test Company",
            gra_security_key="test-key"
        )
        
        submission = Submission(
            business_id=business.id,
            submission_type=SubmissionType.INVOICE.value,
            submission_status=SubmissionStatus.FAILED.value,
            raw_request={"test": "data"},
            error_details={"error": "Test error"}
        )
        db.add(submission)
        db.commit()
        
        assert submission.submission_status == SubmissionStatus.FAILED.value
        assert submission.error_details is not None
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_submission_with_gra_response(mock_hash):
    """Test submission with GRA response data"""
    from app.models.models import Submission, SubmissionStatus, SubmissionType
    from app.services.business_service import BusinessService
    
    mock_hash.return_value = "hashed_secret"
    engine, SessionLocal = create_test_db()
    db = SessionLocal()
    try:
        business, _ = BusinessService.create_business(
            db,
            business_name="Test Business",
            gra_tin="P00123456789",
            gra_company_name="Test Company",
            gra_security_key="test-key"
        )
        
        submission = Submission(
            business_id=business.id,
            submission_type=SubmissionType.INVOICE.value,
            submission_status=SubmissionStatus.SUCCESS.value,
            gra_response_code="00",
            gra_response_message="Success",
            gra_invoice_id="INV-123456",
            gra_qr_code="QR-CODE-DATA",
            gra_receipt_num="RCP-123456",
            raw_request={"test": "data"},
            raw_response={"status": "success"}
        )
        db.add(submission)
        db.commit()
        
        assert submission.gra_response_code == "00"
        assert submission.gra_invoice_id == "INV-123456"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_submission_with_invoice_relationship(mock_hash):
    """Test submission with related invoice"""
    from app.models.models import Submission, Invoice, SubmissionType
    from app.services.business_service import BusinessService
    
    mock_hash.return_value = "hashed_secret"
    engine, SessionLocal = create_test_db()
    db = SessionLocal()
    try:
        business, _ = BusinessService.create_business(
            db,
            business_name="Test Business",
            gra_tin="P00123456789",
            gra_company_name="Test Company",
            gra_security_key="test-key"
        )
        
        submission = Submission(
            business_id=business.id,
            submission_type=SubmissionType.INVOICE.value,
            raw_request={"test": "data"}
        )
        db.add(submission)
        db.commit()
        
        invoice = Invoice(
            submission_id=submission.id,
            business_id=business.id,
            invoice_num="INV-001",
            client_name="Test Client",
            invoice_date="2024-01-01",
            computation_type="INCLUSIVE",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=1
        )
        db.add(invoice)
        db.commit()
        
        assert submission.invoice is not None
        assert submission.invoice.invoice_num == "INV-001"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_submission_with_refund_relationship(mock_hash):
    """Test submission with related refund"""
    from app.models.models import Submission, Refund, SubmissionType
    from app.services.business_service import BusinessService
    
    mock_hash.return_value = "hashed_secret"
    engine, SessionLocal = create_test_db()
    db = SessionLocal()
    try:
        business, _ = BusinessService.create_business(
            db,
            business_name="Test Business",
            gra_tin="P00123456789",
            gra_company_name="Test Company",
            gra_security_key="test-key"
        )
        
        submission = Submission(
            business_id=business.id,
            submission_type=SubmissionType.REFUND.value,
            raw_request={"test": "data"}
        )
        db.add(submission)
        db.commit()
        
        refund = Refund(
            submission_id=submission.id,
            business_id=business.id,
            refund_id="REF-001",
            refund_date="2024-01-01",
            total_vat=50.0,
            total_levy=25.0,
            total_amount=500.0,
            items_count=1
        )
        db.add(refund)
        db.commit()
        
        assert submission.refund is not None
        assert submission.refund.refund_id == "REF-001"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_query_submissions_by_business(mock_hash):
    """Test querying submissions by business"""
    from app.models.models import Submission, SubmissionType
    from app.services.business_service import BusinessService
    
    mock_hash.return_value = "hashed_secret"
    engine, SessionLocal = create_test_db()
    db = SessionLocal()
    try:
        business1, _ = BusinessService.create_business(
            db,
            business_name="Business 1",
            gra_tin="P00111111111",
            gra_company_name="Company 1",
            gra_security_key="key-1"
        )
        business2, _ = BusinessService.create_business(
            db,
            business_name="Business 2",
            gra_tin="P00222222222",
            gra_company_name="Company 2",
            gra_security_key="key-2"
        )
        
        for i in range(3):
            submission = Submission(
                business_id=business1.id,
                submission_type=SubmissionType.INVOICE.value,
                raw_request={"index": i}
            )
            db.add(submission)
        
        for i in range(2):
            submission = Submission(
                business_id=business2.id,
                submission_type=SubmissionType.REFUND.value,
                raw_request={"index": i}
            )
            db.add(submission)
        
        db.commit()
        
        business1_submissions = db.query(Submission).filter_by(business_id=business1.id).all()
        business2_submissions = db.query(Submission).filter_by(business_id=business2.id).all()
        
        assert len(business1_submissions) == 3
        assert len(business2_submissions) == 2
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_submission_with_complex_json(mock_hash):
    """Test submission with complex JSON request and response"""
    from app.models.models import Submission, SubmissionStatus, SubmissionType
    from app.services.business_service import BusinessService
    
    mock_hash.return_value = "hashed_secret"
    engine, SessionLocal = create_test_db()
    db = SessionLocal()
    try:
        business, _ = BusinessService.create_business(
            db,
            business_name="Test Business",
            gra_tin="P00123456789",
            gra_company_name="Test Company",
            gra_security_key="test-key"
        )
        
        complex_request = {
            "invoice_num": "INV-001",
            "items": [
                {"itmref": "ITEM-001", "quantity": 5},
                {"itmref": "ITEM-002", "quantity": 3}
            ]
        }
        
        submission = Submission(
            business_id=business.id,
            submission_type=SubmissionType.INVOICE.value,
            submission_status=SubmissionStatus.SUCCESS.value,
            raw_request=complex_request,
            raw_response={"status": "success"}
        )
        db.add(submission)
        db.commit()
        
        assert submission.raw_request["invoice_num"] == "INV-001"
        assert len(submission.raw_request["items"]) == 2
    finally:
        db.close()

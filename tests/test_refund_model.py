"""Comprehensive tests for Refund model with line items"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker



def create_test_db():
    """Create an in-memory test database"""
    from app.models.base import Base
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)


def test_refund_creation():
    """Test creating a refund"""
    from app.models.models import Refund, Submission, SubmissionType
    from app.services.business_service import BusinessService
    
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
            refund_date="2026-02-10",
            total_vat=50.0,
            total_levy=25.0,
            total_amount=500.0,
            items_count=1
        )
        db.add(refund)
        db.commit()
        
        assert refund.id is not None
        assert refund.refund_id == "REF-001"
        assert refund.refund_date == "2026-02-10"
        assert refund.total_vat == 50.0
        assert refund.total_levy == 25.0
        assert refund.total_amount == 500.0
    finally:
        db.close()


def test_refund_with_original_invoice_reference():
    """Test refund with reference to original invoice"""
    from app.models.models import Refund, Invoice, Submission, SubmissionType
    from app.services.business_service import BusinessService
    
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
        
        # Create original invoice
        invoice_submission = Submission(
            business_id=business.id,
            submission_type=SubmissionType.INVOICE.value,
            raw_request={"test": "data"}
        )
        db.add(invoice_submission)
        db.commit()
        
        invoice = Invoice(
            submission_id=invoice_submission.id,
            business_id=business.id,
            invoice_num="INV-001",
            client_name="Test Client",
            invoice_date="2026-02-09",
            computation_type="INCLUSIVE",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=1
        )
        db.add(invoice)
        db.commit()
        
        # Create refund referencing invoice
        refund_submission = Submission(
            business_id=business.id,
            submission_type=SubmissionType.REFUND.value,
            raw_request={"test": "data"}
        )
        db.add(refund_submission)
        db.commit()
        
        refund = Refund(
            submission_id=refund_submission.id,
            business_id=business.id,
            refund_id="REF-001",
            original_invoice_id=invoice.id,
            refund_date="2026-02-10",
            total_vat=50.0,
            total_levy=25.0,
            total_amount=500.0,
            items_count=1
        )
        db.add(refund)
        db.commit()
        
        assert refund.original_invoice_id == invoice.id
        assert refund.refund_id == "REF-001"
    finally:
        db.close()


def test_refund_with_line_items():
    """Test refund with multiple line items"""
    from app.models.models import Refund, RefundItem, Submission, SubmissionType
    from app.services.business_service import BusinessService
    
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
            refund_id="REF-002",
            refund_date="2026-02-10",
            total_vat=50.0,
            total_levy=25.0,
            total_amount=500.0,
            items_count=2
        )
        db.add(refund)
        db.commit()
        
        item1 = RefundItem(
            refund_id=refund.id,
            itmref="PROD001",
            itmdes="Product 1",
            quantity=5.0,
            unityprice=50.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=1.25,
            levy_amount_b=1.25,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            item_total=250.0
        )
        
        item2 = RefundItem(
            refund_id=refund.id,
            itmref="PROD002",
            itmdes="Product 2",
            quantity=2.5,
            unityprice=50.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=1.25,
            levy_amount_b=1.25,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            item_total=250.0
        )
        
        db.add(item1)
        db.add(item2)
        db.commit()
        
        assert len(refund.items) == 2
        assert refund.items[0].itmref == "PROD001"
        assert refund.items[1].itmref == "PROD002"
        assert refund.items_count == 2
    finally:
        db.close()


def test_refund_item_creation():
    """Test creating a refund item"""
    from app.models.models import Refund, RefundItem, Submission, SubmissionType
    from app.services.business_service import BusinessService
    
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
            refund_id="REF-003",
            refund_date="2026-02-10",
            total_vat=50.0,
            total_levy=25.0,
            total_amount=500.0,
            items_count=1
        )
        db.add(refund)
        db.commit()
        
        item = RefundItem(
            refund_id=refund.id,
            itmref="PROD001",
            itmdes="Product Description",
            quantity=5.0,
            unityprice=50.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=1.25,
            levy_amount_b=1.25,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            item_total=250.0
        )
        db.add(item)
        db.commit()
        
        assert item.id is not None
        assert item.itmref == "PROD001"
        assert item.quantity == 5.0
        assert item.unityprice == 50.0
        assert item.taxcode == "B"
        assert item.taxrate == 15.0
    finally:
        db.close()


def test_refund_item_with_all_levies():
    """Test refund item with all levy amounts"""
    from app.models.models import Refund, RefundItem, Submission, SubmissionType
    from app.services.business_service import BusinessService
    
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
            refund_id="REF-004",
            refund_date="2026-02-10",
            total_vat=50.0,
            total_levy=25.0,
            total_amount=500.0,
            items_count=1
        )
        db.add(refund)
        db.commit()
        
        item = RefundItem(
            refund_id=refund.id,
            itmref="PROD001",
            itmdes="Product Description",
            quantity=5.0,
            unityprice=50.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=1.25,
            levy_amount_b=1.25,
            levy_amount_c=0.5,
            levy_amount_d=2.5,
            item_total=250.0
        )
        db.add(item)
        db.commit()
        
        assert item.levy_amount_a == 1.25
        assert item.levy_amount_b == 1.25
        assert item.levy_amount_c == 0.5
        assert item.levy_amount_d == 2.5
    finally:
        db.close()


def test_refund_item_different_tax_codes():
    """Test refund items with different tax codes"""
    from app.models.models import Refund, RefundItem, Submission, SubmissionType
    from app.services.business_service import BusinessService
    
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
            refund_id="REF-005",
            refund_date="2026-02-10",
            total_vat=50.0,
            total_levy=25.0,
            total_amount=500.0,
            items_count=3
        )
        db.add(refund)
        db.commit()
        
        # Tax code A (Exempted)
        item_a = RefundItem(
            refund_id=refund.id,
            itmref="PROD_A",
            itmdes="Exempted Product",
            quantity=2.5,
            unityprice=50.0,
            taxcode="A",
            taxrate=0.0,
            levy_amount_a=0.0,
            levy_amount_b=0.0,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            item_total=125.0
        )
        
        # Tax code B (Taxable)
        item_b = RefundItem(
            refund_id=refund.id,
            itmref="PROD_B",
            itmdes="Taxable Product",
            quantity=2.5,
            unityprice=50.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=1.25,
            levy_amount_b=1.25,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            item_total=125.0
        )
        
        # Tax code E (Non-VAT)
        item_e = RefundItem(
            refund_id=refund.id,
            itmref="PROD_E",
            itmdes="Non-VAT Product",
            quantity=2.5,
            unityprice=50.0,
            taxcode="E",
            taxrate=3.0,
            levy_amount_a=0.0,
            levy_amount_b=0.0,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            item_total=125.0
        )
        
        db.add(item_a)
        db.add(item_b)
        db.add(item_e)
        db.commit()
        
        assert len(refund.items) == 3
        assert refund.items[0].taxcode == "A"
        assert refund.items[1].taxcode == "B"
        assert refund.items[2].taxcode == "E"
    finally:
        db.close()


def test_refund_timestamps():
    """Test refund has created_at and updated_at timestamps"""
    from app.models.models import Refund, Submission, SubmissionType
    from app.services.business_service import BusinessService
    
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
            refund_id="REF-006",
            refund_date="2026-02-10",
            total_vat=50.0,
            total_levy=25.0,
            total_amount=500.0,
            items_count=1
        )
        db.add(refund)
        db.commit()
        
        assert refund.created_at is not None
        assert refund.updated_at is not None
        assert isinstance(refund.created_at, datetime)
        assert isinstance(refund.updated_at, datetime)
    finally:
        db.close()


def test_refund_cascade_delete_items():
    """Test that deleting refund cascades to delete items"""
    from app.models.models import Refund, RefundItem, Submission, SubmissionType
    from app.services.business_service import BusinessService
    
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
            refund_id="REF-007",
            refund_date="2026-02-10",
            total_vat=50.0,
            total_levy=25.0,
            total_amount=500.0,
            items_count=2
        )
        db.add(refund)
        db.commit()
        
        item1 = RefundItem(
            refund_id=refund.id,
            itmref="PROD001",
            itmdes="Product 1",
            quantity=2.5,
            unityprice=50.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=1.25,
            levy_amount_b=1.25,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            item_total=125.0
        )
        
        item2 = RefundItem(
            refund_id=refund.id,
            itmref="PROD002",
            itmdes="Product 2",
            quantity=2.5,
            unityprice=50.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=1.25,
            levy_amount_b=1.25,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            item_total=125.0
        )
        
        db.add(item1)
        db.add(item2)
        db.commit()
        
        refund_id = refund.id
        db.delete(refund)
        db.commit()
        
        # Verify refund is deleted
        deleted_refund = db.query(Refund).filter_by(id=refund_id).first()
        assert deleted_refund is None
        
        # Verify items are also deleted
        items = db.query(RefundItem).filter_by(refund_id=refund_id).all()
        assert len(items) == 0
    finally:
        db.close()


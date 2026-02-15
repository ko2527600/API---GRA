"""Comprehensive tests for Invoice model with line items"""
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
def test_invoice_creation(mock_hash):
    """Test creating an invoice"""
    from app.models.models import Invoice, Submission, SubmissionType
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
            invoice_date="2026-02-10",
            computation_type="INCLUSIVE",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=1
        )
        db.add(invoice)
        db.commit()
        
        assert invoice.id is not None
        assert invoice.invoice_num == "INV-001"
        assert invoice.client_name == "Test Client"
        assert invoice.total_vat == 100.0
        assert invoice.total_levy == 50.0
        assert invoice.total_amount == 1000.0
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_invoice_with_client_tin(mock_hash):
    """Test invoice with client TIN"""
    from app.models.models import Invoice, Submission, SubmissionType
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
            invoice_num="INV-002",
            client_name="Test Client",
            client_tin="C0022825405",
            invoice_date="2026-02-10",
            computation_type="EXCLUSIVE",
            total_vat=150.0,
            total_levy=60.0,
            total_amount=1200.0,
            items_count=2
        )
        db.add(invoice)
        db.commit()
        
        assert invoice.client_tin == "C0022825405"
        assert invoice.computation_type == "EXCLUSIVE"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_invoice_with_line_items(mock_hash):
    """Test invoice with multiple line items"""
    from app.models.models import Invoice, InvoiceItem, Submission, SubmissionType
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
            invoice_num="INV-003",
            client_name="Test Client",
            invoice_date="2026-02-10",
            computation_type="INCLUSIVE",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=2
        )
        db.add(invoice)
        db.commit()
        
        item1 = InvoiceItem(
            invoice_id=invoice.id,
            itmref="PROD001",
            itmdes="Product 1",
            quantity=10.0,
            unityprice=100.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=2.5,
            levy_amount_b=2.5,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            itmdiscount=0.0,
            item_total=500.0,
            item_category="GOODS"
        )
        
        item2 = InvoiceItem(
            invoice_id=invoice.id,
            itmref="PROD002",
            itmdes="Product 2",
            quantity=5.0,
            unityprice=100.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=2.5,
            levy_amount_b=2.5,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            itmdiscount=0.0,
            item_total=500.0,
            item_category="GOODS"
        )
        
        db.add(item1)
        db.add(item2)
        db.commit()
        
        assert len(invoice.items) == 2
        assert invoice.items[0].itmref == "PROD001"
        assert invoice.items[1].itmref == "PROD002"
        assert invoice.items_count == 2
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_invoice_item_creation(mock_hash):
    """Test creating an invoice item"""
    from app.models.models import Invoice, InvoiceItem, Submission, SubmissionType
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
            invoice_num="INV-004",
            client_name="Test Client",
            invoice_date="2026-02-10",
            computation_type="INCLUSIVE",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=1
        )
        db.add(invoice)
        db.commit()
        
        item = InvoiceItem(
            invoice_id=invoice.id,
            itmref="PROD001",
            itmdes="Product Description",
            quantity=10.0,
            unityprice=100.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=2.5,
            levy_amount_b=2.5,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            itmdiscount=0.0,
            item_total=1000.0,
            item_category="GOODS"
        )
        db.add(item)
        db.commit()
        
        assert item.id is not None
        assert item.itmref == "PROD001"
        assert item.quantity == 10.0
        assert item.unityprice == 100.0
        assert item.taxcode == "B"
        assert item.taxrate == 15.0
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_invoice_item_with_all_levies(mock_hash):
    """Test invoice item with all levy amounts"""
    from app.models.models import Invoice, InvoiceItem, Submission, SubmissionType
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
            invoice_num="INV-005",
            client_name="Test Client",
            invoice_date="2026-02-10",
            computation_type="INCLUSIVE",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=1
        )
        db.add(invoice)
        db.commit()
        
        item = InvoiceItem(
            invoice_id=invoice.id,
            itmref="PROD001",
            itmdes="Product Description",
            quantity=10.0,
            unityprice=100.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=2.5,
            levy_amount_b=2.5,
            levy_amount_c=1.0,
            levy_amount_d=5.0,
            itmdiscount=0.0,
            item_total=1000.0,
            item_category="GOODS"
        )
        db.add(item)
        db.commit()
        
        assert item.levy_amount_a == 2.5
        assert item.levy_amount_b == 2.5
        assert item.levy_amount_c == 1.0
        assert item.levy_amount_d == 5.0
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_invoice_item_with_discount(mock_hash):
    """Test invoice item with discount"""
    from app.models.models import Invoice, InvoiceItem, Submission, SubmissionType
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
            invoice_num="INV-006",
            client_name="Test Client",
            invoice_date="2026-02-10",
            computation_type="INCLUSIVE",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=1
        )
        db.add(invoice)
        db.commit()
        
        item = InvoiceItem(
            invoice_id=invoice.id,
            itmref="PROD001",
            itmdes="Product Description",
            quantity=10.0,
            unityprice=100.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=2.5,
            levy_amount_b=2.5,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            itmdiscount=50.0,
            item_total=950.0,
            item_category="GOODS"
        )
        db.add(item)
        db.commit()
        
        assert item.itmdiscount == 50.0
        assert item.item_total == 950.0
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_invoice_item_different_tax_codes(mock_hash):
    """Test invoice items with different tax codes"""
    from app.models.models import Invoice, InvoiceItem, Submission, SubmissionType
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
            invoice_num="INV-007",
            client_name="Test Client",
            invoice_date="2026-02-10",
            computation_type="INCLUSIVE",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=3
        )
        db.add(invoice)
        db.commit()
        
        # Tax code A (Exempted)
        item_a = InvoiceItem(
            invoice_id=invoice.id,
            itmref="PROD_A",
            itmdes="Exempted Product",
            quantity=5.0,
            unityprice=100.0,
            taxcode="A",
            taxrate=0.0,
            levy_amount_a=0.0,
            levy_amount_b=0.0,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            itmdiscount=0.0,
            item_total=500.0,
            item_category="GOODS"
        )
        
        # Tax code B (Taxable)
        item_b = InvoiceItem(
            invoice_id=invoice.id,
            itmref="PROD_B",
            itmdes="Taxable Product",
            quantity=5.0,
            unityprice=100.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=2.5,
            levy_amount_b=2.5,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            itmdiscount=0.0,
            item_total=500.0,
            item_category="GOODS"
        )
        
        # Tax code E (Non-VAT)
        item_e = InvoiceItem(
            invoice_id=invoice.id,
            itmref="PROD_E",
            itmdes="Non-VAT Product",
            quantity=5.0,
            unityprice=100.0,
            taxcode="E",
            taxrate=3.0,
            levy_amount_a=0.0,
            levy_amount_b=0.0,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            itmdiscount=0.0,
            item_total=500.0,
            item_category="GOODS"
        )
        
        db.add(item_a)
        db.add(item_b)
        db.add(item_e)
        db.commit()
        
        assert len(invoice.items) == 3
        assert invoice.items[0].taxcode == "A"
        assert invoice.items[1].taxcode == "B"
        assert invoice.items[2].taxcode == "E"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_invoice_timestamps(mock_hash):
    """Test invoice has created_at and updated_at timestamps"""
    from app.models.models import Invoice, Submission, SubmissionType
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
            invoice_num="INV-008",
            client_name="Test Client",
            invoice_date="2026-02-10",
            computation_type="INCLUSIVE",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=1
        )
        db.add(invoice)
        db.commit()
        
        assert invoice.created_at is not None
        assert invoice.updated_at is not None
        assert isinstance(invoice.created_at, datetime)
        assert isinstance(invoice.updated_at, datetime)
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_invoice_unique_constraint(mock_hash):
    """Test invoice number is unique per business"""
    from app.models.models import Invoice, Submission, SubmissionType
    from app.services.business_service import BusinessService
    from sqlalchemy.exc import IntegrityError
    
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
        
        submission1 = Submission(
            business_id=business.id,
            submission_type=SubmissionType.INVOICE.value,
            raw_request={"test": "data"}
        )
        db.add(submission1)
        db.commit()
        
        submission2 = Submission(
            business_id=business.id,
            submission_type=SubmissionType.INVOICE.value,
            raw_request={"test": "data"}
        )
        db.add(submission2)
        db.commit()
        
        invoice1 = Invoice(
            submission_id=submission1.id,
            business_id=business.id,
            invoice_num="INV-SAME",
            client_name="Test Client",
            invoice_date="2026-02-10",
            computation_type="INCLUSIVE",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=1
        )
        db.add(invoice1)
        db.commit()
        
        invoice2 = Invoice(
            submission_id=submission2.id,
            business_id=business.id,
            invoice_num="INV-SAME",
            client_name="Test Client",
            invoice_date="2026-02-10",
            computation_type="INCLUSIVE",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=1
        )
        db.add(invoice2)
        
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_invoice_cascade_delete_items(mock_hash):
    """Test that deleting invoice cascades to delete items"""
    from app.models.models import Invoice, InvoiceItem, Submission, SubmissionType
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
            invoice_num="INV-009",
            client_name="Test Client",
            invoice_date="2026-02-10",
            computation_type="INCLUSIVE",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=2
        )
        db.add(invoice)
        db.commit()
        
        item1 = InvoiceItem(
            invoice_id=invoice.id,
            itmref="PROD001",
            itmdes="Product 1",
            quantity=10.0,
            unityprice=100.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=2.5,
            levy_amount_b=2.5,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            itmdiscount=0.0,
            item_total=500.0,
            item_category="GOODS"
        )
        
        item2 = InvoiceItem(
            invoice_id=invoice.id,
            itmref="PROD002",
            itmdes="Product 2",
            quantity=5.0,
            unityprice=100.0,
            taxcode="B",
            taxrate=15.0,
            levy_amount_a=2.5,
            levy_amount_b=2.5,
            levy_amount_c=0.0,
            levy_amount_d=0.0,
            itmdiscount=0.0,
            item_total=500.0,
            item_category="GOODS"
        )
        
        db.add(item1)
        db.add(item2)
        db.commit()
        
        invoice_id = invoice.id
        db.delete(invoice)
        db.commit()
        
        # Verify invoice is deleted
        deleted_invoice = db.query(Invoice).filter_by(id=invoice_id).first()
        assert deleted_invoice is None
        
        # Verify items are also deleted
        items = db.query(InvoiceItem).filter_by(invoice_id=invoice_id).all()
        assert len(items) == 0
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_query_invoices_by_business(mock_hash):
    """Test querying invoices by business"""
    from app.models.models import Invoice, Submission, SubmissionType
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
            db.commit()
            
            invoice = Invoice(
                submission_id=submission.id,
                business_id=business1.id,
                invoice_num=f"INV-B1-{i}",
                client_name="Test Client",
                invoice_date="2026-02-10",
                computation_type="INCLUSIVE",
                total_vat=100.0,
                total_levy=50.0,
                total_amount=1000.0,
                items_count=1
            )
            db.add(invoice)
        
        for i in range(2):
            submission = Submission(
                business_id=business2.id,
                submission_type=SubmissionType.INVOICE.value,
                raw_request={"index": i}
            )
            db.add(submission)
            db.commit()
            
            invoice = Invoice(
                submission_id=submission.id,
                business_id=business2.id,
                invoice_num=f"INV-B2-{i}",
                client_name="Test Client",
                invoice_date="2026-02-10",
                computation_type="INCLUSIVE",
                total_vat=100.0,
                total_levy=50.0,
                total_amount=1000.0,
                items_count=1
            )
            db.add(invoice)
        
        db.commit()
        
        business1_invoices = db.query(Invoice).filter_by(business_id=business1.id).all()
        business2_invoices = db.query(Invoice).filter_by(business_id=business2.id).all()
        
        assert len(business1_invoices) == 3
        assert len(business2_invoices) == 2
    finally:
        db.close()

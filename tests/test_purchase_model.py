"""Comprehensive tests for Purchase model with line items"""
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
def test_purchase_creation(mock_hash):
    """Test creating a purchase"""
    from app.models.models import Purchase, Submission, SubmissionType
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
            submission_type=SubmissionType.PURCHASE.value,
            raw_request={"test": "data"}
        )
        db.add(submission)
        db.commit()
        
        purchase = Purchase(
            submission_id=submission.id,
            business_id=business.id,
            purchase_num="PUR-001",
            supplier_name="Test Supplier",
            purchase_date="2026-02-10",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=1
        )
        db.add(purchase)
        db.commit()
        
        assert purchase.id is not None
        assert purchase.purchase_num == "PUR-001"
        assert purchase.supplier_name == "Test Supplier"
        assert purchase.total_vat == 100.0
        assert purchase.total_levy == 50.0
        assert purchase.total_amount == 1000.0
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_purchase_with_supplier_tin(mock_hash):
    """Test purchase with supplier TIN"""
    from app.models.models import Purchase, Submission, SubmissionType
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
            submission_type=SubmissionType.PURCHASE.value,
            raw_request={"test": "data"}
        )
        db.add(submission)
        db.commit()
        
        purchase = Purchase(
            submission_id=submission.id,
            business_id=business.id,
            purchase_num="PUR-002",
            supplier_name="Test Supplier",
            supplier_tin="P00987654321",
            purchase_date="2026-02-10",
            total_vat=150.0,
            total_levy=60.0,
            total_amount=1200.0,
            items_count=2
        )
        db.add(purchase)
        db.commit()
        
        assert purchase.supplier_tin == "P00987654321"
        assert purchase.purchase_num == "PUR-002"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_purchase_with_line_items(mock_hash):
    """Test purchase with multiple line items"""
    from app.models.models import Purchase, PurchaseItem, Submission, SubmissionType
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
            submission_type=SubmissionType.PURCHASE.value,
            raw_request={"test": "data"}
        )
        db.add(submission)
        db.commit()
        
        purchase = Purchase(
            submission_id=submission.id,
            business_id=business.id,
            purchase_num="PUR-003",
            supplier_name="Test Supplier",
            purchase_date="2026-02-10",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=2
        )
        db.add(purchase)
        db.commit()
        
        item1 = PurchaseItem(
            purchase_id=purchase.id,
            itmref="PROD001",
            itmdes="Product 1",
            quantity=10.0,
            unityprice=100.0,
            taxcode="B",
            taxrate=15.0,
            item_total=500.0
        )
        
        item2 = PurchaseItem(
            purchase_id=purchase.id,
            itmref="PROD002",
            itmdes="Product 2",
            quantity=5.0,
            unityprice=100.0,
            taxcode="B",
            taxrate=15.0,
            item_total=500.0
        )
        
        db.add(item1)
        db.add(item2)
        db.commit()
        
        assert len(purchase.items) == 2
        assert purchase.items[0].itmref == "PROD001"
        assert purchase.items[1].itmref == "PROD002"
        assert purchase.items_count == 2
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_purchase_item_creation(mock_hash):
    """Test creating a purchase item"""
    from app.models.models import Purchase, PurchaseItem, Submission, SubmissionType
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
            submission_type=SubmissionType.PURCHASE.value,
            raw_request={"test": "data"}
        )
        db.add(submission)
        db.commit()
        
        purchase = Purchase(
            submission_id=submission.id,
            business_id=business.id,
            purchase_num="PUR-004",
            supplier_name="Test Supplier",
            purchase_date="2026-02-10",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=1
        )
        db.add(purchase)
        db.commit()
        
        item = PurchaseItem(
            purchase_id=purchase.id,
            itmref="PROD001",
            itmdes="Product Description",
            quantity=10.0,
            unityprice=100.0,
            taxcode="B",
            taxrate=15.0,
            item_total=1000.0
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
def test_purchase_item_different_tax_codes(mock_hash):
    """Test purchase items with different tax codes"""
    from app.models.models import Purchase, PurchaseItem, Submission, SubmissionType
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
            submission_type=SubmissionType.PURCHASE.value,
            raw_request={"test": "data"}
        )
        db.add(submission)
        db.commit()
        
        purchase = Purchase(
            submission_id=submission.id,
            business_id=business.id,
            purchase_num="PUR-005",
            supplier_name="Test Supplier",
            purchase_date="2026-02-10",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=3
        )
        db.add(purchase)
        db.commit()
        
        # Tax code A (Exempted)
        item_a = PurchaseItem(
            purchase_id=purchase.id,
            itmref="PROD_A",
            itmdes="Exempted Product",
            quantity=5.0,
            unityprice=100.0,
            taxcode="A",
            taxrate=0.0,
            item_total=500.0
        )
        
        # Tax code B (Taxable)
        item_b = PurchaseItem(
            purchase_id=purchase.id,
            itmref="PROD_B",
            itmdes="Taxable Product",
            quantity=5.0,
            unityprice=100.0,
            taxcode="B",
            taxrate=15.0,
            item_total=500.0
        )
        
        # Tax code E (Non-VAT)
        item_e = PurchaseItem(
            purchase_id=purchase.id,
            itmref="PROD_E",
            itmdes="Non-VAT Product",
            quantity=5.0,
            unityprice=100.0,
            taxcode="E",
            taxrate=3.0,
            item_total=500.0
        )
        
        db.add(item_a)
        db.add(item_b)
        db.add(item_e)
        db.commit()
        
        assert len(purchase.items) == 3
        assert purchase.items[0].taxcode == "A"
        assert purchase.items[1].taxcode == "B"
        assert purchase.items[2].taxcode == "E"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_purchase_timestamps(mock_hash):
    """Test purchase has created_at and updated_at timestamps"""
    from app.models.models import Purchase, Submission, SubmissionType
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
            submission_type=SubmissionType.PURCHASE.value,
            raw_request={"test": "data"}
        )
        db.add(submission)
        db.commit()
        
        purchase = Purchase(
            submission_id=submission.id,
            business_id=business.id,
            purchase_num="PUR-006",
            supplier_name="Test Supplier",
            purchase_date="2026-02-10",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=1
        )
        db.add(purchase)
        db.commit()
        
        assert purchase.created_at is not None
        assert purchase.updated_at is not None
        assert isinstance(purchase.created_at, datetime)
        assert isinstance(purchase.updated_at, datetime)
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_purchase_unique_constraint(mock_hash):
    """Test purchase number is unique per business"""
    from app.models.models import Purchase, Submission, SubmissionType
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
            submission_type=SubmissionType.PURCHASE.value,
            raw_request={"test": "data"}
        )
        db.add(submission1)
        db.commit()
        
        submission2 = Submission(
            business_id=business.id,
            submission_type=SubmissionType.PURCHASE.value,
            raw_request={"test": "data"}
        )
        db.add(submission2)
        db.commit()
        
        purchase1 = Purchase(
            submission_id=submission1.id,
            business_id=business.id,
            purchase_num="PUR-SAME",
            supplier_name="Test Supplier",
            purchase_date="2026-02-10",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=1
        )
        db.add(purchase1)
        db.commit()
        
        purchase2 = Purchase(
            submission_id=submission2.id,
            business_id=business.id,
            purchase_num="PUR-SAME",
            supplier_name="Test Supplier",
            purchase_date="2026-02-10",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=1
        )
        db.add(purchase2)
        
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_purchase_cascade_delete_items(mock_hash):
    """Test that deleting purchase cascades to delete items"""
    from app.models.models import Purchase, PurchaseItem, Submission, SubmissionType
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
            submission_type=SubmissionType.PURCHASE.value,
            raw_request={"test": "data"}
        )
        db.add(submission)
        db.commit()
        
        purchase = Purchase(
            submission_id=submission.id,
            business_id=business.id,
            purchase_num="PUR-007",
            supplier_name="Test Supplier",
            purchase_date="2026-02-10",
            total_vat=100.0,
            total_levy=50.0,
            total_amount=1000.0,
            items_count=2
        )
        db.add(purchase)
        db.commit()
        
        item1 = PurchaseItem(
            purchase_id=purchase.id,
            itmref="PROD001",
            itmdes="Product 1",
            quantity=10.0,
            unityprice=100.0,
            taxcode="B",
            taxrate=15.0,
            item_total=500.0
        )
        
        item2 = PurchaseItem(
            purchase_id=purchase.id,
            itmref="PROD002",
            itmdes="Product 2",
            quantity=5.0,
            unityprice=100.0,
            taxcode="B",
            taxrate=15.0,
            item_total=500.0
        )
        
        db.add(item1)
        db.add(item2)
        db.commit()
        
        purchase_id = purchase.id
        db.delete(purchase)
        db.commit()
        
        # Verify purchase is deleted
        deleted_purchase = db.query(Purchase).filter_by(id=purchase_id).first()
        assert deleted_purchase is None
        
        # Verify items are also deleted
        items = db.query(PurchaseItem).filter_by(purchase_id=purchase_id).all()
        assert len(items) == 0
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_query_purchases_by_business(mock_hash):
    """Test querying purchases by business"""
    from app.models.models import Purchase, Submission, SubmissionType
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
                submission_type=SubmissionType.PURCHASE.value,
                raw_request={"index": i}
            )
            db.add(submission)
            db.commit()
            
            purchase = Purchase(
                submission_id=submission.id,
                business_id=business1.id,
                purchase_num=f"PUR-B1-{i}",
                supplier_name="Test Supplier",
                purchase_date="2026-02-10",
                total_vat=100.0,
                total_levy=50.0,
                total_amount=1000.0,
                items_count=1
            )
            db.add(purchase)
        
        for i in range(2):
            submission = Submission(
                business_id=business2.id,
                submission_type=SubmissionType.PURCHASE.value,
                raw_request={"index": i}
            )
            db.add(submission)
            db.commit()
            
            purchase = Purchase(
                submission_id=submission.id,
                business_id=business2.id,
                purchase_num=f"PUR-B2-{i}",
                supplier_name="Test Supplier",
                purchase_date="2026-02-10",
                total_vat=100.0,
                total_levy=50.0,
                total_amount=1000.0,
                items_count=1
            )
            db.add(purchase)
        
        db.commit()
        
        business1_purchases = db.query(Purchase).filter_by(business_id=business1.id).all()
        business2_purchases = db.query(Purchase).filter_by(business_id=business2.id).all()
        
        assert len(business1_purchases) == 3
        assert len(business2_purchases) == 2
    finally:
        db.close()

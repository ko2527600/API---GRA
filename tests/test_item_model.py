"""Comprehensive tests for Item registration model"""
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


def test_item_creation():
    """Test creating an item"""
    from app.models.models import Item
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
        
        item = Item(
            business_id=business.id,
            item_ref="PROD001",
            item_name="Product 1",
            item_category="GOODS",
            tax_code="B",
            gra_registration_status="PENDING"
        )
        db.add(item)
        db.commit()
        
        assert item.id is not None
        assert item.item_ref == "PROD001"
        assert item.item_name == "Product 1"
        assert item.item_category == "GOODS"
        assert item.tax_code == "B"
        assert item.gra_registration_status == "PENDING"
    finally:
        db.close()


def test_item_with_all_tax_codes():
    """Test items with all valid tax codes"""
    from app.models.models import Item
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
        
        tax_codes = ["A", "B", "C", "D", "E"]
        for i, tax_code in enumerate(tax_codes):
            item = Item(
                business_id=business.id,
                item_ref=f"PROD_{tax_code}_{i}",
                item_name=f"Product {tax_code}",
                item_category="GOODS",
                tax_code=tax_code,
                gra_registration_status="PENDING"
            )
            db.add(item)
        
        db.commit()
        
        items = db.query(Item).filter_by(business_id=business.id).all()
        assert len(items) == 5
        
        for i, tax_code in enumerate(tax_codes):
            assert items[i].tax_code == tax_code
    finally:
        db.close()


def test_item_unique_constraint_per_business():
    """Test item_ref is unique per business"""
    from app.models.models import Item
    from app.services.business_service import BusinessService
    from sqlalchemy.exc import IntegrityError
    
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
        
        item1 = Item(
            business_id=business.id,
            item_ref="PROD_SAME",
            item_name="Product 1",
            item_category="GOODS",
            tax_code="B",
            gra_registration_status="PENDING"
        )
        db.add(item1)
        db.commit()
        
        item2 = Item(
            business_id=business.id,
            item_ref="PROD_SAME",
            item_name="Product 2",
            item_category="GOODS",
            tax_code="A",
            gra_registration_status="PENDING"
        )
        db.add(item2)
        
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.close()


def test_item_same_ref_different_businesses():
    """Test same item_ref can exist in different businesses"""
    from app.models.models import Item
    from app.services.business_service import BusinessService
    
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
        
        item1 = Item(
            business_id=business1.id,
            item_ref="PROD001",
            item_name="Product 1",
            item_category="GOODS",
            tax_code="B",
            gra_registration_status="PENDING"
        )
        
        item2 = Item(
            business_id=business2.id,
            item_ref="PROD001",
            item_name="Product 1",
            item_category="GOODS",
            tax_code="A",
            gra_registration_status="PENDING"
        )
        
        db.add(item1)
        db.add(item2)
        db.commit()
        
        assert item1.item_ref == item2.item_ref
        assert item1.business_id != item2.business_id
    finally:
        db.close()


def test_item_with_gra_item_id():
    """Test item with GRA registration ID"""
    from app.models.models import Item
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
        
        item = Item(
            business_id=business.id,
            item_ref="PROD001",
            item_name="Product 1",
            item_category="GOODS",
            tax_code="B",
            gra_registration_status="SUCCESS",
            gra_item_id="GRA-ITEM-12345"
        )
        db.add(item)
        db.commit()
        
        assert item.gra_registration_status == "SUCCESS"
        assert item.gra_item_id == "GRA-ITEM-12345"
    finally:
        db.close()


def test_item_registration_status_values():
    """Test different item registration status values"""
    from app.models.models import Item
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
        
        statuses = ["PENDING", "PROCESSING", "SUCCESS", "FAILED"]
        for i, status in enumerate(statuses):
            item = Item(
                business_id=business.id,
                item_ref=f"PROD_{status}_{i}",
                item_name=f"Product {status}",
                item_category="GOODS",
                tax_code="B",
                gra_registration_status=status
            )
            db.add(item)
        
        db.commit()
        
        items = db.query(Item).filter_by(business_id=business.id).all()
        assert len(items) == 4
        
        for i, status in enumerate(statuses):
            assert items[i].gra_registration_status == status
    finally:
        db.close()


def test_item_without_category():
    """Test item creation without category (optional field)"""
    from app.models.models import Item
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
        
        item = Item(
            business_id=business.id,
            item_ref="PROD001",
            item_name="Product 1",
            tax_code="B",
            gra_registration_status="PENDING"
        )
        db.add(item)
        db.commit()
        
        assert item.item_category is None
        assert item.item_name == "Product 1"
    finally:
        db.close()


def test_item_timestamps():
    """Test item has created_at and updated_at timestamps"""
    from app.models.models import Item
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
        
        item = Item(
            business_id=business.id,
            item_ref="PROD001",
            item_name="Product 1",
            item_category="GOODS",
            tax_code="B",
            gra_registration_status="PENDING"
        )
        db.add(item)
        db.commit()
        
        assert item.created_at is not None
        assert item.updated_at is not None
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)
    finally:
        db.close()


def test_query_items_by_business():
    """Test querying items by business"""
    from app.models.models import Item
    from app.services.business_service import BusinessService
    
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
            item = Item(
                business_id=business1.id,
                item_ref=f"PROD_B1_{i}",
                item_name=f"Product B1 {i}",
                item_category="GOODS",
                tax_code="B",
                gra_registration_status="PENDING"
            )
            db.add(item)
        
        for i in range(2):
            item = Item(
                business_id=business2.id,
                item_ref=f"PROD_B2_{i}",
                item_name=f"Product B2 {i}",
                item_category="GOODS",
                tax_code="A",
                gra_registration_status="PENDING"
            )
            db.add(item)
        
        db.commit()
        
        business1_items = db.query(Item).filter_by(business_id=business1.id).all()
        business2_items = db.query(Item).filter_by(business_id=business2.id).all()
        
        assert len(business1_items) == 3
        assert len(business2_items) == 2
    finally:
        db.close()


def test_item_relationship_with_business():
    """Test item relationship with business"""
    from app.models.models import Item
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
        
        item1 = Item(
            business_id=business.id,
            item_ref="PROD001",
            item_name="Product 1",
            item_category="GOODS",
            tax_code="B",
            gra_registration_status="PENDING"
        )
        
        item2 = Item(
            business_id=business.id,
            item_ref="PROD002",
            item_name="Product 2",
            item_category="GOODS",
            tax_code="A",
            gra_registration_status="PENDING"
        )
        
        db.add(item1)
        db.add(item2)
        db.commit()
        
        # Verify relationship
        assert len(business.items) == 2
        assert item1 in business.items
        assert item2 in business.items
    finally:
        db.close()


def test_item_cascade_delete_with_business():
    """Test that deleting business cascades to delete items"""
    from app.models.models import Item
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
        
        item1 = Item(
            business_id=business.id,
            item_ref="PROD001",
            item_name="Product 1",
            item_category="GOODS",
            tax_code="B",
            gra_registration_status="PENDING"
        )
        
        item2 = Item(
            business_id=business.id,
            item_ref="PROD002",
            item_name="Product 2",
            item_category="GOODS",
            tax_code="A",
            gra_registration_status="PENDING"
        )
        
        db.add(item1)
        db.add(item2)
        db.commit()
        
        business_id = business.id
        db.delete(business)
        db.commit()
        
        # Verify business is deleted
        deleted_business = db.query(Item).filter_by(business_id=business_id).all()
        assert len(deleted_business) == 0
    finally:
        db.close()


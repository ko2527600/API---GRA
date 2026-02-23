"""Comprehensive tests for Inventory tracking model"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker



def create_test_db():
    """Create an in-memory test database"""
    from app.models.base import Base
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)


def test_inventory_creation():
    """Test creating an inventory record"""
    from app.models.models import Inventory, Item
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
            gra_registration_status="SUCCESS"
        )
        db.add(item)
        db.commit()
        
        inventory = Inventory(
            business_id=business.id,
            niki_code="BEEHEIN00011",
            item_id=item.id,
            quantity=250.0,
            gra_sync_status="PENDING"
        )
        db.add(inventory)
        db.commit()
        
        assert inventory.id is not None
        assert inventory.niki_code == "BEEHEIN00011"
        assert inventory.quantity == 250.0
        assert inventory.gra_sync_status == "PENDING"
        assert inventory.item_id == item.id
    finally:
        db.close()


def test_inventory_unique_niki_code_per_business():
    """Test niki_code is unique per business"""
    from app.models.models import Inventory, Item
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
            item_ref="PROD001",
            item_name="Product 1",
            item_category="GOODS",
            tax_code="B",
            gra_registration_status="SUCCESS"
        )
        item2 = Item(
            business_id=business.id,
            item_ref="PROD002",
            item_name="Product 2",
            item_category="GOODS",
            tax_code="A",
            gra_registration_status="SUCCESS"
        )
        db.add(item1)
        db.add(item2)
        db.commit()
        
        inventory1 = Inventory(
            business_id=business.id,
            niki_code="BEEHEIN00011",
            item_id=item1.id,
            quantity=250.0,
            gra_sync_status="PENDING"
        )
        db.add(inventory1)
        db.commit()
        
        inventory2 = Inventory(
            business_id=business.id,
            niki_code="BEEHEIN00011",
            item_id=item2.id,
            quantity=100.0,
            gra_sync_status="PENDING"
        )
        db.add(inventory2)
        
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.close()


def test_inventory_same_niki_code_different_businesses():
    """Test same niki_code can exist in different businesses"""
    from app.models.models import Inventory, Item
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
            gra_registration_status="SUCCESS"
        )
        item2 = Item(
            business_id=business2.id,
            item_ref="PROD001",
            item_name="Product 1",
            item_category="GOODS",
            tax_code="B",
            gra_registration_status="SUCCESS"
        )
        db.add(item1)
        db.add(item2)
        db.commit()
        
        inventory1 = Inventory(
            business_id=business1.id,
            niki_code="BEEHEIN00011",
            item_id=item1.id,
            quantity=250.0,
            gra_sync_status="PENDING"
        )
        
        inventory2 = Inventory(
            business_id=business2.id,
            niki_code="BEEHEIN00011",
            item_id=item2.id,
            quantity=100.0,
            gra_sync_status="PENDING"
        )
        
        db.add(inventory1)
        db.add(inventory2)
        db.commit()
        
        assert inventory1.niki_code == inventory2.niki_code
        assert inventory1.business_id != inventory2.business_id
    finally:
        db.close()


def test_inventory_quantity_values():
    """Test inventory with various quantity values"""
    from app.models.models import Inventory, Item
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
        
        quantities = [0.0, 1.0, 100.5, 1000.0, 9999.99]
        for i, qty in enumerate(quantities):
            item = Item(
                business_id=business.id,
                item_ref=f"PROD_{i}",
                item_name=f"Product {i}",
                item_category="GOODS",
                tax_code="B",
                gra_registration_status="SUCCESS"
            )
            db.add(item)
            db.flush()
            
            inventory = Inventory(
                business_id=business.id,
                niki_code=f"NIKI_{i}",
                item_id=item.id,
                quantity=qty,
                gra_sync_status="PENDING"
            )
            db.add(inventory)
        
        db.commit()
        
        inventories = db.query(Inventory).filter_by(business_id=business.id).all()
        assert len(inventories) == 5
        
        for i, qty in enumerate(quantities):
            assert inventories[i].quantity == qty
    finally:
        db.close()


def test_inventory_gra_sync_status_values():
    """Test different GRA sync status values"""
    from app.models.models import Inventory, Item
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
                gra_registration_status="SUCCESS"
            )
            db.add(item)
            db.flush()
            
            inventory = Inventory(
                business_id=business.id,
                niki_code=f"NIKI_{status}_{i}",
                item_id=item.id,
                quantity=100.0,
                gra_sync_status=status
            )
            db.add(inventory)
        
        db.commit()
        
        inventories = db.query(Inventory).filter_by(business_id=business.id).all()
        assert len(inventories) == 4
        
        for i, status in enumerate(statuses):
            assert inventories[i].gra_sync_status == status
    finally:
        db.close()


def test_inventory_last_updated_timestamp():
    """Test inventory last_updated timestamp"""
    from app.models.models import Inventory, Item
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
            gra_registration_status="SUCCESS"
        )
        db.add(item)
        db.commit()
        
        before_time = datetime.utcnow()
        inventory = Inventory(
            business_id=business.id,
            niki_code="BEEHEIN00011",
            item_id=item.id,
            quantity=250.0,
            gra_sync_status="PENDING"
        )
        db.add(inventory)
        db.commit()
        after_time = datetime.utcnow()
        
        assert inventory.last_updated is not None
        assert isinstance(inventory.last_updated, datetime)
        assert before_time <= inventory.last_updated <= after_time
    finally:
        db.close()


def test_inventory_timestamps():
    """Test inventory has created_at and updated_at timestamps"""
    from app.models.models import Inventory, Item
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
            gra_registration_status="SUCCESS"
        )
        db.add(item)
        db.commit()
        
        inventory = Inventory(
            business_id=business.id,
            niki_code="BEEHEIN00011",
            item_id=item.id,
            quantity=250.0,
            gra_sync_status="PENDING"
        )
        db.add(inventory)
        db.commit()
        
        assert inventory.created_at is not None
        assert inventory.updated_at is not None
        assert isinstance(inventory.created_at, datetime)
        assert isinstance(inventory.updated_at, datetime)
    finally:
        db.close()


def test_inventory_relationship_with_item():
    """Test inventory relationship with item"""
    from app.models.models import Inventory, Item
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
            gra_registration_status="SUCCESS"
        )
        db.add(item)
        db.commit()
        
        inventory1 = Inventory(
            business_id=business.id,
            niki_code="NIKI001",
            item_id=item.id,
            quantity=100.0,
            gra_sync_status="PENDING"
        )
        
        inventory2 = Inventory(
            business_id=business.id,
            niki_code="NIKI002",
            item_id=item.id,
            quantity=200.0,
            gra_sync_status="SUCCESS"
        )
        
        db.add(inventory1)
        db.add(inventory2)
        db.commit()
        
        # Verify relationship
        assert len(item.inventory_records) == 2
        assert inventory1 in item.inventory_records
        assert inventory2 in item.inventory_records
    finally:
        db.close()


def test_query_inventory_by_business():
    """Test querying inventory by business"""
    from app.models.models import Inventory, Item
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
            gra_registration_status="SUCCESS"
        )
        item2 = Item(
            business_id=business2.id,
            item_ref="PROD001",
            item_name="Product 1",
            item_category="GOODS",
            tax_code="B",
            gra_registration_status="SUCCESS"
        )
        db.add(item1)
        db.add(item2)
        db.commit()
        
        for i in range(3):
            inventory = Inventory(
                business_id=business1.id,
                niki_code=f"NIKI_B1_{i}",
                item_id=item1.id,
                quantity=100.0 + i,
                gra_sync_status="PENDING"
            )
            db.add(inventory)
        
        for i in range(2):
            inventory = Inventory(
                business_id=business2.id,
                niki_code=f"NIKI_B2_{i}",
                item_id=item2.id,
                quantity=200.0 + i,
                gra_sync_status="PENDING"
            )
            db.add(inventory)
        
        db.commit()
        
        business1_inventory = db.query(Inventory).filter_by(business_id=business1.id).all()
        business2_inventory = db.query(Inventory).filter_by(business_id=business2.id).all()
        
        assert len(business1_inventory) == 3
        assert len(business2_inventory) == 2
    finally:
        db.close()


def test_inventory_item_relationship_integrity():
    """Test that inventory maintains referential integrity with item"""
    from app.models.models import Inventory, Item
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
            gra_registration_status="SUCCESS"
        )
        db.add(item)
        db.commit()
        
        inventory1 = Inventory(
            business_id=business.id,
            niki_code="NIKI001",
            item_id=item.id,
            quantity=100.0,
            gra_sync_status="PENDING"
        )
        
        inventory2 = Inventory(
            business_id=business.id,
            niki_code="NIKI002",
            item_id=item.id,
            quantity=200.0,
            gra_sync_status="SUCCESS"
        )
        
        db.add(inventory1)
        db.add(inventory2)
        db.commit()
        
        # Verify both inventory records reference the same item
        assert inventory1.item_id == item.id
        assert inventory2.item_id == item.id
        assert inventory1.item == item
        assert inventory2.item == item
    finally:
        db.close()


def test_inventory_multiple_items_per_business():
    """Test multiple inventory records for different items in same business"""
    from app.models.models import Inventory, Item
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
        
        items = []
        for i in range(3):
            item = Item(
                business_id=business.id,
                item_ref=f"PROD_{i}",
                item_name=f"Product {i}",
                item_category="GOODS",
                tax_code="B",
                gra_registration_status="SUCCESS"
            )
            db.add(item)
            items.append(item)
        
        db.commit()
        
        for i, item in enumerate(items):
            inventory = Inventory(
                business_id=business.id,
                niki_code=f"NIKI_{i}",
                item_id=item.id,
                quantity=100.0 * (i + 1),
                gra_sync_status="PENDING"
            )
            db.add(inventory)
        
        db.commit()
        
        inventories = db.query(Inventory).filter_by(business_id=business.id).all()
        assert len(inventories) == 3
        
        for i, inventory in enumerate(inventories):
            assert inventory.quantity == 100.0 * (i + 1)
    finally:
        db.close()


def test_inventory_update_quantity():
    """Test updating inventory quantity"""
    from app.models.models import Inventory, Item
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
            gra_registration_status="SUCCESS"
        )
        db.add(item)
        db.commit()
        
        inventory = Inventory(
            business_id=business.id,
            niki_code="BEEHEIN00011",
            item_id=item.id,
            quantity=250.0,
            gra_sync_status="PENDING"
        )
        db.add(inventory)
        db.commit()
        
        original_quantity = inventory.quantity
        inventory.quantity = 500.0
        db.commit()
        
        updated_inventory = db.query(Inventory).filter_by(id=inventory.id).first()
        assert updated_inventory.quantity == 500.0
        assert updated_inventory.quantity != original_quantity
    finally:
        db.close()


def test_inventory_update_sync_status():
    """Test updating inventory GRA sync status"""
    from app.models.models import Inventory, Item
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
            gra_registration_status="SUCCESS"
        )
        db.add(item)
        db.commit()
        
        inventory = Inventory(
            business_id=business.id,
            niki_code="BEEHEIN00011",
            item_id=item.id,
            quantity=250.0,
            gra_sync_status="PENDING"
        )
        db.add(inventory)
        db.commit()
        
        assert inventory.gra_sync_status == "PENDING"
        
        inventory.gra_sync_status = "SUCCESS"
        db.commit()
        
        updated_inventory = db.query(Inventory).filter_by(id=inventory.id).first()
        assert updated_inventory.gra_sync_status == "SUCCESS"
    finally:
        db.close()


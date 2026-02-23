"""Comprehensive tests for item endpoints"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


from app.main import app
from app.database import get_db, SessionLocal, init_db
from app.models.base import Base
from app.models.models import Business, Item, Inventory, TINValidation, TagDescription
from app.services.business_service import BusinessService


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Initialize database tables for all tests"""
    init_db()
    yield
    # Cleanup after all tests


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def business_with_api_key(mock_hash):
    """Create a business with API key for testing"""
    db = SessionLocal()
    try:
        business, api_key = BusinessService.create_business(
            db,
            business_name="Test Business",
            gra_tin="C0022825405",
            gra_company_name="Test Company",
            gra_security_key="test-security-key"
        )
        db.commit()
        return business, api_key
    finally:
        db.close()


class TestItemRegistrationEndpoint:
    """Tests for POST /api/v1/items/register"""
    
    def test_register_item_success(self, mock_hash, client, business_with_api_key):
        """Test 1: Successfully register an item"""
        business, api_key = business_with_api_key
        
        payload = {
            "ITEM_REF": "PROD001",
            "ITEM_DESCRIPTION": "Office Chair",
            "ITEM_CATEGORY": "GOODS",
            "UNIT_OF_MEASURE": "PIECES",
            "TAX_CODE": "B",
            "TAX_RATE": "15",
            "STANDARD_PRICE": "250.00",
            "COMPANY_TIN": "C0022825405",
            "COMPANY_SECURITY_KEY": "test-security-key"
        }
        
        response = client.post(
            "/api/v1/items/register",
            json=payload,
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["item_ref"] == "PROD001"
        assert data["status"] == "RECEIVED"
        assert "submission_id" in data
    
    def test_register_item_duplicate_ref(self, mock_hash, client, business_with_api_key):
        """Test 2: Reject duplicate item reference"""
        business, api_key = business_with_api_key
        
        # Create first item
        db = SessionLocal()
        try:
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
        finally:
            db.close()
        
        payload = {
            "ITEM_REF": "PROD001",
            "ITEM_DESCRIPTION": "Office Chair",
            "ITEM_CATEGORY": "GOODS",
            "UNIT_OF_MEASURE": "PIECES",
            "TAX_CODE": "B",
            "TAX_RATE": "15",
            "STANDARD_PRICE": "250.00",
            "COMPANY_TIN": "C0022825405",
            "COMPANY_SECURITY_KEY": "test-security-key"
        }
        
        response = client.post(
            "/api/v1/items/register",
            json=payload,
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_register_item_invalid_api_key(self, mock_hash, client):
        """Test 3: Reject invalid API key"""
        payload = {
            "ITEM_REF": "PROD001",
            "ITEM_DESCRIPTION": "Office Chair",
            "ITEM_CATEGORY": "GOODS",
            "UNIT_OF_MEASURE": "PIECES",
            "TAX_CODE": "B",
            "TAX_RATE": "15",
            "STANDARD_PRICE": "250.00",
            "COMPANY_TIN": "C0022825405",
            "COMPANY_SECURITY_KEY": "test-security-key"
        }
        
        response = client.post(
            "/api/v1/items/register",
            json=payload,
            headers={"X-API-Key": "invalid-key"}
        )
        
        assert response.status_code == 401
    
    def test_register_item_all_tax_codes(self, mock_hash, client, business_with_api_key):
        """Test 4: Register items with all valid tax codes"""
        business, api_key = business_with_api_key
        tax_codes = ["A", "B", "C", "D", "E"]
        tax_rates = {"A": "0", "B": "15", "C": "0", "D": "0", "E": "3"}
        
        for tax_code in tax_codes:
            payload = {
                "ITEM_REF": f"PROD_{tax_code}",
                "ITEM_DESCRIPTION": f"Product {tax_code}",
                "ITEM_CATEGORY": "GOODS",
                "UNIT_OF_MEASURE": "PIECES",
                "TAX_CODE": tax_code,
                "TAX_RATE": tax_rates[tax_code],
                "STANDARD_PRICE": "100.00",
                "COMPANY_TIN": "C0022825405",
                "COMPANY_SECURITY_KEY": "test-security-key"
            }
            
            response = client.post(
                "/api/v1/items/register",
                json=payload,
                headers={"X-API-Key": api_key}
            )
            
            assert response.status_code == 202
            assert response.json()["status"] == "RECEIVED"
    
    def test_register_item_invalid_tax_code(self, mock_hash, client, business_with_api_key):
        """Test 5: Reject invalid tax code"""
        business, api_key = business_with_api_key
        
        payload = {
            "ITEM_REF": "PROD001",
            "ITEM_DESCRIPTION": "Office Chair",
            "ITEM_CATEGORY": "GOODS",
            "UNIT_OF_MEASURE": "PIECES",
            "TAX_CODE": "Z",  # Invalid
            "TAX_RATE": "15",
            "STANDARD_PRICE": "250.00",
            "COMPANY_TIN": "C0022825405",
            "COMPANY_SECURITY_KEY": "test-security-key"
        }
        
        response = client.post(
            "/api/v1/items/register",
            json=payload,
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 422  # Validation error


class TestGetItemDetailsEndpoint:
    """Tests for GET /api/v1/items/{item_ref}"""
    
    def test_get_item_details_success(self, mock_hash, client, business_with_api_key):
        """Test 6: Successfully retrieve item details"""
        business, api_key = business_with_api_key
        
        db = SessionLocal()
        try:
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
        finally:
            db.close()
        
        response = client.get(
            "/api/v1/items/PROD001",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["item_ref"] == "PROD001"
        assert data["status"] == "RECEIVED"
    
    def test_get_item_not_found(self, mock_hash, client, business_with_api_key):
        """Test 7: Return 404 for non-existent item"""
        business, api_key = business_with_api_key
        
        response = client.get(
            "/api/v1/items/NONEXISTENT",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 404
    
    def test_get_item_with_gra_id(self, mock_hash, client, business_with_api_key):
        """Test 8: Retrieve item with GRA ID"""
        business, api_key = business_with_api_key
        
        db = SessionLocal()
        try:
            item = Item(
                business_id=business.id,
                item_ref="PROD001",
                item_name="Product 1",
                item_category="GOODS",
                tax_code="B",
                gra_registration_status="REGISTERED",
                gra_item_id="GRA-ITEM-001"
            )
            db.add(item)
            db.commit()
        finally:
            db.close()
        
        response = client.get(
            "/api/v1/items/PROD001",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["gra_item_id"] == "GRA-ITEM-001"
        assert data["status"] == "SUCCESS"


class TestInventoryUpdateEndpoint:
    """Tests for POST /api/v1/inventory/update"""
    
    def test_update_inventory_success(self, mock_hash, client, business_with_api_key):
        """Test 9: Successfully update inventory"""
        business, api_key = business_with_api_key
        
        db = SessionLocal()
        try:
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
        finally:
            db.close()
        
        payload = {
            "ITEM_REF": "PROD001",
            "QUANTITY_CHANGE": "50",
            "OPERATION_TYPE": "IN",
            "REFERENCE_NUM": "PO-2026-001",
            "NOTES": "Stock received",
            "COMPANY_TIN": "C0022825405"
        }
        
        response = client.post(
            "/api/v1/inventory/update",
            json=payload,
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["new_quantity"] == "50"
    
    def test_update_inventory_all_operation_types(self, mock_hash, client, business_with_api_key):
        """Test 10: Update inventory with all operation types"""
        business, api_key = business_with_api_key
        
        db = SessionLocal()
        try:
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
        finally:
            db.close()
        
        operation_types = ["IN", "OUT", "ADJUSTMENT", "RETURN"]
        
        for op_type in operation_types:
            payload = {
                "ITEM_REF": "PROD001",
                "QUANTITY_CHANGE": "10" if op_type in ["IN", "ADJUSTMENT"] else "-5",
                "OPERATION_TYPE": op_type,
                "REFERENCE_NUM": f"REF-{op_type}",
                "COMPANY_TIN": "C0022825405"
            }
            
            response = client.post(
                "/api/v1/inventory/update",
                json=payload,
                headers={"X-API-Key": api_key}
            )
            
            assert response.status_code == 202
            assert response.json()["status"] == "SUCCESS"
    
    def test_update_inventory_negative_quantity(self, mock_hash, client, business_with_api_key):
        """Test 11: Update inventory with negative quantity"""
        business, api_key = business_with_api_key
        
        db = SessionLocal()
        try:
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
        finally:
            db.close()
        
        payload = {
            "ITEM_REF": "PROD001",
            "QUANTITY_CHANGE": "-25",
            "OPERATION_TYPE": "OUT",
            "REFERENCE_NUM": "INV-001",
            "COMPANY_TIN": "C0022825405"
        }
        
        response = client.post(
            "/api/v1/inventory/update",
            json=payload,
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "SUCCESS"
    
    def test_update_inventory_item_not_found(self, mock_hash, client, business_with_api_key):
        """Test 12: Reject inventory update for non-existent item"""
        business, api_key = business_with_api_key
        
        payload = {
            "ITEM_REF": "NONEXISTENT",
            "QUANTITY_CHANGE": "50",
            "OPERATION_TYPE": "IN",
            "REFERENCE_NUM": "PO-001",
            "COMPANY_TIN": "C0022825405"
        }
        
        response = client.post(
            "/api/v1/inventory/update",
            json=payload,
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 404


class TestTINValidationEndpoint:
    """Tests for POST /api/v1/tin/validate"""
    
    def test_validate_tin_success(self, mock_hash, client, business_with_api_key):
        """Test 13: Successfully validate TIN"""
        business, api_key = business_with_api_key
        
        payload = {
            "TIN": "C0022825405",
            "TIN_TYPE": "COMPANY"
        }
        
        response = client.post(
            "/api/v1/tin/validate",
            json=payload,
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tin"] == "C0022825405"
        assert data["is_valid"] is True
        assert data["cached"] is False
    
    def test_validate_tin_cached(self, mock_hash, client, business_with_api_key):
        """Test 14: TIN validation returns cached result"""
        business, api_key = business_with_api_key
        
        # Create cached validation
        db = SessionLocal()
        try:
            tin_validation = TINValidation(
                business_id=business.id,
                tin="C0022825405",
                validation_status="VALID",
                taxpayer_name="Test Company",
                gra_response_code="TIN001",
                cached_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=24)
            )
            db.add(tin_validation)
            db.commit()
        finally:
            db.close()
        
        payload = {
            "TIN": "C0022825405",
            "TIN_TYPE": "COMPANY"
        }
        
        response = client.post(
            "/api/v1/tin/validate",
            json=payload,
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["cached"] is True
        assert data["entity_name"] == "Test Company"
    
    def test_validate_tin_individual(self, mock_hash, client, business_with_api_key):
        """Test 15: Validate individual TIN"""
        business, api_key = business_with_api_key
        
        payload = {
            "TIN": "P0022825405",
            "TIN_TYPE": "INDIVIDUAL"
        }
        
        response = client.post(
            "/api/v1/tin/validate",
            json=payload,
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["tin_type"] == "INDIVIDUAL"


class TestTagDescriptionEndpoint:
    """Tests for POST /api/v1/tags/register"""
    
    def test_register_tag_success(self, mock_hash, client, business_with_api_key):
        """Test 16: Successfully register tag description"""
        business, api_key = business_with_api_key
        
        payload = {
            "TAG_CODE": "TAG001",
            "TAG_DESCRIPTION": "Premium Product",
            "TAG_CATEGORY": "PRODUCT_TYPE",
            "COMPANY_TIN": "C0022825405",
            "COMPANY_SECURITY_KEY": "test-security-key"
        }
        
        response = client.post(
            "/api/v1/tags/register",
            json=payload,
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["tag_code"] == "TAG001"
        assert data["status"] == "RECEIVED"
    
    def test_register_tag_duplicate(self, mock_hash, client, business_with_api_key):
        """Test 17: Reject duplicate tag code"""
        business, api_key = business_with_api_key
        
        # Create first tag
        db = SessionLocal()
        try:
            tag = TagDescription(
                business_id=business.id,
                tag_code="TAG001",
                description="Premium Product",
                category="PRODUCT_TYPE"
            )
            db.add(tag)
            db.commit()
        finally:
            db.close()
        
        payload = {
            "TAG_CODE": "TAG001",
            "TAG_DESCRIPTION": "Premium Product",
            "TAG_CATEGORY": "PRODUCT_TYPE",
            "COMPANY_TIN": "C0022825405",
            "COMPANY_SECURITY_KEY": "test-security-key"
        }
        
        response = client.post(
            "/api/v1/tags/register",
            json=payload,
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]


"""Comprehensive tests for Tag Description model"""
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
def test_tag_description_creation(mock_hash):
    """Test creating a tag description"""
    from app.models.models import TagDescription
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
        
        tag = TagDescription(
            business_id=business.id,
            tag_code="TAG001",
            description="Premium Product",
            category="PRODUCT_TYPE"
        )
        db.add(tag)
        db.commit()
        
        assert tag.id is not None
        assert tag.tag_code == "TAG001"
        assert tag.description == "Premium Product"
        assert tag.category == "PRODUCT_TYPE"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tag_description_without_category(mock_hash):
    """Test tag description creation without category (optional field)"""
    from app.models.models import TagDescription
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
        
        tag = TagDescription(
            business_id=business.id,
            tag_code="TAG002",
            description="Standard Product"
        )
        db.add(tag)
        db.commit()
        
        assert tag.category is None
        assert tag.description == "Standard Product"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tag_description_unique_constraint_per_business(mock_hash):
    """Test tag_code is unique per business"""
    from app.models.models import TagDescription
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
        
        tag1 = TagDescription(
            business_id=business.id,
            tag_code="TAG_SAME",
            description="First Description",
            category="CATEGORY_A"
        )
        db.add(tag1)
        db.commit()
        
        tag2 = TagDescription(
            business_id=business.id,
            tag_code="TAG_SAME",
            description="Second Description",
            category="CATEGORY_B"
        )
        db.add(tag2)
        
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tag_description_same_code_different_businesses(mock_hash):
    """Test same tag_code can exist in different businesses"""
    from app.models.models import TagDescription
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
        
        tag1 = TagDescription(
            business_id=business1.id,
            tag_code="TAG001",
            description="Premium Product",
            category="PRODUCT_TYPE"
        )
        
        tag2 = TagDescription(
            business_id=business2.id,
            tag_code="TAG001",
            description="Premium Product",
            category="PRODUCT_TYPE"
        )
        
        db.add(tag1)
        db.add(tag2)
        db.commit()
        
        assert tag1.tag_code == tag2.tag_code
        assert tag1.business_id != tag2.business_id
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tag_description_with_long_description(mock_hash):
    """Test tag description with long text"""
    from app.models.models import TagDescription
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
        
        long_description = "This is a very long description " * 20
        tag = TagDescription(
            business_id=business.id,
            tag_code="TAG003",
            description=long_description,
            category="PRODUCT_TYPE"
        )
        db.add(tag)
        db.commit()
        
        assert tag.description == long_description
        assert len(tag.description) > 500
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tag_description_timestamps(mock_hash):
    """Test tag description has created_at and updated_at timestamps"""
    from app.models.models import TagDescription
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
        
        tag = TagDescription(
            business_id=business.id,
            tag_code="TAG004",
            description="Test Description",
            category="CATEGORY_A"
        )
        db.add(tag)
        db.commit()
        
        assert tag.created_at is not None
        assert tag.updated_at is not None
        assert isinstance(tag.created_at, datetime)
        assert isinstance(tag.updated_at, datetime)
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_query_tag_descriptions_by_business(mock_hash):
    """Test querying tag descriptions by business"""
    from app.models.models import TagDescription
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
            tag = TagDescription(
                business_id=business1.id,
                tag_code=f"TAG_B1_{i}",
                description=f"Description B1 {i}",
                category="CATEGORY_A"
            )
            db.add(tag)
        
        for i in range(2):
            tag = TagDescription(
                business_id=business2.id,
                tag_code=f"TAG_B2_{i}",
                description=f"Description B2 {i}",
                category="CATEGORY_B"
            )
            db.add(tag)
        
        db.commit()
        
        business1_tags = db.query(TagDescription).filter_by(business_id=business1.id).all()
        business2_tags = db.query(TagDescription).filter_by(business_id=business2.id).all()
        
        assert len(business1_tags) == 3
        assert len(business2_tags) == 2
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tag_description_relationship_with_business(mock_hash):
    """Test tag description relationship with business"""
    from app.models.models import TagDescription
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
        
        tag1 = TagDescription(
            business_id=business.id,
            tag_code="TAG001",
            description="Premium Product",
            category="PRODUCT_TYPE"
        )
        
        tag2 = TagDescription(
            business_id=business.id,
            tag_code="TAG002",
            description="Standard Product",
            category="PRODUCT_TYPE"
        )
        
        db.add(tag1)
        db.add(tag2)
        db.commit()
        
        # Verify relationship
        assert len(business.tag_descriptions) == 2
        assert tag1 in business.tag_descriptions
        assert tag2 in business.tag_descriptions
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tag_description_cascade_delete_with_business(mock_hash):
    """Test that deleting business cascades to delete tag descriptions"""
    from app.models.models import TagDescription
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
        
        tag1 = TagDescription(
            business_id=business.id,
            tag_code="TAG001",
            description="Premium Product",
            category="PRODUCT_TYPE"
        )
        
        tag2 = TagDescription(
            business_id=business.id,
            tag_code="TAG002",
            description="Standard Product",
            category="PRODUCT_TYPE"
        )
        
        db.add(tag1)
        db.add(tag2)
        db.commit()
        
        business_id = business.id
        db.delete(business)
        db.commit()
        
        # Verify business and tags are deleted
        deleted_tags = db.query(TagDescription).filter_by(business_id=business_id).all()
        assert len(deleted_tags) == 0
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tag_description_multiple_categories(mock_hash):
    """Test tag descriptions with different categories"""
    from app.models.models import TagDescription
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
        
        categories = ["PRODUCT_TYPE", "DISCOUNT_TYPE", "PAYMENT_METHOD", "CUSTOMER_TYPE"]
        for i, category in enumerate(categories):
            tag = TagDescription(
                business_id=business.id,
                tag_code=f"TAG_{category}_{i}",
                description=f"Description for {category}",
                category=category
            )
            db.add(tag)
        
        db.commit()
        
        tags = db.query(TagDescription).filter_by(business_id=business.id).all()
        assert len(tags) == 4
        
        for i, category in enumerate(categories):
            assert tags[i].category == category
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tag_description_query_by_tag_code(mock_hash):
    """Test querying tag description by tag code"""
    from app.models.models import TagDescription
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
        
        tag = TagDescription(
            business_id=business.id,
            tag_code="UNIQUE_TAG",
            description="Unique Description",
            category="PRODUCT_TYPE"
        )
        db.add(tag)
        db.commit()
        
        # Query by tag code
        found_tag = db.query(TagDescription).filter_by(
            business_id=business.id,
            tag_code="UNIQUE_TAG"
        ).first()
        
        assert found_tag is not None
        assert found_tag.description == "Unique Description"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tag_description_update(mock_hash):
    """Test updating tag description"""
    from app.models.models import TagDescription
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
        
        tag = TagDescription(
            business_id=business.id,
            tag_code="TAG001",
            description="Original Description",
            category="CATEGORY_A"
        )
        db.add(tag)
        db.commit()
        
        # Update description
        tag.description = "Updated Description"
        tag.category = "CATEGORY_B"
        db.commit()
        
        # Verify update
        updated_tag = db.query(TagDescription).filter_by(tag_code="TAG001").first()
        assert updated_tag.description == "Updated Description"
        assert updated_tag.category == "CATEGORY_B"
    finally:
        db.close()

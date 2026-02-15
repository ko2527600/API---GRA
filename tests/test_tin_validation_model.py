"""Comprehensive tests for TIN validation cache model"""
import pytest
from datetime import datetime, timedelta
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
def test_tin_validation_creation(mock_hash):
    """Test creating a TIN validation cache record"""
    from app.models.models import TINValidation
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
        
        expires_at = datetime.utcnow() + timedelta(hours=24)
        tin_validation = TINValidation(
            business_id=business.id,
            tin="C0022825405",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(tin_validation)
        db.commit()
        
        assert tin_validation.id is not None
        assert tin_validation.tin == "C0022825405"
        assert tin_validation.validation_status == "VALID"
        assert tin_validation.taxpayer_name == "Test Taxpayer"
        assert tin_validation.business_id == business.id
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_all_status_values(mock_hash):
    """Test all TIN validation status values"""
    from app.models.models import TINValidation
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
        
        statuses = ["VALID", "INVALID", "STOPPED", "PROTECTED"]
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        for i, status in enumerate(statuses):
            tin_validation = TINValidation(
                business_id=business.id,
                tin=f"C00{i:010d}",
                validation_status=status,
                taxpayer_name=f"Taxpayer {status}" if status == "VALID" else None,
                gra_response_code=None,
                expires_at=expires_at
            )
            db.add(tin_validation)
        
        db.commit()
        
        validations = db.query(TINValidation).filter_by(business_id=business.id).all()
        assert len(validations) == 4
        
        for i, status in enumerate(statuses):
            assert validations[i].validation_status == status
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_unique_per_business(mock_hash):
    """Test TIN is unique per business"""
    from app.models.models import TINValidation
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
        
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        tin_validation1 = TINValidation(
            business_id=business.id,
            tin="C0022825405",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(tin_validation1)
        db.commit()
        
        tin_validation2 = TINValidation(
            business_id=business.id,
            tin="C0022825405",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(tin_validation2)
        
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_same_tin_different_businesses(mock_hash):
    """Test same TIN can exist in different businesses"""
    from app.models.models import TINValidation
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
        
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        tin_validation1 = TINValidation(
            business_id=business1.id,
            tin="C0022825405",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at
        )
        
        tin_validation2 = TINValidation(
            business_id=business2.id,
            tin="C0022825405",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at
        )
        
        db.add(tin_validation1)
        db.add(tin_validation2)
        db.commit()
        
        assert tin_validation1.tin == tin_validation2.tin
        assert tin_validation1.business_id != tin_validation2.business_id
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_cache_expiration(mock_hash):
    """Test TIN validation cache expiration time"""
    from app.models.models import TINValidation
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
        
        expires_at = datetime.utcnow() + timedelta(hours=24)
        tin_validation = TINValidation(
            business_id=business.id,
            tin="C0022825405",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(tin_validation)
        db.commit()
        
        assert tin_validation.expires_at is not None
        assert isinstance(tin_validation.expires_at, datetime)
        assert tin_validation.expires_at > datetime.utcnow()
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_cached_at_timestamp(mock_hash):
    """Test TIN validation cached_at timestamp"""
    from app.models.models import TINValidation
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
        
        before_time = datetime.utcnow()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        tin_validation = TINValidation(
            business_id=business.id,
            tin="C0022825405",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(tin_validation)
        db.commit()
        after_time = datetime.utcnow()
        
        assert tin_validation.cached_at is not None
        assert isinstance(tin_validation.cached_at, datetime)
        assert before_time <= tin_validation.cached_at <= after_time
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_timestamps(mock_hash):
    """Test TIN validation has created_at and updated_at timestamps"""
    from app.models.models import TINValidation
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
        
        expires_at = datetime.utcnow() + timedelta(hours=24)
        tin_validation = TINValidation(
            business_id=business.id,
            tin="C0022825405",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(tin_validation)
        db.commit()
        
        assert tin_validation.created_at is not None
        assert tin_validation.updated_at is not None
        assert isinstance(tin_validation.created_at, datetime)
        assert isinstance(tin_validation.updated_at, datetime)
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_gra_response_code(mock_hash):
    """Test TIN validation with GRA response code"""
    from app.models.models import TINValidation
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
        
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Valid TIN with no error code
        tin_validation1 = TINValidation(
            business_id=business.id,
            tin="C0022825405",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at
        )
        
        # Invalid TIN with error code
        tin_validation2 = TINValidation(
            business_id=business.id,
            tin="C0022825406",
            validation_status="INVALID",
            taxpayer_name=None,
            gra_response_code="T01",
            expires_at=expires_at
        )
        
        db.add(tin_validation1)
        db.add(tin_validation2)
        db.commit()
        
        assert tin_validation1.gra_response_code is None
        assert tin_validation2.gra_response_code == "T01"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_taxpayer_name_optional(mock_hash):
    """Test taxpayer_name is optional"""
    from app.models.models import TINValidation
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
        
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # With taxpayer name
        tin_validation1 = TINValidation(
            business_id=business.id,
            tin="C0022825405",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at
        )
        
        # Without taxpayer name
        tin_validation2 = TINValidation(
            business_id=business.id,
            tin="C0022825406",
            validation_status="INVALID",
            taxpayer_name=None,
            gra_response_code="T01",
            expires_at=expires_at
        )
        
        db.add(tin_validation1)
        db.add(tin_validation2)
        db.commit()
        
        assert tin_validation1.taxpayer_name == "Test Taxpayer"
        assert tin_validation2.taxpayer_name is None
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_query_by_business(mock_hash):
    """Test querying TIN validations by business"""
    from app.models.models import TINValidation
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
        
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        for i in range(3):
            tin_validation = TINValidation(
                business_id=business1.id,
                tin=f"C00{i:010d}",
                validation_status="VALID",
                taxpayer_name=f"Taxpayer {i}",
                gra_response_code=None,
                expires_at=expires_at
            )
            db.add(tin_validation)
        
        for i in range(2):
            tin_validation = TINValidation(
                business_id=business2.id,
                tin=f"C10{i:010d}",
                validation_status="VALID",
                taxpayer_name=f"Taxpayer {i}",
                gra_response_code=None,
                expires_at=expires_at
            )
            db.add(tin_validation)
        
        db.commit()
        
        business1_validations = db.query(TINValidation).filter_by(business_id=business1.id).all()
        business2_validations = db.query(TINValidation).filter_by(business_id=business2.id).all()
        
        assert len(business1_validations) == 3
        assert len(business2_validations) == 2
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_query_by_tin(mock_hash):
    """Test querying TIN validation by TIN"""
    from app.models.models import TINValidation
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
        
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        tin_validation = TINValidation(
            business_id=business.id,
            tin="C0022825405",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(tin_validation)
        db.commit()
        
        found = db.query(TINValidation).filter_by(business_id=business.id, tin="C0022825405").first()
        assert found is not None
        assert found.tin == "C0022825405"
        assert found.validation_status == "VALID"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_query_expired(mock_hash):
    """Test querying expired TIN validations"""
    from app.models.models import TINValidation
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
        
        # Not expired
        expires_at_future = datetime.utcnow() + timedelta(hours=24)
        tin_validation1 = TINValidation(
            business_id=business.id,
            tin="C0022825405",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at_future
        )
        
        # Expired
        expires_at_past = datetime.utcnow() - timedelta(hours=1)
        tin_validation2 = TINValidation(
            business_id=business.id,
            tin="C0022825406",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at_past
        )
        
        db.add(tin_validation1)
        db.add(tin_validation2)
        db.commit()
        
        # Query non-expired
        non_expired = db.query(TINValidation).filter(
            TINValidation.business_id == business.id,
            TINValidation.expires_at > datetime.utcnow()
        ).all()
        
        assert len(non_expired) == 1
        assert non_expired[0].tin == "C0022825405"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_update_status(mock_hash):
    """Test updating TIN validation status"""
    from app.models.models import TINValidation
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
        
        expires_at = datetime.utcnow() + timedelta(hours=24)
        tin_validation = TINValidation(
            business_id=business.id,
            tin="C0022825405",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(tin_validation)
        db.commit()
        
        assert tin_validation.validation_status == "VALID"
        
        tin_validation.validation_status = "STOPPED"
        db.commit()
        
        updated = db.query(TINValidation).filter_by(id=tin_validation.id).first()
        assert updated.validation_status == "STOPPED"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_update_expiration(mock_hash):
    """Test updating TIN validation expiration time"""
    from app.models.models import TINValidation
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
        
        expires_at = datetime.utcnow() + timedelta(hours=24)
        tin_validation = TINValidation(
            business_id=business.id,
            tin="C0022825405",
            validation_status="VALID",
            taxpayer_name="Test Taxpayer",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(tin_validation)
        db.commit()
        
        original_expiration = tin_validation.expires_at
        new_expiration = datetime.utcnow() + timedelta(hours=48)
        tin_validation.expires_at = new_expiration
        db.commit()
        
        updated = db.query(TINValidation).filter_by(id=tin_validation.id).first()
        assert updated.expires_at != original_expiration
        assert updated.expires_at == new_expiration
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_multiple_tins_per_business(mock_hash):
    """Test multiple TIN validations per business"""
    from app.models.models import TINValidation
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
        
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        tins = ["C0022825405", "C0022825406", "C0022825407"]
        for tin in tins:
            tin_validation = TINValidation(
                business_id=business.id,
                tin=tin,
                validation_status="VALID",
                taxpayer_name=f"Taxpayer {tin}",
                gra_response_code=None,
                expires_at=expires_at
            )
            db.add(tin_validation)
        
        db.commit()
        
        validations = db.query(TINValidation).filter_by(business_id=business.id).all()
        assert len(validations) == 3
        
        for i, validation in enumerate(validations):
            assert validation.tin == tins[i]
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_tin_validation_various_tin_formats(mock_hash):
    """Test TIN validation with various TIN formats"""
    from app.models.models import TINValidation
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
        
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # 11-character TIN
        tin_validation1 = TINValidation(
            business_id=business.id,
            tin="P0012345678",
            validation_status="VALID",
            taxpayer_name="Taxpayer 1",
            gra_response_code=None,
            expires_at=expires_at
        )
        
        # 15-character TIN
        tin_validation2 = TINValidation(
            business_id=business.id,
            tin="C00228254050000",
            validation_status="VALID",
            taxpayer_name="Taxpayer 2",
            gra_response_code=None,
            expires_at=expires_at
        )
        
        db.add(tin_validation1)
        db.add(tin_validation2)
        db.commit()
        
        assert len(tin_validation1.tin) == 11
        assert len(tin_validation2.tin) == 15
    finally:
        db.close()

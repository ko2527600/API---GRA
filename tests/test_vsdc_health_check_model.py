"""Comprehensive tests for VSDC health check model"""
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
def test_vsdc_health_check_creation(mock_hash):
    """Test creating a VSDC health check record"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        vsdc_check = VSDCHealthCheck(
            business_id=business.id,
            status="UP",
            sdc_id="SDC-001",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(vsdc_check)
        db.commit()
        
        assert vsdc_check.id is not None
        assert vsdc_check.status == "UP"
        assert vsdc_check.sdc_id == "SDC-001"
        assert vsdc_check.business_id == business.id
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_all_status_values(mock_hash):
    """Test all VSDC health check status values"""
    from app.models.models import VSDCHealthCheck
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
        
        statuses = ["UP", "DOWN", "DEGRADED"]
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        for i, status in enumerate(statuses):
            vsdc_check = VSDCHealthCheck(
                business_id=business.id,
                status=status,
                sdc_id=f"SDC-{i:03d}",
                gra_response_code=None,
                expires_at=expires_at
            )
            db.add(vsdc_check)
        
        db.commit()
        
        checks = db.query(VSDCHealthCheck).filter_by(business_id=business.id).all()
        assert len(checks) == 3
        
        for i, status in enumerate(statuses):
            assert checks[i].status == status
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_latest_per_business(mock_hash):
    """Test querying latest VSDC health check per business"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        # Create multiple checks
        for i in range(3):
            vsdc_check = VSDCHealthCheck(
                business_id=business.id,
                status="UP" if i < 2 else "DOWN",
                sdc_id=f"SDC-{i:03d}",
                gra_response_code=None,
                expires_at=expires_at
            )
            db.add(vsdc_check)
        
        db.commit()
        
        # Query latest
        latest = db.query(VSDCHealthCheck).filter_by(business_id=business.id).order_by(
            VSDCHealthCheck.checked_at.desc()
        ).first()
        
        assert latest is not None
        assert latest.status == "DOWN"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_expiration(mock_hash):
    """Test VSDC health check expiration time"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        vsdc_check = VSDCHealthCheck(
            business_id=business.id,
            status="UP",
            sdc_id="SDC-001",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(vsdc_check)
        db.commit()
        
        assert vsdc_check.expires_at is not None
        assert isinstance(vsdc_check.expires_at, datetime)
        assert vsdc_check.expires_at > datetime.utcnow()
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_checked_at_timestamp(mock_hash):
    """Test VSDC health check checked_at timestamp"""
    from app.models.models import VSDCHealthCheck
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
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        vsdc_check = VSDCHealthCheck(
            business_id=business.id,
            status="UP",
            sdc_id="SDC-001",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(vsdc_check)
        db.commit()
        after_time = datetime.utcnow()
        
        assert vsdc_check.checked_at is not None
        assert isinstance(vsdc_check.checked_at, datetime)
        assert before_time <= vsdc_check.checked_at <= after_time
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_timestamps(mock_hash):
    """Test VSDC health check has created_at and updated_at timestamps"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        vsdc_check = VSDCHealthCheck(
            business_id=business.id,
            status="UP",
            sdc_id="SDC-001",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(vsdc_check)
        db.commit()
        
        assert vsdc_check.created_at is not None
        assert vsdc_check.updated_at is not None
        assert isinstance(vsdc_check.created_at, datetime)
        assert isinstance(vsdc_check.updated_at, datetime)
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_gra_response_code(mock_hash):
    """Test VSDC health check with GRA response code"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        # Successful check with no error code
        vsdc_check1 = VSDCHealthCheck(
            business_id=business.id,
            status="UP",
            sdc_id="SDC-001",
            gra_response_code=None,
            expires_at=expires_at
        )
        
        # Failed check with error code
        vsdc_check2 = VSDCHealthCheck(
            business_id=business.id,
            status="DOWN",
            sdc_id=None,
            gra_response_code="D06",
            expires_at=expires_at
        )
        
        db.add(vsdc_check1)
        db.add(vsdc_check2)
        db.commit()
        
        assert vsdc_check1.gra_response_code is None
        assert vsdc_check2.gra_response_code == "D06"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_sdc_id_optional(mock_hash):
    """Test sdc_id is optional"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        # With SDC ID
        vsdc_check1 = VSDCHealthCheck(
            business_id=business.id,
            status="UP",
            sdc_id="SDC-001",
            gra_response_code=None,
            expires_at=expires_at
        )
        
        # Without SDC ID
        vsdc_check2 = VSDCHealthCheck(
            business_id=business.id,
            status="DOWN",
            sdc_id=None,
            gra_response_code="D06",
            expires_at=expires_at
        )
        
        db.add(vsdc_check1)
        db.add(vsdc_check2)
        db.commit()
        
        assert vsdc_check1.sdc_id == "SDC-001"
        assert vsdc_check2.sdc_id is None
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_query_by_business(mock_hash):
    """Test querying VSDC health checks by business"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        for i in range(3):
            vsdc_check = VSDCHealthCheck(
                business_id=business1.id,
                status="UP",
                sdc_id=f"SDC-{i:03d}",
                gra_response_code=None,
                expires_at=expires_at
            )
            db.add(vsdc_check)
        
        for i in range(2):
            vsdc_check = VSDCHealthCheck(
                business_id=business2.id,
                status="UP",
                sdc_id=f"SDC-{i:03d}",
                gra_response_code=None,
                expires_at=expires_at
            )
            db.add(vsdc_check)
        
        db.commit()
        
        business1_checks = db.query(VSDCHealthCheck).filter_by(business_id=business1.id).all()
        business2_checks = db.query(VSDCHealthCheck).filter_by(business_id=business2.id).all()
        
        assert len(business1_checks) == 3
        assert len(business2_checks) == 2
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_query_expired(mock_hash):
    """Test querying expired VSDC health checks"""
    from app.models.models import VSDCHealthCheck
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
        expires_at_future = datetime.utcnow() + timedelta(minutes=5)
        vsdc_check1 = VSDCHealthCheck(
            business_id=business.id,
            status="UP",
            sdc_id="SDC-001",
            gra_response_code=None,
            expires_at=expires_at_future
        )
        
        # Expired
        expires_at_past = datetime.utcnow() - timedelta(minutes=1)
        vsdc_check2 = VSDCHealthCheck(
            business_id=business.id,
            status="UP",
            sdc_id="SDC-002",
            gra_response_code=None,
            expires_at=expires_at_past
        )
        
        db.add(vsdc_check1)
        db.add(vsdc_check2)
        db.commit()
        
        # Query non-expired
        non_expired = db.query(VSDCHealthCheck).filter(
            VSDCHealthCheck.business_id == business.id,
            VSDCHealthCheck.expires_at > datetime.utcnow()
        ).all()
        
        assert len(non_expired) == 1
        assert non_expired[0].sdc_id == "SDC-001"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_update_status(mock_hash):
    """Test updating VSDC health check status"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        vsdc_check = VSDCHealthCheck(
            business_id=business.id,
            status="UP",
            sdc_id="SDC-001",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(vsdc_check)
        db.commit()
        
        assert vsdc_check.status == "UP"
        
        vsdc_check.status = "DOWN"
        db.commit()
        
        updated = db.query(VSDCHealthCheck).filter_by(id=vsdc_check.id).first()
        assert updated.status == "DOWN"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_update_expiration(mock_hash):
    """Test updating VSDC health check expiration time"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        vsdc_check = VSDCHealthCheck(
            business_id=business.id,
            status="UP",
            sdc_id="SDC-001",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(vsdc_check)
        db.commit()
        
        original_expiration = vsdc_check.expires_at
        new_expiration = datetime.utcnow() + timedelta(minutes=10)
        vsdc_check.expires_at = new_expiration
        db.commit()
        
        updated = db.query(VSDCHealthCheck).filter_by(id=vsdc_check.id).first()
        assert updated.expires_at != original_expiration
        assert updated.expires_at == new_expiration
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_multiple_checks_per_business(mock_hash):
    """Test multiple VSDC health checks per business"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        statuses = ["UP", "DOWN", "DEGRADED"]
        for status in statuses:
            vsdc_check = VSDCHealthCheck(
                business_id=business.id,
                status=status,
                sdc_id=f"SDC-{status}",
                gra_response_code=None,
                expires_at=expires_at
            )
            db.add(vsdc_check)
        
        db.commit()
        
        checks = db.query(VSDCHealthCheck).filter_by(business_id=business.id).all()
        assert len(checks) == 3
        
        for i, check in enumerate(checks):
            assert check.status == statuses[i]
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_different_businesses(mock_hash):
    """Test VSDC health checks for different businesses are isolated"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        vsdc_check1 = VSDCHealthCheck(
            business_id=business1.id,
            status="UP",
            sdc_id="SDC-001",
            gra_response_code=None,
            expires_at=expires_at
        )
        
        vsdc_check2 = VSDCHealthCheck(
            business_id=business2.id,
            status="DOWN",
            sdc_id=None,
            gra_response_code="D06",
            expires_at=expires_at
        )
        
        db.add(vsdc_check1)
        db.add(vsdc_check2)
        db.commit()
        
        business1_checks = db.query(VSDCHealthCheck).filter_by(business_id=business1.id).all()
        business2_checks = db.query(VSDCHealthCheck).filter_by(business_id=business2.id).all()
        
        assert len(business1_checks) == 1
        assert len(business2_checks) == 1
        assert business1_checks[0].status == "UP"
        assert business2_checks[0].status == "DOWN"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_degraded_status(mock_hash):
    """Test VSDC health check with DEGRADED status"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        vsdc_check = VSDCHealthCheck(
            business_id=business.id,
            status="DEGRADED",
            sdc_id="SDC-001",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(vsdc_check)
        db.commit()
        
        assert vsdc_check.status == "DEGRADED"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_various_sdc_ids(mock_hash):
    """Test VSDC health check with various SDC ID formats"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        sdc_ids = ["SDC-001", "VSDC-12345", "GRA-SDC-ABC123"]
        for sdc_id in sdc_ids:
            vsdc_check = VSDCHealthCheck(
                business_id=business.id,
                status="UP",
                sdc_id=sdc_id,
                gra_response_code=None,
                expires_at=expires_at
            )
            db.add(vsdc_check)
        
        db.commit()
        
        checks = db.query(VSDCHealthCheck).filter_by(business_id=business.id).all()
        assert len(checks) == 3
        
        for i, check in enumerate(checks):
            assert check.sdc_id == sdc_ids[i]
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_various_error_codes(mock_hash):
    """Test VSDC health check with various GRA error codes"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        
        error_codes = ["D06", "A13", "IS100"]
        for error_code in error_codes:
            vsdc_check = VSDCHealthCheck(
                business_id=business.id,
                status="DOWN",
                sdc_id=None,
                gra_response_code=error_code,
                expires_at=expires_at
            )
            db.add(vsdc_check)
        
        db.commit()
        
        checks = db.query(VSDCHealthCheck).filter_by(business_id=business.id).all()
        assert len(checks) == 3
        
        for i, check in enumerate(checks):
            assert check.gra_response_code == error_codes[i]
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_five_minute_cache(mock_hash):
    """Test VSDC health check with 5-minute cache expiration"""
    from app.models.models import VSDCHealthCheck
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
        
        # Create check with 5-minute expiration
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        vsdc_check = VSDCHealthCheck(
            business_id=business.id,
            status="UP",
            sdc_id="SDC-001",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(vsdc_check)
        db.commit()
        
        # Verify expiration is approximately 5 minutes from now
        time_diff = (vsdc_check.expires_at - datetime.utcnow()).total_seconds()
        assert 290 < time_diff < 310  # Allow 10 second variance
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_vsdc_health_check_delete_cascade(mock_hash):
    """Test VSDC health check is deleted when business is deleted"""
    from app.models.models import VSDCHealthCheck
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
        
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        vsdc_check = VSDCHealthCheck(
            business_id=business.id,
            status="UP",
            sdc_id="SDC-001",
            gra_response_code=None,
            expires_at=expires_at
        )
        db.add(vsdc_check)
        db.commit()
        
        check_id = vsdc_check.id
        
        db.delete(business)
        db.commit()
        
        deleted_check = db.query(VSDCHealthCheck).filter_by(id=check_id).first()
        assert deleted_check is None
    finally:
        db.close()

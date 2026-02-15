"""Comprehensive tests for Z-Report model"""
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
def test_z_report_creation(mock_hash):
    """Test creating a Z-Report record"""
    from app.models.models import ZReport
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
        
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10,
            inv_open=5,
            inv_vat=1500.00,
            inv_total=10000.00,
            inv_levy=500.00
        )
        db.add(z_report)
        db.commit()
        
        assert z_report.id is not None
        assert z_report.report_date == "2026-02-10"
        assert z_report.inv_close == 5
        assert z_report.inv_count == 10
        assert z_report.inv_open == 5
        assert z_report.inv_vat == 1500.00
        assert z_report.inv_total == 10000.00
        assert z_report.inv_levy == 500.00
        assert z_report.business_id == business.id
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_unique_per_business_per_date(mock_hash):
    """Test report_date is unique per business"""
    from app.models.models import ZReport
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
        
        z_report1 = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10,
            inv_open=5,
            inv_vat=1500.00,
            inv_total=10000.00,
            inv_levy=500.00
        )
        db.add(z_report1)
        db.commit()
        
        z_report2 = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=3,
            inv_count=8,
            inv_open=5,
            inv_vat=1200.00,
            inv_total=9000.00,
            inv_levy=400.00
        )
        db.add(z_report2)
        
        with pytest.raises(IntegrityError):
            db.commit()
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_same_date_different_businesses(mock_hash):
    """Test same date can exist in different businesses"""
    from app.models.models import ZReport
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
        
        z_report1 = ZReport(
            business_id=business1.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10,
            inv_open=5,
            inv_vat=1500.00,
            inv_total=10000.00,
            inv_levy=500.00
        )
        
        z_report2 = ZReport(
            business_id=business2.id,
            report_date="2026-02-10",
            inv_close=3,
            inv_count=8,
            inv_open=5,
            inv_vat=1200.00,
            inv_total=9000.00,
            inv_levy=400.00
        )
        
        db.add(z_report1)
        db.add(z_report2)
        db.commit()
        
        assert z_report1.report_date == z_report2.report_date
        assert z_report1.business_id != z_report2.business_id
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_all_fields_optional_except_required(mock_hash):
    """Test Z-Report with only required fields"""
    from app.models.models import ZReport
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
        
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10"
        )
        db.add(z_report)
        db.commit()
        
        assert z_report.id is not None
        assert z_report.report_date == "2026-02-10"
        assert z_report.inv_close is None
        assert z_report.inv_count is None
        assert z_report.inv_open is None
        assert z_report.inv_vat is None
        assert z_report.inv_total is None
        assert z_report.inv_levy is None
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_with_gra_response_code(mock_hash):
    """Test Z-Report with GRA response code"""
    from app.models.models import ZReport
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
        
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10,
            inv_open=5,
            inv_vat=1500.00,
            inv_total=10000.00,
            inv_levy=500.00,
            gra_response_code="D06"
        )
        db.add(z_report)
        db.commit()
        
        assert z_report.gra_response_code == "D06"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_with_raw_response(mock_hash):
    """Test Z-Report with raw GRA response"""
    from app.models.models import ZReport
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
        
        raw_response = {
            "status": "SUCCESS",
            "inv_close": 5,
            "inv_count": 10,
            "inv_open": 5,
            "inv_vat": 1500.00,
            "inv_total": 10000.00,
            "inv_levy": 500.00
        }
        
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10,
            inv_open=5,
            inv_vat=1500.00,
            inv_total=10000.00,
            inv_levy=500.00,
            raw_response=raw_response
        )
        db.add(z_report)
        db.commit()
        
        assert z_report.raw_response == raw_response
        assert z_report.raw_response["status"] == "SUCCESS"
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_timestamps(mock_hash):
    """Test Z-Report has created_at and updated_at timestamps"""
    from app.models.models import ZReport
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
        
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10,
            inv_open=5,
            inv_vat=1500.00,
            inv_total=10000.00,
            inv_levy=500.00
        )
        db.add(z_report)
        db.commit()
        
        assert z_report.created_at is not None
        assert z_report.updated_at is not None
        assert isinstance(z_report.created_at, datetime)
        assert isinstance(z_report.updated_at, datetime)
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_query_by_business(mock_hash):
    """Test querying Z-Reports by business"""
    from app.models.models import ZReport
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
            z_report = ZReport(
                business_id=business1.id,
                report_date=f"2026-02-{10+i:02d}",
                inv_close=5,
                inv_count=10,
                inv_open=5,
                inv_vat=1500.00,
                inv_total=10000.00,
                inv_levy=500.00
            )
            db.add(z_report)
        
        for i in range(2):
            z_report = ZReport(
                business_id=business2.id,
                report_date=f"2026-02-{10+i:02d}",
                inv_close=3,
                inv_count=8,
                inv_open=5,
                inv_vat=1200.00,
                inv_total=9000.00,
                inv_levy=400.00
            )
            db.add(z_report)
        
        db.commit()
        
        business1_reports = db.query(ZReport).filter_by(business_id=business1.id).all()
        business2_reports = db.query(ZReport).filter_by(business_id=business2.id).all()
        
        assert len(business1_reports) == 3
        assert len(business2_reports) == 2
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_query_by_date(mock_hash):
    """Test querying Z-Report by date"""
    from app.models.models import ZReport
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
        
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10,
            inv_open=5,
            inv_vat=1500.00,
            inv_total=10000.00,
            inv_levy=500.00
        )
        db.add(z_report)
        db.commit()
        
        found = db.query(ZReport).filter_by(business_id=business.id, report_date="2026-02-10").first()
        assert found is not None
        assert found.report_date == "2026-02-10"
        assert found.inv_close == 5
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_update_values(mock_hash):
    """Test updating Z-Report values"""
    from app.models.models import ZReport
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
        
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10,
            inv_open=5,
            inv_vat=1500.00,
            inv_total=10000.00,
            inv_levy=500.00
        )
        db.add(z_report)
        db.commit()
        
        assert z_report.inv_close == 5
        
        z_report.inv_close = 7
        z_report.inv_count = 12
        z_report.inv_vat = 1800.00
        db.commit()
        
        updated = db.query(ZReport).filter_by(id=z_report.id).first()
        assert updated.inv_close == 7
        assert updated.inv_count == 12
        assert updated.inv_vat == 1800.00
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_multiple_dates_per_business(mock_hash):
    """Test multiple Z-Reports for different dates per business"""
    from app.models.models import ZReport
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
        
        dates = ["2026-02-08", "2026-02-09", "2026-02-10"]
        for date in dates:
            z_report = ZReport(
                business_id=business.id,
                report_date=date,
                inv_close=5,
                inv_count=10,
                inv_open=5,
                inv_vat=1500.00,
                inv_total=10000.00,
                inv_levy=500.00
            )
            db.add(z_report)
        
        db.commit()
        
        reports = db.query(ZReport).filter_by(business_id=business.id).all()
        assert len(reports) == 3
        
        for i, report in enumerate(reports):
            assert report.report_date == dates[i]
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_date_format_yyyy_mm_dd(mock_hash):
    """Test Z-Report date format is YYYY-MM-DD"""
    from app.models.models import ZReport
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
        
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10,
            inv_open=5,
            inv_vat=1500.00,
            inv_total=10000.00,
            inv_levy=500.00
        )
        db.add(z_report)
        db.commit()
        
        assert len(z_report.report_date) == 10
        assert z_report.report_date.count("-") == 2
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_numeric_fields(mock_hash):
    """Test Z-Report numeric fields"""
    from app.models.models import ZReport
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
        
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10,
            inv_open=5,
            inv_vat=1500.50,
            inv_total=10000.75,
            inv_levy=500.25
        )
        db.add(z_report)
        db.commit()
        
        assert isinstance(z_report.inv_close, int)
        assert isinstance(z_report.inv_count, int)
        assert isinstance(z_report.inv_open, int)
        assert isinstance(z_report.inv_vat, float)
        assert isinstance(z_report.inv_total, float)
        assert isinstance(z_report.inv_levy, float)
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_zero_values(mock_hash):
    """Test Z-Report with zero values"""
    from app.models.models import ZReport
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
        
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=0,
            inv_count=0,
            inv_open=0,
            inv_vat=0.0,
            inv_total=0.0,
            inv_levy=0.0
        )
        db.add(z_report)
        db.commit()
        
        assert z_report.inv_close == 0
        assert z_report.inv_count == 0
        assert z_report.inv_open == 0
        assert z_report.inv_vat == 0.0
        assert z_report.inv_total == 0.0
        assert z_report.inv_levy == 0.0
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_large_values(mock_hash):
    """Test Z-Report with large numeric values"""
    from app.models.models import ZReport
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
        
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=999999,
            inv_count=999999,
            inv_open=999999,
            inv_vat=999999999.99,
            inv_total=999999999.99,
            inv_levy=999999999.99
        )
        db.add(z_report)
        db.commit()
        
        assert z_report.inv_close == 999999
        assert z_report.inv_count == 999999
        assert z_report.inv_open == 999999
        assert z_report.inv_vat == 999999999.99
        assert z_report.inv_total == 999999999.99
        assert z_report.inv_levy == 999999999.99
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_delete_cascade(mock_hash):
    """Test Z-Report is deleted when business is deleted"""
    from app.models.models import ZReport
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
        
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10,
            inv_open=5,
            inv_vat=1500.00,
            inv_total=10000.00,
            inv_levy=500.00
        )
        db.add(z_report)
        db.commit()
        
        report_id = z_report.id
        
        db.delete(business)
        db.commit()
        
        deleted_report = db.query(ZReport).filter_by(id=report_id).first()
        assert deleted_report is None
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_query_by_date_range(mock_hash):
    """Test querying Z-Reports by date range"""
    from app.models.models import ZReport
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
        
        dates = ["2026-02-08", "2026-02-09", "2026-02-10", "2026-02-11", "2026-02-12"]
        for date in dates:
            z_report = ZReport(
                business_id=business.id,
                report_date=date,
                inv_close=5,
                inv_count=10,
                inv_open=5,
                inv_vat=1500.00,
                inv_total=10000.00,
                inv_levy=500.00
            )
            db.add(z_report)
        
        db.commit()
        
        # Query reports between 2026-02-09 and 2026-02-11
        reports = db.query(ZReport).filter(
            ZReport.business_id == business.id,
            ZReport.report_date >= "2026-02-09",
            ZReport.report_date <= "2026-02-11"
        ).all()
        
        assert len(reports) == 3
        assert all(r.report_date in ["2026-02-09", "2026-02-10", "2026-02-11"] for r in reports)
    finally:
        db.close()


@patch('app.services.api_key_service.pwd_context.hash')
def test_z_report_partial_data(mock_hash):
    """Test Z-Report with partial data (some fields null)"""
    from app.models.models import ZReport
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
        
        z_report = ZReport(
            business_id=business.id,
            report_date="2026-02-10",
            inv_close=5,
            inv_count=10,
            inv_vat=1500.00
        )
        db.add(z_report)
        db.commit()
        
        assert z_report.inv_close == 5
        assert z_report.inv_count == 10
        assert z_report.inv_vat == 1500.00
        assert z_report.inv_open is None
        assert z_report.inv_total is None
        assert z_report.inv_levy is None
    finally:
        db.close()

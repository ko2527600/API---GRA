"""Tests for business credential encryption/decryption"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import Business
from app.models.base import Base
from app.services.business_service import BusinessService
from app.config import settings


class TestBusinessCredentialMethods:
    """Test Business model credential methods"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test database for each test"""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def test_get_decrypted_gra_tin(self):
        """Test decrypting GRA TIN"""
        db = self.SessionLocal()
        try:
            test_data = {
                "business_name": "Test Business Ltd",
                "gra_tin": "P00123456789",
                "gra_company_name": "Test Business Limited",
                "gra_security_key": "test-security-key-12345"
            }
            business, _ = BusinessService.create_business(db, **test_data)
            decrypted_tin = business.get_decrypted_gra_tin()
            assert decrypted_tin == test_data["gra_tin"]
        finally:
            db.close()
    
    def test_get_decrypted_gra_company_name(self):
        """Test decrypting GRA company name"""
        db = self.SessionLocal()
        try:
            test_data = {
                "business_name": "Test Business Ltd",
                "gra_tin": "P00123456789",
                "gra_company_name": "Test Business Limited",
                "gra_security_key": "test-security-key-12345"
            }
            business, _ = BusinessService.create_business(db, **test_data)
            decrypted_name = business.get_decrypted_gra_company_name()
            assert decrypted_name == test_data["gra_company_name"]
        finally:
            db.close()
    
    def test_get_decrypted_gra_security_key(self):
        """Test decrypting GRA security key"""
        db = self.SessionLocal()
        try:
            test_data = {
                "business_name": "Test Business Ltd",
                "gra_tin": "P00123456789",
                "gra_company_name": "Test Business Limited",
                "gra_security_key": "test-security-key-12345"
            }
            business, _ = BusinessService.create_business(db, **test_data)
            decrypted_key = business.get_decrypted_gra_security_key()
            assert decrypted_key == test_data["gra_security_key"]
        finally:
            db.close()
    
    def test_get_decrypted_gra_credentials(self):
        """Test getting all decrypted GRA credentials"""
        db = self.SessionLocal()
        try:
            test_data = {
                "business_name": "Test Business Ltd",
                "gra_tin": "P00123456789",
                "gra_company_name": "Test Business Limited",
                "gra_security_key": "test-security-key-12345"
            }
            business, _ = BusinessService.create_business(db, **test_data)
            credentials = business.get_decrypted_gra_credentials()
            assert isinstance(credentials, dict)
            assert credentials["gra_tin"] == test_data["gra_tin"]
            assert credentials["gra_company_name"] == test_data["gra_company_name"]
            assert credentials["gra_security_key"] == test_data["gra_security_key"]
        finally:
            db.close()
    
    def test_credentials_are_encrypted_in_database(self):
        """Test that credentials are stored encrypted in database"""
        db = self.SessionLocal()
        try:
            test_data = {
                "business_name": "Test Business Ltd",
                "gra_tin": "P00123456789",
                "gra_company_name": "Test Business Limited",
                "gra_security_key": "test-security-key-12345"
            }
            business, _ = BusinessService.create_business(db, **test_data)
            assert business.gra_tin != test_data["gra_tin"]
            assert business.gra_company_name != test_data["gra_company_name"]
            assert business.gra_security_key != test_data["gra_security_key"]
            assert business.gra_tin.startswith("gAAAAAB")
            assert business.gra_company_name.startswith("gAAAAAB")
            assert business.gra_security_key.startswith("gAAAAAB")
        finally:
            db.close()
    
    def test_decrypt_corrupted_data(self):
        """Test decryption fails with corrupted data"""
        db = self.SessionLocal()
        try:
            test_data = {
                "business_name": "Test Business Ltd",
                "gra_tin": "P00123456789",
                "gra_company_name": "Test Business Limited",
                "gra_security_key": "test-security-key-12345"
            }
            business, _ = BusinessService.create_business(db, **test_data)
            business.gra_tin = "corrupted-data-not-encrypted"
            with pytest.raises(ValueError, match="Decryption failed"):
                business.get_decrypted_gra_tin()
        finally:
            db.close()
    
    def test_multiple_businesses_have_different_encrypted_values(self):
        """Test that same plaintext encrypts differently for different businesses"""
        db = self.SessionLocal()
        try:
            data1 = {
                "business_name": "Business 1",
                "gra_tin": "P00111111111",
                "gra_company_name": "Company 1",
                "gra_security_key": "key-1"
            }
            data2 = {
                "business_name": "Business 2",
                "gra_tin": "P00111111111",
                "gra_company_name": "Company 2",
                "gra_security_key": "key-2"
            }
            business1, _ = BusinessService.create_business(db, **data1)
            business2, _ = BusinessService.create_business(db, **data2)
            assert business1.gra_tin != business2.gra_tin
            assert business1.get_decrypted_gra_tin() == business2.get_decrypted_gra_tin()
        finally:
            db.close()
    
    def test_credentials_persist_after_database_refresh(self):
        """Test that credentials can be decrypted after database refresh"""
        db = self.SessionLocal()
        try:
            test_data = {
                "business_name": "Test Business Ltd",
                "gra_tin": "P00123456789",
                "gra_company_name": "Test Business Limited",
                "gra_security_key": "test-security-key-12345"
            }
            business, _ = BusinessService.create_business(db, **test_data)
            db.refresh(business)
            assert business.get_decrypted_gra_tin() == test_data["gra_tin"]
            assert business.get_decrypted_gra_company_name() == test_data["gra_company_name"]
            assert business.get_decrypted_gra_security_key() == test_data["gra_security_key"]
        finally:
            db.close()
    
    def test_get_decrypted_credentials_returns_all_fields(self):
        """Test that get_decrypted_gra_credentials returns all required fields"""
        db = self.SessionLocal()
        try:
            test_data = {
                "business_name": "Test Business Ltd",
                "gra_tin": "P00123456789",
                "gra_company_name": "Test Business Limited",
                "gra_security_key": "test-security-key-12345"
            }
            business, _ = BusinessService.create_business(db, **test_data)
            credentials = business.get_decrypted_gra_credentials()
            assert "gra_tin" in credentials
            assert "gra_company_name" in credentials
            assert "gra_security_key" in credentials
            assert len(credentials) == 3
        finally:
            db.close()
    
    def test_decrypt_empty_encrypted_field(self):
        """Test decryption fails with empty encrypted field"""
        db = self.SessionLocal()
        try:
            test_data = {
                "business_name": "Test Business Ltd",
                "gra_tin": "P00123456789",
                "gra_company_name": "Test Business Limited",
                "gra_security_key": "test-security-key-12345"
            }
            business, _ = BusinessService.create_business(db, **test_data)
            business.gra_tin = ""
            with pytest.raises(ValueError, match="Cannot decrypt empty data"):
                business.get_decrypted_gra_tin()
        finally:
            db.close()
    
    def test_credentials_with_special_characters(self):
        """Test encryption/decryption with special characters"""
        db = self.SessionLocal()
        try:
            special_data = {
                "business_name": "Test & Co.",
                "gra_tin": "P00123456789",
                "gra_company_name": "Test Company (Pty) Ltd.",
                "gra_security_key": "key!@#$%^&*()_+-=[]{}|;:',.<>?/"
            }
            business, _ = BusinessService.create_business(db, **special_data)
            credentials = business.get_decrypted_gra_credentials()
            assert credentials["gra_company_name"] == special_data["gra_company_name"]
            assert credentials["gra_security_key"] == special_data["gra_security_key"]
        finally:
            db.close()
    
    def test_credentials_with_unicode_characters(self):
        """Test encryption/decryption with unicode characters"""
        db = self.SessionLocal()
        try:
            unicode_data = {
                "business_name": "Test Business",
                "gra_tin": "P00123456789",
                "gra_company_name": "Тестовая Компания",
                "gra_security_key": "キー"
            }
            business, _ = BusinessService.create_business(db, **unicode_data)
            credentials = business.get_decrypted_gra_credentials()
            assert credentials["gra_company_name"] == unicode_data["gra_company_name"]
            assert credentials["gra_security_key"] == unicode_data["gra_security_key"]
        finally:
            db.close()

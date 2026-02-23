"""Tests for secrets management service"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from datetime import datetime

from app.models.models import Business
from app.models.base import Base
from app.services.secrets_manager import SecretsManager
from app.services.business_service import BusinessService
from app.config import settings


class TestSecretsManager:
    """Test suite for SecretsManager"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test database for each test"""
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def test_store_gra_credentials(self):
        """Test storing GRA credentials"""
        db = self.SessionLocal()
        try:
            # Create business first
            business, _ = BusinessService.create_business(
                db,
                business_name="Test Business",
                gra_tin="P00123456789",
                gra_company_name="Test Company",
                gra_security_key="test-key"
            )
            
            # Store credentials
            result = SecretsManager.store_gra_credentials(
                db,
                business.id,
                gra_tin="P00987654321",
                gra_company_name="Updated Company",
                gra_security_key="updated-key"
            )
            
            assert result["business_id"] == str(business.id)
            assert result["status"] == "active"
            assert "stored_at" in result
            
            # Verify credentials were updated
            db.refresh(business)
            credentials = business.get_decrypted_gra_credentials()
            assert credentials["gra_tin"] == "P00987654321"
            assert credentials["gra_company_name"] == "Updated Company"
            assert credentials["gra_security_key"] == "updated-key"
        finally:
            db.close()
    
    def test_store_credentials_with_empty_values(self):
        """Test storing credentials with empty values raises error"""
        db = self.SessionLocal()
        try:
            business, _ = BusinessService.create_business(
                db,
                business_name="Test Business",
                gra_tin="P00123456789",
                gra_company_name="Test Company",
                gra_security_key="test-key"
            )
            
            with pytest.raises(ValueError, match="All GRA credentials must be provided"):
                SecretsManager.store_gra_credentials(
                    db,
                    business.id,
                    gra_tin="",
                    gra_company_name="Company",
                    gra_security_key="key"
                )
        finally:
            db.close()
    
    def test_retrieve_gra_credentials(self):
        """Test retrieving GRA credentials"""
        db = self.SessionLocal()
        try:
            business, _ = BusinessService.create_business(
                db,
                business_name="Test Business",
                gra_tin="P00123456789",
                gra_company_name="Test Company",
                gra_security_key="test-key"
            )
            
            credentials = SecretsManager.retrieve_gra_credentials(db, business.id)
            
            assert credentials["gra_tin"] == "P00123456789"
            assert credentials["gra_company_name"] == "Test Company"
            assert credentials["gra_security_key"] == "test-key"
        finally:
            db.close()
    
    def test_retrieve_credentials_for_inactive_business(self):
        """Test retrieving credentials for inactive business raises error"""
        db = self.SessionLocal()
        try:
            business, _ = BusinessService.create_business(
                db,
                business_name="Test Business",
                gra_tin="P00123456789",
                gra_company_name="Test Company",
                gra_security_key="test-key"
            )
            
            # Deactivate business
            business.status = "inactive"
            db.commit()
            
            with pytest.raises(ValueError, match="not active"):
                SecretsManager.retrieve_gra_credentials(db, business.id)
        finally:
            db.close()
    
    def test_rotate_gra_credentials(self):
        """Test rotating GRA credentials"""
        db = self.SessionLocal()
        try:
            business, _ = BusinessService.create_business(
                db,
                business_name="Test Business",
                gra_tin="P00123456789",
                gra_company_name="Test Company",
                gra_security_key="test-key"
            )
            
            # Rotate credentials
            result = SecretsManager.rotate_gra_credentials(
                db,
                business.id,
                new_gra_tin="P00999999999",
                new_gra_company_name="New Company",
                new_gra_security_key="new-key"
            )
            
            assert result["business_id"] == str(business.id)
            assert result["status"] == "success"
            assert "rotated_at" in result
            
            # Verify new credentials
            db.refresh(business)
            credentials = business.get_decrypted_gra_credentials()
            assert credentials["gra_tin"] == "P00999999999"
            assert credentials["gra_company_name"] == "New Company"
            assert credentials["gra_security_key"] == "new-key"
        finally:
            db.close()
    
    def test_rotate_credentials_with_empty_values(self):
        """Test rotating credentials with empty values raises error"""
        db = self.SessionLocal()
        try:
            business, _ = BusinessService.create_business(
                db,
                business_name="Test Business",
                gra_tin="P00123456789",
                gra_company_name="Test Company",
                gra_security_key="test-key"
            )
            
            with pytest.raises(ValueError, match="All new GRA credentials must be provided"):
                SecretsManager.rotate_gra_credentials(
                    db,
                    business.id,
                    new_gra_tin="",
                    new_gra_company_name="Company",
                    new_gra_security_key="key"
                )
        finally:
            db.close()
    
    def test_revoke_gra_credentials(self):
        """Test revoking GRA credentials"""
        db = self.SessionLocal()
        try:
            business, _ = BusinessService.create_business(
                db,
                business_name="Test Business",
                gra_tin="P00123456789",
                gra_company_name="Test Company",
                gra_security_key="test-key"
            )
            
            # Revoke credentials
            result = SecretsManager.revoke_gra_credentials(
                db,
                business.id,
                reason="Security breach"
            )
            
            assert result["business_id"] == str(business.id)
            assert result["status"] == "revoked"
            assert result["reason"] == "Security breach"
            
            # Verify business is inactive
            db.refresh(business)
            assert business.status == "inactive"
        finally:
            db.close()
    
    def test_validate_gra_credentials_valid(self):
        """Test validating valid GRA credentials"""
        db = self.SessionLocal()
        try:
            business, _ = BusinessService.create_business(
                db,
                business_name="Test Business",
                gra_tin="P00123456789",
                gra_company_name="Test Company",
                gra_security_key="test-key"
            )
            
            result = SecretsManager.validate_gra_credentials(db, business.id)
            
            assert result["business_id"] == str(business.id)
            assert result["status"] == "valid"
            assert result["checks"]["business_active"] is True
            assert result["checks"]["gra_tin_encrypted"] is True
            assert result["checks"]["gra_company_name_encrypted"] is True
            assert result["checks"]["gra_security_key_encrypted"] is True
            assert result["checks"]["credentials_decryptable"] is True
            assert result["checks"]["all_credentials_present"] is True
        finally:
            db.close()
    
    def test_validate_credentials_inactive_business(self):
        """Test validating credentials for inactive business"""
        db = self.SessionLocal()
        try:
            business, _ = BusinessService.create_business(
                db,
                business_name="Test Business",
                gra_tin="P00123456789",
                gra_company_name="Test Company",
                gra_security_key="test-key"
            )
            
            # Deactivate business
            business.status = "inactive"
            db.commit()
            
            result = SecretsManager.validate_gra_credentials(db, business.id)
            
            assert result["status"] == "invalid"
            assert result["checks"]["business_active"] is False
        finally:
            db.close()
    
    def test_get_credential_metadata(self):
        """Test getting credential metadata"""
        db = self.SessionLocal()
        try:
            business, _ = BusinessService.create_business(
                db,
                business_name="Test Business",
                gra_tin="P00123456789",
                gra_company_name="Test Company",
                gra_security_key="test-key"
            )
            
            metadata = SecretsManager.get_credential_metadata(db, business.id)
            
            assert metadata["business_id"] == str(business.id)
            assert metadata["business_name"] == "Test Business"
            assert metadata["status"] == "active"
            assert metadata["credentials_stored"] is True
            assert metadata["credentials_encrypted"] is True
            assert "created_at" in metadata
            assert "updated_at" in metadata
        finally:
            db.close()
    
    def test_retrieve_nonexistent_business(self):
        """Test retrieving credentials for nonexistent business"""
        db = self.SessionLocal()
        try:
            import uuid
            fake_id = uuid.uuid4()
            
            with pytest.raises(ValueError, match="not found"):
                SecretsManager.retrieve_gra_credentials(db, fake_id)
        finally:
            db.close()
    
    def test_store_credentials_nonexistent_business(self):
        """Test storing credentials for nonexistent business"""
        db = self.SessionLocal()
        try:
            import uuid
            fake_id = uuid.uuid4()
            
            with pytest.raises(ValueError, match="not found"):
                SecretsManager.store_gra_credentials(
                    db,
                    fake_id,
                    gra_tin="P00123456789",
                    gra_company_name="Company",
                    gra_security_key="key"
                )
        finally:
            db.close()
    
    def test_rotate_credentials_nonexistent_business(self):
        """Test rotating credentials for nonexistent business"""
        db = self.SessionLocal()
        try:
            import uuid
            fake_id = uuid.uuid4()
            
            with pytest.raises(ValueError, match="not found"):
                SecretsManager.rotate_gra_credentials(
                    db,
                    fake_id,
                    new_gra_tin="P00123456789",
                    new_gra_company_name="Company",
                    new_gra_security_key="key"
                )
        finally:
            db.close()
    
    def test_revoke_credentials_nonexistent_business(self):
        """Test revoking credentials for nonexistent business"""
        db = self.SessionLocal()
        try:
            import uuid
            fake_id = uuid.uuid4()
            
            with pytest.raises(ValueError, match="not found"):
                SecretsManager.revoke_gra_credentials(db, fake_id)
        finally:
            db.close()
    
    def test_validate_credentials_nonexistent_business(self):
        """Test validating credentials for nonexistent business"""
        db = self.SessionLocal()
        try:
            import uuid
            fake_id = uuid.uuid4()
            
            with pytest.raises(ValueError, match="not found"):
                SecretsManager.validate_gra_credentials(db, fake_id)
        finally:
            db.close()
    
    def test_get_metadata_nonexistent_business(self):
        """Test getting metadata for nonexistent business"""
        db = self.SessionLocal()
        try:
            import uuid
            fake_id = uuid.uuid4()
            
            with pytest.raises(ValueError, match="not found"):
                SecretsManager.get_credential_metadata(db, fake_id)
        finally:
            db.close()


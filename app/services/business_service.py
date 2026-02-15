"""Business management service"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from typing import Optional
import uuid

from app.models.models import Business
from app.services.api_key_service import APIKeyService
from app.utils.encryption import encryption_manager
from app.logger import logger


class BusinessService:
    """Service for managing business registrations and API credentials"""
    
    @staticmethod
    def create_business(
        db: Session,
        business_name: str,
        gra_tin: str,
        gra_company_name: str,
        gra_security_key: str
    ) -> tuple[Business, str]:
        """
        Create a new business and generate API credentials.
        
        Args:
            db: Database session
            business_name: Name of the business
            gra_tin: GRA TIN number
            gra_company_name: GRA company name
            gra_security_key: GRA security key
            
        Returns:
            tuple[Business, str]: Created business object and plain API secret
            
        Raises:
            IntegrityError: If business with same TIN already exists
        """
        try:
            # Generate API credentials
            api_key, api_secret = APIKeyService.generate_credentials()
            hashed_secret = APIKeyService.hash_api_secret(api_secret)
            
            # Encrypt sensitive GRA data
            encrypted_tin = encryption_manager.encrypt(gra_tin)
            encrypted_company_name = encryption_manager.encrypt(gra_company_name)
            encrypted_security_key = encryption_manager.encrypt(gra_security_key)
            
            # Create business record
            business = Business(
                id=uuid.uuid4(),
                name=business_name,
                api_key=api_key,
                api_secret=hashed_secret,
                gra_tin=encrypted_tin,
                gra_company_name=encrypted_company_name,
                gra_security_key=encrypted_security_key,
                status="active"
            )
            
            db.add(business)
            db.commit()
            db.refresh(business)
            
            logger.info(f"Business created: {business.id} - {business_name}")
            
            # Return business and plain API secret (only shown once)
            return business, api_secret
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Failed to create business: {str(e)}")
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating business: {str(e)}")
            raise
    
    @staticmethod
    def get_business_by_api_key(db: Session, api_key: str) -> Optional[Business]:
        """
        Retrieve business by API key.
        
        Args:
            db: Database session
            api_key: API key to search for
            
        Returns:
            Business object if found, None otherwise
        """
        return db.query(Business).filter(Business.api_key == api_key).first()
    
    @staticmethod
    def get_business_by_id(db: Session, business_id: UUID) -> Optional[Business]:
        """
        Retrieve business by ID.
        
        Args:
            db: Database session
            business_id: Business ID
            
        Returns:
            Business object if found, None otherwise
        """
        return db.query(Business).filter(Business.id == business_id).first()
    
    @staticmethod
    def verify_api_credentials(db: Session, api_key: str, api_secret: str) -> Optional[Business]:
        """
        Verify API credentials and return business if valid.
        
        Args:
            db: Database session
            api_key: API key
            api_secret: Plain text API secret
            
        Returns:
            Business object if credentials are valid, None otherwise
        """
        business = BusinessService.get_business_by_api_key(db, api_key)
        if not business:
            return None
        
        if not APIKeyService.verify_api_secret(api_secret, business.api_secret):
            return None
        
        return business
    
    @staticmethod
    def deactivate_business(db: Session, business_id: UUID) -> Business:
        """
        Deactivate a business.
        
        Args:
            db: Database session
            business_id: Business ID to deactivate
            
        Returns:
            Updated business object
        """
        business = BusinessService.get_business_by_id(db, business_id)
        if not business:
            raise ValueError(f"Business {business_id} not found")
        
        business.status = "inactive"
        db.commit()
        db.refresh(business)
        
        logger.info(f"Business deactivated: {business_id}")
        return business
    
    @staticmethod
    def update_gra_credentials(
        db: Session,
        business_id: UUID,
        gra_tin: str,
        gra_company_name: str,
        gra_security_key: str
    ) -> Business:
        """
        Update GRA credentials for a business.
        
        Args:
            db: Database session
            business_id: Business ID
            gra_tin: New GRA TIN
            gra_company_name: New GRA company name
            gra_security_key: New GRA security key
            
        Returns:
            Updated business object
            
        Raises:
            ValueError: If business not found
        """
        business = BusinessService.get_business_by_id(db, business_id)
        if not business:
            raise ValueError(f"Business {business_id} not found")
        
        try:
            # Encrypt new credentials
            business.gra_tin = encryption_manager.encrypt(gra_tin)
            business.gra_company_name = encryption_manager.encrypt(gra_company_name)
            business.gra_security_key = encryption_manager.encrypt(gra_security_key)
            
            db.commit()
            db.refresh(business)
            
            logger.info(f"GRA credentials updated for business: {business_id}")
            return business
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update GRA credentials: {str(e)}")
            raise
    
    @staticmethod
    def get_decrypted_gra_credentials(db: Session, business_id: UUID) -> dict:
        """
        Get decrypted GRA credentials for a business.
        
        Args:
            db: Database session
            business_id: Business ID
            
        Returns:
            Dictionary with decrypted credentials
            
        Raises:
            ValueError: If business not found or decryption fails
        """
        business = BusinessService.get_business_by_id(db, business_id)
        if not business:
            raise ValueError(f"Business {business_id} not found")
        
        try:
            return business.get_decrypted_gra_credentials()
        except Exception as e:
            logger.error(f"Failed to decrypt GRA credentials: {str(e)}")
            raise

"""Secrets management service for GRA credentials"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import os

from app.models.models import Business
from app.utils.encryption import encryption_manager
from app.logger import logger
from app.config import settings


class SecretsManager:
    """
    Manages secure storage and retrieval of GRA credentials.
    
    Features:
    - Encrypted credential storage
    - Credential versioning
    - Audit trail for credential access
    - Key rotation support
    - Credential revocation
    """
    
    @staticmethod
    def store_gra_credentials(
        db: Session,
        business_id: UUID,
        gra_tin: str,
        gra_company_name: str,
        gra_security_key: str,
        version: int = 1
    ) -> Dict[str, Any]:
        """
        Store GRA credentials securely with versioning.
        
        Args:
            db: Database session
            business_id: Business ID
            gra_tin: GRA TIN number
            gra_company_name: GRA company name
            gra_security_key: GRA security key
            version: Credential version (for rotation tracking)
            
        Returns:
            Dictionary with credential metadata
            
        Raises:
            ValueError: If business not found or validation fails
        """
        try:
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business:
                raise ValueError(f"Business {business_id} not found")
            
            # Validate credentials are not empty
            if not all([gra_tin, gra_company_name, gra_security_key]):
                raise ValueError("All GRA credentials must be provided")
            
            # Encrypt credentials
            encrypted_tin = encryption_manager.encrypt(gra_tin)
            encrypted_company_name = encryption_manager.encrypt(gra_company_name)
            encrypted_security_key = encryption_manager.encrypt(gra_security_key)
            
            # Update business credentials
            business.gra_tin = encrypted_tin
            business.gra_company_name = encrypted_company_name
            business.gra_security_key = encrypted_security_key
            
            db.commit()
            db.refresh(business)
            
            logger.info(
                f"GRA credentials stored for business {business_id} (version {version})",
                extra={
                    "business_id": str(business_id),
                    "version": version,
                    "action": "STORE_CREDENTIALS"
                }
            )
            
            return {
                "business_id": str(business_id),
                "version": version,
                "stored_at": datetime.utcnow().isoformat(),
                "status": "active"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store GRA credentials: {str(e)}")
            raise
    
    @staticmethod
    def retrieve_gra_credentials(
        db: Session,
        business_id: UUID,
        audit_log: bool = True
    ) -> Dict[str, str]:
        """
        Retrieve and decrypt GRA credentials.
        
        Args:
            db: Database session
            business_id: Business ID
            audit_log: Whether to log this access (default: True)
            
        Returns:
            Dictionary with decrypted credentials
            
        Raises:
            ValueError: If business not found or decryption fails
        """
        try:
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business:
                raise ValueError(f"Business {business_id} not found")
            
            if business.status != "active":
                raise ValueError(f"Business {business_id} is not active")
            
            # Decrypt credentials
            credentials = business.get_decrypted_gra_credentials()
            
            if audit_log:
                logger.info(
                    f"GRA credentials retrieved for business {business_id}",
                    extra={
                        "business_id": str(business_id),
                        "action": "RETRIEVE_CREDENTIALS"
                    }
                )
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to retrieve GRA credentials: {str(e)}")
            raise
    
    @staticmethod
    def rotate_gra_credentials(
        db: Session,
        business_id: UUID,
        new_gra_tin: str,
        new_gra_company_name: str,
        new_gra_security_key: str
    ) -> Dict[str, Any]:
        """
        Rotate GRA credentials (key rotation).
        
        Args:
            db: Database session
            business_id: Business ID
            new_gra_tin: New GRA TIN
            new_gra_company_name: New GRA company name
            new_gra_security_key: New GRA security key
            
        Returns:
            Dictionary with rotation metadata
            
        Raises:
            ValueError: If business not found or validation fails
        """
        try:
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business:
                raise ValueError(f"Business {business_id} not found")
            
            # Validate new credentials
            if not all([new_gra_tin, new_gra_company_name, new_gra_security_key]):
                raise ValueError("All new GRA credentials must be provided")
            
            # Store old credentials for audit trail (optional - can be extended)
            old_credentials = {
                "gra_tin": business.gra_tin,
                "gra_company_name": business.gra_company_name,
                "gra_security_key": business.gra_security_key,
                "rotated_at": datetime.utcnow().isoformat()
            }
            
            # Encrypt and store new credentials
            business.gra_tin = encryption_manager.encrypt(new_gra_tin)
            business.gra_company_name = encryption_manager.encrypt(new_gra_company_name)
            business.gra_security_key = encryption_manager.encrypt(new_gra_security_key)
            
            db.commit()
            db.refresh(business)
            
            logger.info(
                f"GRA credentials rotated for business {business_id}",
                extra={
                    "business_id": str(business_id),
                    "action": "ROTATE_CREDENTIALS"
                }
            )
            
            return {
                "business_id": str(business_id),
                "rotated_at": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to rotate GRA credentials: {str(e)}")
            raise
    
    @staticmethod
    def revoke_gra_credentials(
        db: Session,
        business_id: UUID,
        reason: str = "Manual revocation"
    ) -> Dict[str, Any]:
        """
        Revoke GRA credentials (deactivate business).
        
        Args:
            db: Database session
            business_id: Business ID
            reason: Reason for revocation
            
        Returns:
            Dictionary with revocation metadata
            
        Raises:
            ValueError: If business not found
        """
        try:
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business:
                raise ValueError(f"Business {business_id} not found")
            
            # Deactivate business
            business.status = "inactive"
            db.commit()
            db.refresh(business)
            
            logger.warning(
                f"GRA credentials revoked for business {business_id}: {reason}",
                extra={
                    "business_id": str(business_id),
                    "reason": reason,
                    "action": "REVOKE_CREDENTIALS"
                }
            )
            
            return {
                "business_id": str(business_id),
                "revoked_at": datetime.utcnow().isoformat(),
                "reason": reason,
                "status": "revoked"
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to revoke GRA credentials: {str(e)}")
            raise
    
    @staticmethod
    def validate_gra_credentials(
        db: Session,
        business_id: UUID
    ) -> Dict[str, Any]:
        """
        Validate that GRA credentials are properly stored and accessible.
        
        Args:
            db: Database session
            business_id: Business ID
            
        Returns:
            Dictionary with validation results
            
        Raises:
            ValueError: If business not found
        """
        try:
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business:
                raise ValueError(f"Business {business_id} not found")
            
            validation_results = {
                "business_id": str(business_id),
                "status": "valid",
                "checks": {}
            }
            
            # Check 1: Business is active
            validation_results["checks"]["business_active"] = business.status == "active"
            
            # Check 2: Credentials are encrypted
            validation_results["checks"]["gra_tin_encrypted"] = (
                business.gra_tin and business.gra_tin.startswith("gAAAAAB")
            )
            validation_results["checks"]["gra_company_name_encrypted"] = (
                business.gra_company_name and business.gra_company_name.startswith("gAAAAAB")
            )
            validation_results["checks"]["gra_security_key_encrypted"] = (
                business.gra_security_key and business.gra_security_key.startswith("gAAAAAB")
            )
            
            # Check 3: Credentials can be decrypted
            try:
                credentials = business.get_decrypted_gra_credentials()
                validation_results["checks"]["credentials_decryptable"] = True
                validation_results["checks"]["all_credentials_present"] = all([
                    credentials.get("gra_tin"),
                    credentials.get("gra_company_name"),
                    credentials.get("gra_security_key")
                ])
            except Exception as e:
                validation_results["checks"]["credentials_decryptable"] = False
                validation_results["checks"]["all_credentials_present"] = False
                validation_results["status"] = "invalid"
                logger.error(f"Credential validation failed: {str(e)}")
            
            # Overall status
            all_checks_passed = all(validation_results["checks"].values())
            validation_results["status"] = "valid" if all_checks_passed else "invalid"
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Failed to validate GRA credentials: {str(e)}")
            raise
    
    @staticmethod
    def get_credential_metadata(
        db: Session,
        business_id: UUID
    ) -> Dict[str, Any]:
        """
        Get metadata about stored credentials (without exposing them).
        
        Args:
            db: Database session
            business_id: Business ID
            
        Returns:
            Dictionary with credential metadata
            
        Raises:
            ValueError: If business not found
        """
        try:
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business:
                raise ValueError(f"Business {business_id} not found")
            
            return {
                "business_id": str(business_id),
                "business_name": business.name,
                "status": business.status,
                "credentials_stored": all([
                    business.gra_tin,
                    business.gra_company_name,
                    business.gra_security_key
                ]),
                "credentials_encrypted": all([
                    business.gra_tin.startswith("gAAAAAB") if business.gra_tin else False,
                    business.gra_company_name.startswith("gAAAAAB") if business.gra_company_name else False,
                    business.gra_security_key.startswith("gAAAAAB") if business.gra_security_key else False
                ]),
                "created_at": business.created_at.isoformat() if business.created_at else None,
                "updated_at": business.updated_at.isoformat() if business.updated_at else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get credential metadata: {str(e)}")
            raise

"""Encryption utilities for sensitive data"""
from cryptography.fernet import Fernet, InvalidToken
from app.config import settings
import base64
import hashlib
from typing import Optional
from app.logger import logger


class EncryptionManager:
    """Manages encryption and decryption of sensitive data using AES-256 via Fernet"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption manager with key from settings or provided key.
        
        Args:
            encryption_key: Optional encryption key. If not provided, uses settings.ENCRYPTION_KEY
            
        Raises:
            ValueError: If encryption key is invalid or too short
        """
        key_source = encryption_key or settings.ENCRYPTION_KEY
        
        if not key_source:
            raise ValueError("ENCRYPTION_KEY must be set in configuration")
        
        # Derive a proper Fernet key from the provided key
        self.cipher = self._initialize_cipher(key_source)
    
    @staticmethod
    def _initialize_cipher(key_source: str) -> Fernet:
        """
        Initialize Fernet cipher with proper key derivation.
        
        Args:
            key_source: Raw key source string
            
        Returns:
            Fernet cipher instance
            
        Raises:
            ValueError: If key derivation fails
        """
        try:
            # Use SHA256 to derive a 32-byte key from the source
            key_bytes = hashlib.sha256(key_source.encode()).digest()
            # Encode to base64 for Fernet
            fernet_key = base64.urlsafe_b64encode(key_bytes)
            return Fernet(fernet_key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption cipher: {str(e)}")
            raise ValueError(f"Invalid encryption key: {str(e)}")
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt a string using AES-256.
        
        Args:
            data: Plain text string to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
            
        Raises:
            ValueError: If encryption fails
        """
        try:
            if not data:
                raise ValueError("Cannot encrypt empty data")
            
            encrypted_bytes = self.cipher.encrypt(data.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise ValueError(f"Encryption failed: {str(e)}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a string using AES-256.
        
        Args:
            encrypted_data: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted plain text string
            
        Raises:
            ValueError: If decryption fails or data is corrupted
        """
        try:
            if not encrypted_data:
                raise ValueError("Cannot decrypt empty data")
            
            decrypted_bytes = self.cipher.decrypt(encrypted_data.encode())
            return decrypted_bytes.decode()
        except InvalidToken:
            logger.error("Decryption failed: Invalid token or corrupted data")
            raise ValueError("Decryption failed: Invalid token or corrupted data")
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def is_encrypted(self, data: str) -> bool:
        """
        Check if a string appears to be encrypted (basic check).
        
        Args:
            data: String to check
            
        Returns:
            True if string appears to be encrypted, False otherwise
        """
        try:
            # Fernet tokens start with 'gAAAAAB'
            return data.startswith('gAAAAAB')
        except Exception:
            return False


# Create global encryption manager instance
try:
    encryption_manager = EncryptionManager()
except ValueError as e:
    logger.error(f"Failed to initialize global encryption manager: {str(e)}")
    # Create a dummy manager that will fail at runtime if used
    encryption_manager = None

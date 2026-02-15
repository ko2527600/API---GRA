"""API Key generation and management service"""
import secrets
import string
import hashlib
from typing import Tuple


class APIKeyService:
    """Service for generating and managing API keys"""
    
    # API Key format: 32 characters (alphanumeric)
    API_KEY_LENGTH = 32
    # API Secret format: 32 characters (alphanumeric) - reduced for bcrypt compatibility
    API_SECRET_LENGTH = 32
    
    @staticmethod
    def generate_api_key() -> str:
        """
        Generate a unique API key.
        
        Returns:
            str: A 32-character alphanumeric API key
        """
        characters = string.ascii_letters + string.digits
        api_key = ''.join(secrets.choice(characters) for _ in range(APIKeyService.API_KEY_LENGTH))
        return api_key
    
    @staticmethod
    def generate_api_secret() -> str:
        """
        Generate a unique API secret.
        
        Returns:
            str: A 64-character alphanumeric API secret
        """
        characters = string.ascii_letters + string.digits
        api_secret = ''.join(secrets.choice(characters) for _ in range(APIKeyService.API_SECRET_LENGTH))
        return api_secret
    
    @staticmethod
    def generate_credentials() -> Tuple[str, str]:
        """
        Generate both API key and API secret.
        
        Returns:
            Tuple[str, str]: (api_key, api_secret)
        """
        api_key = APIKeyService.generate_api_key()
        api_secret = APIKeyService.generate_api_secret()
        return api_key, api_secret
    
    @staticmethod
    def hash_api_secret(api_secret: str) -> str:
        """
        Hash an API secret using SHA256.
        
        Args:
            api_secret: The plain text API secret
            
        Returns:
            str: The hashed API secret (hex format)
        """
        return hashlib.sha256(api_secret.encode()).hexdigest()
    
    @staticmethod
    def verify_api_secret(plain_secret: str, hashed_secret: str) -> bool:
        """
        Verify a plain text API secret against a hashed secret.
        
        Args:
            plain_secret: The plain text API secret
            hashed_secret: The hashed API secret from database
            
        Returns:
            bool: True if secrets match, False otherwise
        """
        return hashlib.sha256(plain_secret.encode()).hexdigest() == hashed_secret

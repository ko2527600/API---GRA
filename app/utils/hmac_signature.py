"""HMAC signature generation and verification utilities"""
import hmac
import hashlib
from typing import Optional
from datetime import datetime, timedelta
import json


class HMACSignatureManager:
    """Manages HMAC-SHA256 signature generation and verification"""
    
    # Signature validity window in seconds (5 minutes)
    SIGNATURE_VALIDITY_WINDOW = 300
    
    @staticmethod
    def generate_body_hash(body: bytes) -> str:
        """
        Generate SHA256 hash of request body.
        
        Args:
            body: Request body as bytes
            
        Returns:
            str: Hex-encoded SHA256 hash of the body
        """
        if not body:
            body = b""
        return hashlib.sha256(body).hexdigest()
    
    @staticmethod
    def generate_signature_message(
        method: str,
        path: str,
        timestamp: str,
        body_hash: str
    ) -> str:
        """
        Generate the message to be signed.
        
        Format: <request_method>|<request_path>|<timestamp>|<request_body_hash>
        
        Args:
            method: HTTP method (GET, POST, etc)
            path: Request path (e.g., /api/v1/invoices/submit)
            timestamp: ISO format timestamp
            body_hash: SHA256 hash of request body
            
        Returns:
            str: Message to be signed
        """
        return f"{method}|{path}|{timestamp}|{body_hash}"
    
    @staticmethod
    def generate_signature(api_secret: str, message: str) -> str:
        """
        Generate HMAC-SHA256 signature.
        
        Args:
            api_secret: The API secret key
            message: The message to sign
            
        Returns:
            str: Hex-encoded HMAC-SHA256 signature
        """
        signature = hmac.new(
            key=api_secret.encode(),
            msg=message.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        return signature
    
    @staticmethod
    def verify_signature(
        api_secret: str,
        message: str,
        provided_signature: str
    ) -> bool:
        """
        Verify HMAC-SHA256 signature.
        
        Uses constant-time comparison to prevent timing attacks.
        
        Args:
            api_secret: The API secret key
            message: The message that was signed
            provided_signature: The signature to verify
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        expected_signature = HMACSignatureManager.generate_signature(api_secret, message)
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, provided_signature)
    
    @staticmethod
    def verify_timestamp(timestamp_str: str, validity_window: int = SIGNATURE_VALIDITY_WINDOW) -> bool:
        """
        Verify that timestamp is within acceptable window.
        
        Prevents replay attacks by ensuring signatures are recent.
        
        Args:
            timestamp_str: ISO format timestamp string
            validity_window: Validity window in seconds (default 5 minutes)
            
        Returns:
            bool: True if timestamp is within validity window, False otherwise
        """
        try:
            # Parse ISO format timestamp
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            now = datetime.utcnow().replace(tzinfo=timestamp.tzinfo) if timestamp.tzinfo else datetime.utcnow()
            
            # Check if timestamp is not in the future and not too old
            time_diff = abs((now - timestamp).total_seconds())
            return time_diff <= validity_window
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def create_signature_context(
        method: str,
        path: str,
        body: bytes,
        timestamp: Optional[str] = None
    ) -> dict:
        """
        Create a complete signature context for verification.
        
        Args:
            method: HTTP method
            path: Request path
            body: Request body as bytes
            timestamp: ISO format timestamp (uses current time if not provided)
            
        Returns:
            dict: Signature context with message and body_hash
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat() + "Z"
        
        body_hash = HMACSignatureManager.generate_body_hash(body)
        message = HMACSignatureManager.generate_signature_message(method, path, timestamp, body_hash)
        
        return {
            "timestamp": timestamp,
            "body_hash": body_hash,
            "message": message
        }

"""Webhook signature verification utilities"""
import hmac
import hashlib
import json
from typing import Dict, Any, Optional


class WebhookSignatureVerifier:
    """Verifies webhook signatures to ensure authenticity"""
    
    SIGNATURE_HEADER = "X-Webhook-Signature"
    
    @staticmethod
    def generate_signature(
        payload: Dict[str, Any],
        webhook_secret: str,
    ) -> str:
        """
        Generate HMAC-SHA256 signature for webhook payload.
        
        This matches the signature generation on the server side.
        
        Args:
            payload: Webhook payload dictionary
            webhook_secret: Webhook secret for HMAC
            
        Returns:
            str: Hex-encoded HMAC-SHA256 signature
        """
        # Convert payload to JSON with sorted keys for consistency
        payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            key=webhook_secret.encode(),
            msg=payload_json.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return signature
    
    @staticmethod
    def verify_signature(
        payload: Dict[str, Any],
        webhook_secret: str,
        provided_signature: str,
    ) -> bool:
        """
        Verify webhook signature using constant-time comparison.
        
        This prevents timing attacks by using constant-time comparison.
        
        Args:
            payload: Webhook payload dictionary
            webhook_secret: Webhook secret for HMAC
            provided_signature: The signature from X-Webhook-Signature header
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        # Generate expected signature
        expected_signature = WebhookSignatureVerifier.generate_signature(
            payload,
            webhook_secret,
        )
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, provided_signature)
    
    @staticmethod
    def verify_webhook_request(
        payload: Dict[str, Any],
        webhook_secret: str,
        signature_header: str,
    ) -> bool:
        """
        Verify a complete webhook request.
        
        Args:
            payload: Webhook payload dictionary
            webhook_secret: Webhook secret for HMAC
            signature_header: Value from X-Webhook-Signature header
            
        Returns:
            bool: True if webhook is authentic, False otherwise
        """
        if not signature_header:
            return False
        
        return WebhookSignatureVerifier.verify_signature(
            payload,
            webhook_secret,
            signature_header,
        )
    
    @staticmethod
    def extract_signature_from_headers(headers: Dict[str, str]) -> Optional[str]:
        """
        Extract webhook signature from request headers.
        
        Args:
            headers: Request headers dictionary
            
        Returns:
            str: Signature value or None if not found
        """
        # Try different header name variations
        for header_name in [
            "X-Webhook-Signature",
            "x-webhook-signature",
            "X-Webhook-Sig",
            "x-webhook-sig",
        ]:
            if header_name in headers:
                return headers[header_name]
        
        return None

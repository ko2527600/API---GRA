"""Tests for HMAC signature generation and verification"""
import hmac
import hashlib
from datetime import datetime, timedelta
from app.utils.hmac_signature import HMACSignatureManager


class TestHMACSignatureManager:
    """Test suite for HMAC signature management"""
    
    def test_generate_body_hash_empty_body(self):
        """Test body hash generation with empty body"""
        body = b""
        expected_hash = hashlib.sha256(b"").hexdigest()
        result = HMACSignatureManager.generate_body_hash(body)
        assert result == expected_hash
    
    def test_generate_body_hash_with_content(self):
        """Test body hash generation with content"""
        body = b'{"key": "value"}'
        expected_hash = hashlib.sha256(body).hexdigest()
        result = HMACSignatureManager.generate_body_hash(body)
        assert result == expected_hash
    
    def test_generate_body_hash_consistency(self):
        """Test that same body produces same hash"""
        body = b'{"invoice": "INV-001"}'
        hash1 = HMACSignatureManager.generate_body_hash(body)
        hash2 = HMACSignatureManager.generate_body_hash(body)
        assert hash1 == hash2
    
    def test_generate_signature_message_format(self):
        """Test signature message format"""
        method = "POST"
        path = "/api/v1/invoices/submit"
        timestamp = "2026-02-10T10:00:00Z"
        body_hash = "abc123def456"
        
        result = HMACSignatureManager.generate_signature_message(
            method, path, timestamp, body_hash
        )
        
        expected = "POST|/api/v1/invoices/submit|2026-02-10T10:00:00Z|abc123def456"
        assert result == expected
    
    def test_generate_signature(self):
        """Test HMAC-SHA256 signature generation"""
        api_secret = "test-secret-key"
        message = "POST|/api/v1/invoices/submit|2026-02-10T10:00:00Z|abc123"
        
        result = HMACSignatureManager.generate_signature(api_secret, message)
        
        # Verify it matches manual calculation
        expected = hmac.new(
            key=api_secret.encode(),
            msg=message.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        assert result == expected
    
    def test_generate_signature_consistency(self):
        """Test that same inputs produce same signature"""
        api_secret = "test-secret"
        message = "GET|/api/v1/status|2026-02-10T10:00:00Z|hash123"
        
        sig1 = HMACSignatureManager.generate_signature(api_secret, message)
        sig2 = HMACSignatureManager.generate_signature(api_secret, message)
        
        assert sig1 == sig2
    
    def test_generate_signature_different_secrets(self):
        """Test that different secrets produce different signatures"""
        message = "POST|/api/v1/invoices/submit|2026-02-10T10:00:00Z|hash123"
        
        sig1 = HMACSignatureManager.generate_signature("secret1", message)
        sig2 = HMACSignatureManager.generate_signature("secret2", message)
        
        assert sig1 != sig2
    
    def test_generate_signature_different_messages(self):
        """Test that different messages produce different signatures"""
        api_secret = "test-secret"
        
        sig1 = HMACSignatureManager.generate_signature(api_secret, "message1")
        sig2 = HMACSignatureManager.generate_signature(api_secret, "message2")
        
        assert sig1 != sig2
    
    def test_verify_signature_valid(self):
        """Test verification of valid signature"""
        api_secret = "test-secret-key"
        message = "POST|/api/v1/invoices/submit|2026-02-10T10:00:00Z|abc123"
        
        signature = HMACSignatureManager.generate_signature(api_secret, message)
        result = HMACSignatureManager.verify_signature(api_secret, message, signature)
        
        assert result is True
    
    def test_verify_signature_invalid(self):
        """Test verification of invalid signature"""
        api_secret = "test-secret-key"
        message = "POST|/api/v1/invoices/submit|2026-02-10T10:00:00Z|abc123"
        invalid_signature = "invalid_signature_12345"
        
        result = HMACSignatureManager.verify_signature(api_secret, message, invalid_signature)
        
        assert result is False
    
    def test_verify_signature_wrong_secret(self):
        """Test verification with wrong secret"""
        message = "POST|/api/v1/invoices/submit|2026-02-10T10:00:00Z|abc123"
        
        signature = HMACSignatureManager.generate_signature("secret1", message)
        result = HMACSignatureManager.verify_signature("secret2", message, signature)
        
        assert result is False
    
    def test_verify_signature_tampered_message(self):
        """Test verification with tampered message"""
        api_secret = "test-secret"
        original_message = "POST|/api/v1/invoices/submit|2026-02-10T10:00:00Z|abc123"
        tampered_message = "POST|/api/v1/invoices/submit|2026-02-10T10:00:00Z|abc124"
        
        signature = HMACSignatureManager.generate_signature(api_secret, original_message)
        result = HMACSignatureManager.verify_signature(api_secret, tampered_message, signature)
        
        assert result is False
    
    def test_verify_timestamp_valid_current(self):
        """Test timestamp verification with current time"""
        current_timestamp = datetime.utcnow().isoformat() + "Z"
        result = HMACSignatureManager.verify_timestamp(current_timestamp)
        assert result is True
    
    def test_verify_timestamp_valid_recent(self):
        """Test timestamp verification with recent timestamp"""
        recent_timestamp = (datetime.utcnow() - timedelta(seconds=60)).isoformat() + "Z"
        result = HMACSignatureManager.verify_timestamp(recent_timestamp)
        assert result is True
    
    def test_verify_timestamp_invalid_too_old(self):
        """Test timestamp verification with old timestamp"""
        old_timestamp = (datetime.utcnow() - timedelta(seconds=400)).isoformat() + "Z"
        result = HMACSignatureManager.verify_timestamp(old_timestamp)
        assert result is False
    
    def test_verify_timestamp_invalid_future(self):
        """Test timestamp verification with future timestamp"""
        future_timestamp = (datetime.utcnow() + timedelta(seconds=400)).isoformat() + "Z"
        result = HMACSignatureManager.verify_timestamp(future_timestamp)
        assert result is False
    
    def test_verify_timestamp_invalid_format(self):
        """Test timestamp verification with invalid format"""
        result = HMACSignatureManager.verify_timestamp("invalid-timestamp")
        assert result is False
    
    def test_verify_timestamp_custom_window(self):
        """Test timestamp verification with custom validity window"""
        # Timestamp 100 seconds old
        old_timestamp = (datetime.utcnow() - timedelta(seconds=100)).isoformat() + "Z"
        
        # Should fail with default 300 second window
        assert HMACSignatureManager.verify_timestamp(old_timestamp, validity_window=300) is True
        
        # Should fail with 50 second window
        assert HMACSignatureManager.verify_timestamp(old_timestamp, validity_window=50) is False
    
    def test_create_signature_context_with_timestamp(self):
        """Test signature context creation with provided timestamp"""
        method = "POST"
        path = "/api/v1/invoices/submit"
        body = b'{"invoice": "INV-001"}'
        timestamp = "2026-02-10T10:00:00Z"
        
        context = HMACSignatureManager.create_signature_context(
            method, path, body, timestamp
        )
        
        assert context["timestamp"] == timestamp
        assert "body_hash" in context
        assert "message" in context
        assert context["body_hash"] == hashlib.sha256(body).hexdigest()
    
    def test_create_signature_context_without_timestamp(self):
        """Test signature context creation without timestamp (uses current time)"""
        method = "GET"
        path = "/api/v1/status"
        body = b""
        
        context = HMACSignatureManager.create_signature_context(method, path, body)
        
        assert "timestamp" in context
        assert "body_hash" in context
        assert "message" in context
        # Verify timestamp is recent
        timestamp = datetime.fromisoformat(context["timestamp"].replace('Z', '+00:00'))
        now = datetime.utcnow().replace(tzinfo=timestamp.tzinfo) if timestamp.tzinfo else datetime.utcnow()
        time_diff = abs((now - timestamp).total_seconds())
        assert time_diff < 5  # Should be within 5 seconds
    
    def test_create_signature_context_message_format(self):
        """Test that signature context message has correct format"""
        method = "POST"
        path = "/api/v1/refunds/submit"
        body = b'{"refund": "REF-001"}'
        timestamp = "2026-02-10T10:00:00Z"
        
        context = HMACSignatureManager.create_signature_context(
            method, path, body, timestamp
        )
        
        # Message should be: method|path|timestamp|body_hash
        parts = context["message"].split("|")
        assert len(parts) == 4
        assert parts[0] == method
        assert parts[1] == path
        assert parts[2] == timestamp
        assert parts[3] == context["body_hash"]
    
    def test_end_to_end_signature_flow(self):
        """Test complete signature generation and verification flow"""
        api_secret = "my-api-secret-key"
        method = "POST"
        path = "/api/v1/invoices/submit"
        body = b'{"invoice_num": "INV-2026-001", "total_amount": 1000}'
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Generate signature context
        context = HMACSignatureManager.create_signature_context(
            method, path, body, timestamp
        )
        
        # Generate signature
        signature = HMACSignatureManager.generate_signature(
            api_secret, context["message"]
        )
        
        # Verify signature
        is_valid = HMACSignatureManager.verify_signature(
            api_secret, context["message"], signature
        )
        
        assert is_valid is True
        
        # Verify timestamp
        is_timestamp_valid = HMACSignatureManager.verify_timestamp(context["timestamp"])
        assert is_timestamp_valid is True

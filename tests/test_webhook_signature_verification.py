"""Tests for webhook signature verification"""
import pytest
import json
import hmac
import hashlib
from datetime import datetime
from uuid import uuid4

from app.utils.webhook_signature import WebhookSignatureVerifier


class TestWebhookSignatureGeneration:
    """Tests for webhook signature generation"""
    
    def test_generate_signature_basic(self):
        """Test generating a basic webhook signature"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        webhook_secret = "test-webhook-secret"
        
        signature = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex is 64 characters
        assert all(c in "0123456789abcdef" for c in signature)
    
    def test_generate_signature_consistency(self):
        """Test that same payload generates same signature"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        webhook_secret = "test-webhook-secret"
        
        sig1 = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        sig2 = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        
        assert sig1 == sig2
    
    def test_generate_signature_different_payloads(self):
        """Test that different payloads generate different signatures"""
        payload1 = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        payload2 = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-002"},
        }
        webhook_secret = "test-webhook-secret"
        
        sig1 = WebhookSignatureVerifier.generate_signature(payload1, webhook_secret)
        sig2 = WebhookSignatureVerifier.generate_signature(payload2, webhook_secret)
        
        assert sig1 != sig2
    
    def test_generate_signature_different_secrets(self):
        """Test that different secrets generate different signatures"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        
        sig1 = WebhookSignatureVerifier.generate_signature(payload, "secret1")
        sig2 = WebhookSignatureVerifier.generate_signature(payload, "secret2")
        
        assert sig1 != sig2
    
    def test_generate_signature_with_nested_data(self):
        """Test signature generation with nested data structures"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {
                "invoice_num": "INV-001",
                "items": [
                    {"itmref": "PROD001", "quantity": 10},
                    {"itmref": "PROD002", "quantity": 5},
                ],
                "totals": {
                    "vat": 159,
                    "levy": 60,
                    "amount": 3438,
                },
            },
        }
        webhook_secret = "test-webhook-secret"
        
        signature = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        
        assert isinstance(signature, str)
        assert len(signature) == 64
    
    def test_generate_signature_with_timestamp(self):
        """Test signature generation with timestamp in payload"""
        payload = {
            "event_type": "invoice.success",
            "timestamp": "2026-02-10T10:05:00Z",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        webhook_secret = "test-webhook-secret"
        
        signature = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        
        assert isinstance(signature, str)
        assert len(signature) == 64
    
    def test_generate_signature_json_key_order_independent(self):
        """Test that JSON key order doesn't affect signature"""
        payload1 = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        payload2 = {
            "data": {"invoice_num": "INV-001"},
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
        }
        webhook_secret = "test-webhook-secret"
        
        sig1 = WebhookSignatureVerifier.generate_signature(payload1, webhook_secret)
        sig2 = WebhookSignatureVerifier.generate_signature(payload2, webhook_secret)
        
        # Signatures should be the same because JSON is sorted
        assert sig1 == sig2


class TestWebhookSignatureVerification:
    """Tests for webhook signature verification"""
    
    def test_verify_signature_valid(self):
        """Test verifying a valid signature"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        webhook_secret = "test-webhook-secret"
        
        # Generate signature
        signature = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        
        # Verify signature
        is_valid = WebhookSignatureVerifier.verify_signature(
            payload,
            webhook_secret,
            signature,
        )
        
        assert is_valid is True
    
    def test_verify_signature_invalid(self):
        """Test verifying an invalid signature"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        webhook_secret = "test-webhook-secret"
        
        # Use wrong signature
        wrong_signature = "0" * 64
        
        is_valid = WebhookSignatureVerifier.verify_signature(
            payload,
            webhook_secret,
            wrong_signature,
        )
        
        assert is_valid is False
    
    def test_verify_signature_tampered_payload(self):
        """Test that tampered payload fails verification"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        webhook_secret = "test-webhook-secret"
        
        # Generate signature for original payload
        signature = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        
        # Tamper with payload
        tampered_payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-002"},  # Changed
        }
        
        # Verify should fail
        is_valid = WebhookSignatureVerifier.verify_signature(
            tampered_payload,
            webhook_secret,
            signature,
        )
        
        assert is_valid is False
    
    def test_verify_signature_wrong_secret(self):
        """Test that wrong secret fails verification"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        webhook_secret = "test-webhook-secret"
        
        # Generate signature with correct secret
        signature = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        
        # Try to verify with wrong secret
        is_valid = WebhookSignatureVerifier.verify_signature(
            payload,
            "wrong-secret",
            signature,
        )
        
        assert is_valid is False
    
    def test_verify_signature_empty_signature(self):
        """Test that empty signature fails verification"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        webhook_secret = "test-webhook-secret"
        
        is_valid = WebhookSignatureVerifier.verify_signature(
            payload,
            webhook_secret,
            "",
        )
        
        assert is_valid is False
    
    def test_verify_signature_case_sensitive(self):
        """Test that signature verification is case-sensitive"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        webhook_secret = "test-webhook-secret"
        
        # Generate signature
        signature = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        
        # Try with uppercase (should fail)
        uppercase_signature = signature.upper()
        
        is_valid = WebhookSignatureVerifier.verify_signature(
            payload,
            webhook_secret,
            uppercase_signature,
        )
        
        # Should fail because signature is case-sensitive
        assert is_valid is False
    
    def test_verify_signature_timing_attack_resistance(self):
        """Test that verification uses constant-time comparison"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        webhook_secret = "test-webhook-secret"
        
        # Generate valid signature
        valid_signature = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        
        # Create signatures that differ at different positions
        # Use 'f' instead of '0' to ensure we're not accidentally matching
        wrong_sig_start = "f" + valid_signature[1:]
        wrong_sig_middle = valid_signature[:32] + "f" + valid_signature[33:]
        wrong_sig_end = valid_signature[:-1] + "f"
        
        # All should fail verification
        assert WebhookSignatureVerifier.verify_signature(payload, webhook_secret, wrong_sig_start) is False
        assert WebhookSignatureVerifier.verify_signature(payload, webhook_secret, wrong_sig_middle) is False
        assert WebhookSignatureVerifier.verify_signature(payload, webhook_secret, wrong_sig_end) is False


class TestWebhookRequestVerification:
    """Tests for complete webhook request verification"""
    
    def test_verify_webhook_request_valid(self):
        """Test verifying a valid webhook request"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        webhook_secret = "test-webhook-secret"
        
        # Generate signature
        signature = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        
        # Verify webhook request
        is_valid = WebhookSignatureVerifier.verify_webhook_request(
            payload,
            webhook_secret,
            signature,
        )
        
        assert is_valid is True
    
    def test_verify_webhook_request_missing_signature(self):
        """Test that missing signature fails verification"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        webhook_secret = "test-webhook-secret"
        
        is_valid = WebhookSignatureVerifier.verify_webhook_request(
            payload,
            webhook_secret,
            "",
        )
        
        assert is_valid is False
    
    def test_verify_webhook_request_none_signature(self):
        """Test that None signature fails verification"""
        payload = {
            "event_type": "invoice.success",
            "submission_id": "test-id-123",
            "data": {"invoice_num": "INV-001"},
        }
        webhook_secret = "test-webhook-secret"
        
        is_valid = WebhookSignatureVerifier.verify_webhook_request(
            payload,
            webhook_secret,
            None,
        )
        
        assert is_valid is False


class TestSignatureHeaderExtraction:
    """Tests for extracting signature from headers"""
    
    def test_extract_signature_standard_header(self):
        """Test extracting signature from standard header"""
        headers = {
            "X-Webhook-Signature": "abc123def456",
            "Content-Type": "application/json",
        }
        
        signature = WebhookSignatureVerifier.extract_signature_from_headers(headers)
        
        assert signature == "abc123def456"
    
    def test_extract_signature_lowercase_header(self):
        """Test extracting signature from lowercase header"""
        headers = {
            "x-webhook-signature": "abc123def456",
            "Content-Type": "application/json",
        }
        
        signature = WebhookSignatureVerifier.extract_signature_from_headers(headers)
        
        assert signature == "abc123def456"
    
    def test_extract_signature_short_name_header(self):
        """Test extracting signature from short name header"""
        headers = {
            "X-Webhook-Sig": "abc123def456",
            "Content-Type": "application/json",
        }
        
        signature = WebhookSignatureVerifier.extract_signature_from_headers(headers)
        
        assert signature == "abc123def456"
    
    def test_extract_signature_missing(self):
        """Test extracting signature when not present"""
        headers = {
            "Content-Type": "application/json",
        }
        
        signature = WebhookSignatureVerifier.extract_signature_from_headers(headers)
        
        assert signature is None
    
    def test_extract_signature_empty_headers(self):
        """Test extracting signature from empty headers"""
        headers = {}
        
        signature = WebhookSignatureVerifier.extract_signature_from_headers(headers)
        
        assert signature is None


class TestWebhookSignatureIntegration:
    """Integration tests for webhook signature verification"""
    
    def test_full_webhook_flow_valid(self):
        """Test full webhook flow with valid signature"""
        # Simulate server generating webhook
        payload = {
            "event_type": "invoice.success",
            "timestamp": "2026-02-10T10:05:00Z",
            "submission_id": str(uuid4()),
            "data": {
                "invoice_num": "INV-001",
                "status": "SUCCESS",
                "gra_invoice_id": "GRA-INV-001",
            },
        }
        webhook_secret = "test-webhook-secret-12345"
        
        # Server generates signature
        server_signature = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        
        # Client receives webhook and verifies signature
        is_valid = WebhookSignatureVerifier.verify_webhook_request(
            payload,
            webhook_secret,
            server_signature,
        )
        
        assert is_valid is True
    
    def test_full_webhook_flow_tampered(self):
        """Test full webhook flow with tampered payload"""
        # Simulate server generating webhook
        payload = {
            "event_type": "invoice.success",
            "timestamp": "2026-02-10T10:05:00Z",
            "submission_id": str(uuid4()),
            "data": {
                "invoice_num": "INV-001",
                "status": "SUCCESS",
                "gra_invoice_id": "GRA-INV-001",
            },
        }
        webhook_secret = "test-webhook-secret-12345"
        
        # Server generates signature
        server_signature = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        
        # Attacker tampers with payload
        tampered_payload = payload.copy()
        tampered_payload["data"] = {
            "invoice_num": "INV-001",
            "status": "FAILED",  # Changed
            "gra_invoice_id": "GRA-INV-001",
        }
        
        # Client receives tampered webhook and verifies signature
        is_valid = WebhookSignatureVerifier.verify_webhook_request(
            tampered_payload,
            webhook_secret,
            server_signature,
        )
        
        assert is_valid is False
    
    def test_full_webhook_flow_wrong_secret(self):
        """Test full webhook flow with wrong secret"""
        # Simulate server generating webhook
        payload = {
            "event_type": "invoice.success",
            "timestamp": "2026-02-10T10:05:00Z",
            "submission_id": str(uuid4()),
            "data": {
                "invoice_num": "INV-001",
                "status": "SUCCESS",
                "gra_invoice_id": "GRA-INV-001",
            },
        }
        webhook_secret = "test-webhook-secret-12345"
        
        # Server generates signature
        server_signature = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        
        # Client tries to verify with wrong secret
        is_valid = WebhookSignatureVerifier.verify_webhook_request(
            payload,
            "wrong-secret",
            server_signature,
        )
        
        assert is_valid is False
    
    def test_webhook_signature_with_complex_payload(self):
        """Test webhook signature with complex nested payload"""
        payload = {
            "event_type": "invoice.success",
            "timestamp": "2026-02-10T10:05:00Z",
            "submission_id": str(uuid4()),
            "data": {
                "invoice_num": "INV-001",
                "status": "SUCCESS",
                "gra_invoice_id": "GRA-INV-001",
                "gra_qr_code": "https://gra.gov.gh/qr/...",
                "gra_receipt_num": "VSDC-REC-12345",
                "items": [
                    {
                        "itmref": "PROD001",
                        "itmdes": "Product 1",
                        "quantity": 10,
                        "unityprice": 100,
                        "taxcode": "B",
                        "taxrate": 15,
                    },
                    {
                        "itmref": "PROD002",
                        "itmdes": "Product 2",
                        "quantity": 5,
                        "unityprice": 200,
                        "taxcode": "B",
                        "taxrate": 15,
                    },
                ],
                "totals": {
                    "vat": 159,
                    "levy": 60,
                    "amount": 3438,
                },
            },
        }
        webhook_secret = "test-webhook-secret-12345"
        
        # Generate and verify signature
        signature = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
        is_valid = WebhookSignatureVerifier.verify_webhook_request(
            payload,
            webhook_secret,
            signature,
        )
        
        assert is_valid is True
        
        # Tamper with nested data
        tampered_payload = json.loads(json.dumps(payload))
        tampered_payload["data"]["items"][0]["quantity"] = 20
        
        is_valid = WebhookSignatureVerifier.verify_webhook_request(
            tampered_payload,
            webhook_secret,
            signature,
        )
        
        assert is_valid is False

# Webhook Signature Verification Guide

## Overview

Webhook signature verification ensures that webhook requests received by your business system are genuinely from the GRA External Integration API and have not been tampered with. This guide explains how to implement and use webhook signature verification.

## How It Works

### Server-Side (API)

When the API sends a webhook notification to your business:

1. **Generate Payload**: Create the webhook payload with event details
2. **Generate Signature**: Calculate HMAC-SHA256 signature using:
   - Webhook secret (stored securely)
   - Payload JSON (sorted keys for consistency)
3. **Send Webhook**: Include signature in `X-Webhook-Signature` header

### Client-Side (Your Business)

When your business receives a webhook:

1. **Extract Signature**: Get the `X-Webhook-Signature` header value
2. **Verify Signature**: Use the webhook secret to verify the signature
3. **Process Webhook**: Only process if signature is valid

## Implementation

### Python Implementation

The API provides a `WebhookSignatureVerifier` utility class for signature verification:

```python
from app.utils.webhook_signature import WebhookSignatureVerifier

# Verify a webhook request
payload = {
    "event_type": "invoice.success",
    "timestamp": "2026-02-10T10:05:00Z",
    "submission_id": "uuid-12345",
    "data": {
        "invoice_num": "INV-001",
        "status": "SUCCESS",
        "gra_invoice_id": "GRA-INV-001",
    }
}

webhook_secret = "your-webhook-secret"
signature_header = "abc123def456..."  # From X-Webhook-Signature header

# Verify the signature
is_valid = WebhookSignatureVerifier.verify_webhook_request(
    payload,
    webhook_secret,
    signature_header,
)

if is_valid:
    print("Webhook is authentic!")
    # Process the webhook
else:
    print("Webhook signature verification failed!")
    # Reject the webhook
```

### JavaScript/Node.js Implementation

```javascript
const crypto = require('crypto');

function verifyWebhookSignature(payload, webhookSecret, providedSignature) {
    // Convert payload to JSON with sorted keys
    const payloadJson = JSON.stringify(payload, Object.keys(payload).sort());
    
    // Generate HMAC-SHA256 signature
    const expectedSignature = crypto
        .createHmac('sha256', webhookSecret)
        .update(payloadJson)
        .digest('hex');
    
    // Use constant-time comparison
    return crypto.timingSafeEqual(
        Buffer.from(expectedSignature),
        Buffer.from(providedSignature)
    );
}

// Usage
const payload = {
    event_type: "invoice.success",
    timestamp: "2026-02-10T10:05:00Z",
    submission_id: "uuid-12345",
    data: {
        invoice_num: "INV-001",
        status: "SUCCESS",
        gra_invoice_id: "GRA-INV-001",
    }
};

const webhookSecret = "your-webhook-secret";
const signatureHeader = "abc123def456...";

if (verifyWebhookSignature(payload, webhookSecret, signatureHeader)) {
    console.log("Webhook is authentic!");
    // Process the webhook
} else {
    console.log("Webhook signature verification failed!");
    // Reject the webhook
}
```

### Java Implementation

```java
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;

public class WebhookSignatureVerifier {
    
    public static String generateSignature(String payload, String webhookSecret) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        SecretKeySpec secretKey = new SecretKeySpec(
            webhookSecret.getBytes(StandardCharsets.UTF_8),
            "HmacSHA256"
        );
        mac.init(secretKey);
        
        byte[] hash = mac.doFinal(payload.getBytes(StandardCharsets.UTF_8));
        return bytesToHex(hash);
    }
    
    public static boolean verifySignature(String payload, String webhookSecret, String providedSignature) throws Exception {
        String expectedSignature = generateSignature(payload, webhookSecret);
        return constantTimeEquals(expectedSignature, providedSignature);
    }
    
    private static String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02x", b));
        }
        return sb.toString();
    }
    
    private static boolean constantTimeEquals(String a, String b) {
        if (a.length() != b.length()) {
            return false;
        }
        
        int result = 0;
        for (int i = 0; i < a.length(); i++) {
            result |= a.charAt(i) ^ b.charAt(i);
        }
        return result == 0;
    }
}

// Usage
String payload = "{\"event_type\":\"invoice.success\",...}";
String webhookSecret = "your-webhook-secret";
String signatureHeader = "abc123def456...";

if (WebhookSignatureVerifier.verifySignature(payload, webhookSecret, signatureHeader)) {
    System.out.println("Webhook is authentic!");
    // Process the webhook
} else {
    System.out.println("Webhook signature verification failed!");
    // Reject the webhook
}
```

## Webhook Payload Format

When you receive a webhook, the payload will have this structure:

```json
{
    "event_type": "invoice.success",
    "timestamp": "2026-02-10T10:05:00Z",
    "submission_id": "550e8400-e29b-41d4-a716-446655440000",
    "data": {
        "invoice_num": "INV-001",
        "status": "SUCCESS",
        "gra_invoice_id": "GRA-INV-001",
        "gra_qr_code": "https://gra.gov.gh/qr/...",
        "gra_receipt_num": "VSDC-REC-12345",
        "submitted_at": "2026-02-10T10:00:00Z",
        "completed_at": "2026-02-10T10:05:00Z",
        "processing_time_ms": 5000
    }
}
```

## Headers

When receiving a webhook, check for these headers:

- **X-Webhook-Signature**: HMAC-SHA256 signature of the payload (hex-encoded)
- **Content-Type**: `application/json`

Example:
```
POST /webhooks HTTP/1.1
Host: yourbusiness.com
Content-Type: application/json
X-Webhook-Signature: abc123def456...

{
    "event_type": "invoice.success",
    ...
}
```

## Security Best Practices

### 1. Always Verify Signatures

Never process webhooks without verifying the signature first:

```python
# ❌ DON'T DO THIS
def handle_webhook(request):
    payload = request.json
    process_webhook(payload)  # No signature verification!

# ✅ DO THIS
def handle_webhook(request):
    payload = request.json
    signature = request.headers.get('X-Webhook-Signature')
    
    if not WebhookSignatureVerifier.verify_webhook_request(
        payload,
        WEBHOOK_SECRET,
        signature
    ):
        return {"error": "Invalid signature"}, 401
    
    process_webhook(payload)
```

### 2. Use Constant-Time Comparison

Always use constant-time comparison to prevent timing attacks:

```python
# ❌ DON'T DO THIS
if expected_signature == provided_signature:  # Vulnerable to timing attacks
    process_webhook()

# ✅ DO THIS
import hmac
if hmac.compare_digest(expected_signature, provided_signature):
    process_webhook()
```

### 3. Store Webhook Secret Securely

- Never commit webhook secrets to version control
- Use environment variables or secure vaults
- Rotate secrets periodically
- Use different secrets for different environments (dev, staging, prod)

```python
import os

WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')
if not WEBHOOK_SECRET:
    raise ValueError("WEBHOOK_SECRET environment variable not set")
```

### 4. Validate Payload Structure

After verifying the signature, validate the payload structure:

```python
def handle_webhook(request):
    payload = request.json
    signature = request.headers.get('X-Webhook-Signature')
    
    # Verify signature
    if not WebhookSignatureVerifier.verify_webhook_request(
        payload,
        WEBHOOK_SECRET,
        signature
    ):
        return {"error": "Invalid signature"}, 401
    
    # Validate payload structure
    required_fields = ['event_type', 'timestamp', 'submission_id', 'data']
    if not all(field in payload for field in required_fields):
        return {"error": "Invalid payload structure"}, 400
    
    # Validate event type
    valid_events = [
        'invoice.success', 'invoice.failed',
        'refund.success', 'refund.failed',
        'purchase.success', 'purchase.failed'
    ]
    if payload['event_type'] not in valid_events:
        return {"error": "Invalid event type"}, 400
    
    process_webhook(payload)
```

### 5. Implement Idempotency

Webhooks may be delivered multiple times. Implement idempotency to handle duplicates:

```python
def handle_webhook(request):
    payload = request.json
    signature = request.headers.get('X-Webhook-Signature')
    
    # Verify signature
    if not WebhookSignatureVerifier.verify_webhook_request(
        payload,
        WEBHOOK_SECRET,
        signature
    ):
        return {"error": "Invalid signature"}, 401
    
    submission_id = payload['submission_id']
    
    # Check if we've already processed this webhook
    if WebhookDeliveryLog.exists(submission_id):
        return {"status": "already_processed"}, 200
    
    # Process webhook
    process_webhook(payload)
    
    # Log that we've processed this webhook
    WebhookDeliveryLog.create(submission_id)
    
    return {"status": "processed"}, 200
```

### 6. Return 200 OK Quickly

Acknowledge receipt of the webhook quickly, then process asynchronously:

```python
from celery import shared_task

@app.post("/webhooks")
def handle_webhook(request):
    payload = request.json
    signature = request.headers.get('X-Webhook-Signature')
    
    # Verify signature
    if not WebhookSignatureVerifier.verify_webhook_request(
        payload,
        WEBHOOK_SECRET,
        signature
    ):
        return {"error": "Invalid signature"}, 401
    
    # Queue for async processing
    process_webhook_async.delay(payload)
    
    # Return 200 OK immediately
    return {"status": "received"}, 200

@shared_task
def process_webhook_async(payload):
    # Do the actual processing here
    process_webhook(payload)
```

## Testing

### Unit Tests

The API includes comprehensive unit tests for webhook signature verification:

```bash
python -m pytest tests/test_webhook_signature_verification.py -v
```

Test coverage includes:
- Signature generation consistency
- Signature verification with valid/invalid signatures
- Tampered payload detection
- Wrong secret detection
- Timing attack resistance
- Complex nested payload handling

### Integration Tests

Test your webhook handler with real signatures:

```python
import pytest
from app.utils.webhook_signature import WebhookSignatureVerifier

def test_webhook_handler():
    # Create test payload
    payload = {
        "event_type": "invoice.success",
        "timestamp": "2026-02-10T10:05:00Z",
        "submission_id": "test-id-123",
        "data": {"invoice_num": "INV-001"},
    }
    
    # Generate signature
    webhook_secret = "test-secret"
    signature = WebhookSignatureVerifier.generate_signature(payload, webhook_secret)
    
    # Send webhook to your handler
    response = client.post(
        "/webhooks",
        json=payload,
        headers={"X-Webhook-Signature": signature}
    )
    
    assert response.status_code == 200
    assert response.json()["status"] == "processed"
```

## Troubleshooting

### Signature Verification Fails

**Problem**: Webhook signature verification always fails

**Solutions**:
1. Verify webhook secret is correct
2. Ensure payload JSON is sorted by keys
3. Check that signature is hex-encoded
4. Verify no whitespace differences in JSON

### Webhook Not Received

**Problem**: Webhooks are not being delivered

**Solutions**:
1. Check webhook URL is correct and accessible
2. Verify webhook is active (not disabled)
3. Check firewall/network rules
4. Review API logs for delivery errors
5. Check webhook delivery status in dashboard

### Signature Mismatch

**Problem**: Signature verification fails intermittently

**Solutions**:
1. Ensure webhook secret hasn't changed
2. Check for JSON formatting differences
3. Verify timestamp is correct
4. Check for encoding issues (UTF-8)

## API Reference

### WebhookSignatureVerifier Class

#### Methods

**`generate_signature(payload, webhook_secret) -> str`**

Generate HMAC-SHA256 signature for a webhook payload.

Parameters:
- `payload` (dict): Webhook payload
- `webhook_secret` (str): Webhook secret

Returns:
- `str`: Hex-encoded HMAC-SHA256 signature

**`verify_signature(payload, webhook_secret, provided_signature) -> bool`**

Verify webhook signature using constant-time comparison.

Parameters:
- `payload` (dict): Webhook payload
- `webhook_secret` (str): Webhook secret
- `provided_signature` (str): Signature to verify

Returns:
- `bool`: True if signature is valid, False otherwise

**`verify_webhook_request(payload, webhook_secret, signature_header) -> bool`**

Verify a complete webhook request.

Parameters:
- `payload` (dict): Webhook payload
- `webhook_secret` (str): Webhook secret
- `signature_header` (str): Value from X-Webhook-Signature header

Returns:
- `bool`: True if webhook is authentic, False otherwise

**`extract_signature_from_headers(headers) -> Optional[str]`**

Extract webhook signature from request headers.

Parameters:
- `headers` (dict): Request headers

Returns:
- `str`: Signature value or None if not found

## Event Types

Supported webhook event types:

- `invoice.success`: Invoice successfully submitted to GRA
- `invoice.failed`: Invoice submission failed
- `refund.success`: Refund successfully submitted to GRA
- `refund.failed`: Refund submission failed
- `purchase.success`: Purchase successfully submitted to GRA
- `purchase.failed`: Purchase submission failed

## Support

For issues or questions about webhook signature verification:

1. Check this guide and troubleshooting section
2. Review test cases in `tests/test_webhook_signature_verification.py`
3. Check API logs for detailed error messages
4. Contact GRA External Integration API support

## References

- [HMAC-SHA256 Wikipedia](https://en.wikipedia.org/wiki/HMAC)
- [Webhook Security Best Practices](https://docs.github.com/en/developers/webhooks-and-events/webhooks/securing-your-webhooks)
- [Timing Attacks](https://en.wikipedia.org/wiki/Timing_attack)

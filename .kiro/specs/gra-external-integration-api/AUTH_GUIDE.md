# Authentication Middleware Guide

## Overview

The authentication middleware implements API Key + HMAC-SHA256 Signature verification for the GRA External Integration API. This ensures that only authorized businesses can submit invoices and access the API.

## How It Works

### 1. Authentication Flow

```
Client Request
    ↓
Extract Headers (X-API-Key, X-API-Signature, X-API-Timestamp)
    ↓
Validate Headers Present
    ↓
Verify Timestamp (within 5 minutes)
    ↓
Lookup Business by API Key
    ↓
Check Business Status (active)
    ↓
Verify HMAC-SHA256 Signature
    ↓
Grant Access / Deny Access
```

### 2. Signature Generation (Client Side)

Clients must generate a signature for each request:

```python
import hmac
import hashlib
from datetime import datetime

# 1. Generate body hash
body = b'{"invoice": "data"}'
body_hash = hashlib.sha256(body).hexdigest()

# 2. Create message to sign
timestamp = datetime.utcnow().isoformat() + "Z"
message = f"POST|/api/v1/invoices/submit|{timestamp}|{body_hash}"

# 3. Generate HMAC-SHA256 signature
api_secret = "your_api_secret_from_registration"
signature = hmac.new(
    key=api_secret.encode(),
    msg=message.encode(),
    digestmod=hashlib.sha256
).hexdigest()

# 4. Send request with headers
headers = {
    "X-API-Key": "your_api_key",
    "X-API-Signature": signature,
    "X-API-Timestamp": timestamp,
    "Content-Type": "application/json"
}

response = requests.post(
    "https://api.example.com/api/v1/invoices/submit",
    json={"invoice": "data"},
    headers=headers
)
```

### 3. Required Headers

Every request (except public endpoints) must include:

| Header | Description | Example |
|--------|-------------|---------|
| `X-API-Key` | Business API key (32 chars) | `abc123def456ghi789jkl012mno345pq` |
| `X-API-Signature` | HMAC-SHA256 signature (hex) | `a1b2c3d4e5f6...` |
| `X-API-Timestamp` | ISO format timestamp | `2026-02-10T10:30:45Z` |

### 4. Signature Message Format

```
<HTTP_METHOD>|<REQUEST_PATH>|<TIMESTAMP>|<BODY_HASH>
```

Example:
```
POST|/api/v1/invoices/submit|2026-02-10T10:30:45Z|abc123def456...
```

## Using in FastAPI Routes

### Basic Usage

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.middleware.auth_dependency import verify_auth, get_db

router = APIRouter()

@router.post("/api/v1/invoices/submit")
async def submit_invoice(
    request: Request,
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """
    Submit an invoice to GRA.
    
    Args:
        request: FastAPI request
        business: Authenticated business data
        db: Database session
        
    Returns:
        Submission response
    """
    # business contains:
    # {
    #     "id": "uuid-string",
    #     "name": "Business Name",
    #     "api_key": "api_key_string",
    #     "status": "active"
    # }
    
    business_id = business["id"]
    # ... process invoice ...
    return {"submission_id": "uuid", "status": "RECEIVED"}
```

### Accessing Request Body

Since the middleware reads the request body for signature verification, you need to handle it carefully:

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
import json

from app.middleware.auth_dependency import verify_auth, get_db

router = APIRouter()

@router.post("/api/v1/invoices/submit")
async def submit_invoice(
    request: Request,
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    # Read body (already read by middleware)
    body = await request.body()
    data = json.loads(body)
    
    # Process data...
    return {"status": "success"}
```

## Public Endpoints

The following endpoints do NOT require authentication:

- `GET /api/v1/health` - Health check
- `GET /docs` - Swagger documentation
- `GET /openapi.json` - OpenAPI schema
- `GET /redoc` - ReDoc documentation

To add more public endpoints, modify `AuthMiddleware.PUBLIC_ENDPOINTS`:

```python
class AuthMiddleware:
    PUBLIC_ENDPOINTS = {
        "/api/v1/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/v1/custom-public-endpoint"  # Add here
    }
```

## Error Responses

### Missing Header

```json
{
    "error_code": "AUTH_FAILED",
    "message": "Missing X-API-Key header",
    "timestamp": "2026-02-10T10:30:45Z"
}
```

### Invalid Signature

```json
{
    "error_code": "AUTH_FAILED",
    "message": "Invalid signature",
    "timestamp": "2026-02-10T10:30:45Z"
}
```

### Timestamp Outside Window

```json
{
    "error_code": "AUTH_FAILED",
    "message": "Timestamp outside acceptable window (5 minutes)",
    "timestamp": "2026-02-10T10:30:45Z"
}
```

### Invalid API Key

```json
{
    "error_code": "AUTH_FAILED",
    "message": "Invalid API key",
    "timestamp": "2026-02-10T10:30:45Z"
}
```

### Inactive Business

```json
{
    "error_code": "AUTH_FAILED",
    "message": "Business account is inactive",
    "timestamp": "2026-02-10T10:30:45Z"
}
```

## Security Considerations

### 1. Timestamp Validation

- Timestamps must be within 5 minutes of server time
- Prevents replay attacks
- Clients should sync their clocks with NTP

### 2. Signature Verification

- Uses constant-time comparison (prevents timing attacks)
- HMAC-SHA256 is cryptographically secure
- Signature includes method, path, timestamp, and body hash

### 3. API Secret Storage

- API secrets are hashed using bcrypt
- Never stored in plain text
- Never returned in API responses
- Only shown once during business registration

### 4. Rate Limiting

- Implement rate limiting per business
- Recommended: 1000 requests/hour per business
- Return 429 Too Many Requests when exceeded

### 5. HTTPS Only

- All communication must use HTTPS (TLS 1.2+)
- Certificate pinning recommended for clients
- No HTTP fallback

## Testing

### Unit Tests

```bash
pytest tests/test_auth_middleware.py -v
```

### Manual Testing with cURL

```bash
# 1. Generate signature (use Python script)
python scripts/generate_signature.py \
    --api-key "your_api_key" \
    --api-secret "your_api_secret" \
    --method "POST" \
    --path "/api/v1/invoices/submit" \
    --body '{"invoice": "data"}'

# 2. Make request
curl -X POST https://api.example.com/api/v1/invoices/submit \
    -H "X-API-Key: your_api_key" \
    -H "X-API-Signature: generated_signature" \
    -H "X-API-Timestamp: 2026-02-10T10:30:45Z" \
    -H "Content-Type: application/json" \
    -d '{"invoice": "data"}'
```

### Manual Testing with Python

```python
import requests
import hmac
import hashlib
from datetime import datetime
import json

# Configuration
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
BASE_URL = "https://api.example.com"

# Request data
method = "POST"
path = "/api/v1/invoices/submit"
body = json.dumps({"invoice": "data"}).encode()
timestamp = datetime.utcnow().isoformat() + "Z"

# Generate signature
body_hash = hashlib.sha256(body).hexdigest()
message = f"{method}|{path}|{timestamp}|{body_hash}"
signature = hmac.new(
    key=API_SECRET.encode(),
    msg=message.encode(),
    digestmod=hashlib.sha256
).hexdigest()

# Make request
headers = {
    "X-API-Key": API_KEY,
    "X-API-Signature": signature,
    "X-API-Timestamp": timestamp,
    "Content-Type": "application/json"
}

response = requests.post(
    f"{BASE_URL}{path}",
    data=body,
    headers=headers
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

## Troubleshooting

### "Invalid signature" Error

1. Verify API secret is correct
2. Check timestamp format (must be ISO format with Z suffix)
3. Ensure body hash is calculated correctly
4. Verify message format: `METHOD|PATH|TIMESTAMP|BODY_HASH`
5. Check that signature is hex-encoded

### "Timestamp outside acceptable window" Error

1. Sync client clock with NTP
2. Check server time is correct
3. Ensure timestamp is within 5 minutes of server time
4. Use UTC time, not local time

### "Invalid API key" Error

1. Verify API key is correct
2. Check for leading/trailing whitespace
3. Ensure business account exists
4. Verify business status is "active"

### "Business account is inactive" Error

1. Contact support to reactivate business
2. Check business status in database
3. Verify business hasn't been deactivated

## Best Practices

1. **Store API Secret Securely**
   - Never commit to version control
   - Use environment variables
   - Rotate regularly

2. **Implement Retry Logic**
   - Retry on 5xx errors
   - Use exponential backoff
   - Don't retry on 4xx errors

3. **Log Authentication Events**
   - Log successful authentications
   - Log failed authentication attempts
   - Monitor for suspicious patterns

4. **Monitor Rate Limits**
   - Track API usage per business
   - Alert on unusual patterns
   - Implement rate limiting

5. **Keep Clocks Synchronized**
   - Use NTP for time synchronization
   - Monitor clock drift
   - Alert on significant deviations

## API Key Rotation

To rotate API keys:

1. Generate new API key and secret
2. Update business record in database
3. Notify business of new credentials
4. Provide grace period for migration
5. Deactivate old API key after grace period

## Support

For authentication issues, contact support with:
- API key (first 8 chars only)
- Timestamp used
- Error message received
- Request method and path

# Authentication Quick Reference

## TL;DR

Every API request needs 3 headers:
```
X-API-Key: your_api_key
X-API-Signature: hmac_sha256_signature
X-API-Timestamp: 2026-02-10T10:30:45Z
```

## Generate Signature (Python)

```python
import hmac, hashlib, json
from datetime import datetime

api_secret = "your_api_secret"
method = "POST"
path = "/api/v1/invoices/submit"
body = json.dumps({"invoice": "data"}).encode()
timestamp = datetime.utcnow().isoformat() + "Z"

body_hash = hashlib.sha256(body).hexdigest()
message = f"{method}|{path}|{timestamp}|{body_hash}"
signature = hmac.new(
    key=api_secret.encode(),
    msg=message.encode(),
    digestmod=hashlib.sha256
).hexdigest()
```

## Generate Signature (CLI)

```bash
python scripts/generate_signature.py \
    --api-key "key" \
    --api-secret "secret" \
    --method "POST" \
    --path "/api/v1/invoices/submit" \
    --body '{"invoice": "data"}'
```

## Use in FastAPI Route

```python
from fastapi import APIRouter, Depends, Request
from app.middleware.auth_dependency import verify_auth, get_db

@router.post("/api/v1/invoices/submit")
async def submit_invoice(
    request: Request,
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    # business = {"id": "uuid", "name": "...", "api_key": "...", "status": "active"}
    return {"status": "success"}
```

## Make Request (Python)

```python
import requests, hmac, hashlib, json
from datetime import datetime

api_key = "your_api_key"
api_secret = "your_api_secret"
body = json.dumps({"invoice": "data"}).encode()
timestamp = datetime.utcnow().isoformat() + "Z"

body_hash = hashlib.sha256(body).hexdigest()
message = f"POST|/api/v1/invoices/submit|{timestamp}|{body_hash}"
signature = hmac.new(api_secret.encode(), message.encode(), hashlib.sha256).hexdigest()

headers = {
    "X-API-Key": api_key,
    "X-API-Signature": signature,
    "X-API-Timestamp": timestamp,
    "Content-Type": "application/json"
}

response = requests.post(
    "https://api.example.com/api/v1/invoices/submit",
    data=body,
    headers=headers
)
```

## Make Request (cURL)

```bash
curl -X POST https://api.example.com/api/v1/invoices/submit \
  -H "X-API-Key: your_api_key" \
  -H "X-API-Signature: generated_signature" \
  -H "X-API-Timestamp: 2026-02-10T10:30:45Z" \
  -H "Content-Type: application/json" \
  -d '{"invoice": "data"}'
```

## Error Codes

| Error | Cause | Fix |
|-------|-------|-----|
| Missing X-API-Key | Header not provided | Add header |
| Missing X-API-Signature | Header not provided | Add header |
| Missing X-API-Timestamp | Header not provided | Add header |
| Invalid API key | Key doesn't exist | Check key |
| Invalid signature | Signature mismatch | Regenerate signature |
| Timestamp outside window | >5 min old or future | Sync clock |
| Business account is inactive | Account deactivated | Contact support |

## Signature Message Format

```
METHOD|PATH|TIMESTAMP|BODY_HASH

Example:
POST|/api/v1/invoices/submit|2026-02-10T10:30:45Z|abc123def456...
```

## Public Endpoints (No Auth)

- `GET /api/v1/health`
- `GET /docs`
- `GET /openapi.json`
- `GET /redoc`

## Test Authentication

```bash
# Generate signature
python scripts/generate_signature.py \
    --api-key "test_key" \
    --api-secret "test_secret" \
    --method "POST" \
    --path "/api/v1/test" \
    --body '{}' \
    --output curl

# Run tests
pytest tests/test_auth_middleware.py -v
```

## Common Issues

**"Invalid signature"**
- Check API secret is correct
- Verify timestamp format (ISO + Z)
- Ensure body hash is calculated correctly
- Check message format: `METHOD|PATH|TIMESTAMP|BODY_HASH`

**"Timestamp outside window"**
- Sync clock with NTP
- Use UTC time, not local
- Ensure within 5 minutes of server

**"Invalid API key"**
- Check key is correct
- No leading/trailing spaces
- Verify business exists and is active

## Files

- `app/middleware/auth.py` - Main middleware
- `app/middleware/auth_dependency.py` - FastAPI integration
- `app/middleware/AUTH_GUIDE.md` - Full documentation
- `tests/test_auth_middleware.py` - Tests
- `scripts/generate_signature.py` - CLI tool

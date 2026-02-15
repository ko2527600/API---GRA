# Credential Verification Process - Complete Guide

## Overview

After a business registers through the registration page, the system performs multiple levels of verification and security measures to ensure the credentials are valid and secure. Here's the complete process:

---

## 1. Registration Flow

### Step 1: Business Submits Registration Form

```
User fills form:
├── Business Name: "ABC Company Ltd"
├── GRA TIN: "C00XXXXXXXX"
├── GRA Company Name: "ABC COMPANY LTD"
└── GRA Security Key: "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
```

### Step 2: Frontend Validation

```javascript
// Client-side validation in register.html
✓ Business Name: Not empty, 1-255 characters
✓ GRA TIN: 11-15 characters, alphanumeric
✓ GRA Company Name: Not empty, 1-255 characters
✓ GRA Security Key: Not empty, masked input
```

### Step 3: API Request

```
POST /api/v1/api-keys/generate

Request Body:
{
  "business_name": "ABC Company Ltd",
  "gra_tin": "C00XXXXXXXX",
  "gra_company_name": "ABC COMPANY LTD",
  "gra_security_key": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
}
```

---

## 2. Backend Verification Process

### Phase 1: Schema Validation

```python
# app/schemas/api_key.py - APIKeyGenerateRequest

class APIKeyGenerateRequest(BaseModel):
    business_name: str = Field(..., min_length=1, max_length=255)
    gra_tin: str = Field(..., min_length=11, max_length=15)
    gra_company_name: str = Field(..., min_length=1, max_length=255)
    gra_security_key: str = Field(..., min_length=1)

# Pydantic validates:
✓ All fields are present
✓ Field types are correct
✓ Field lengths are within limits
✓ No null or empty values
```

**If validation fails:**
```
Response: 422 Unprocessable Entity
{
  "detail": [
    {
      "loc": ["body", "gra_tin"],
      "msg": "ensure this value has at least 11 characters",
      "type": "value_error.string.min_length"
    }
  ]
}
```

### Phase 2: Credential Generation

```python
# app/services/api_key_service.py

# Generate API Key (32 random alphanumeric characters)
api_key = "aBcDeFgHiJkLmNoPqRsTuVwXyZ123456"

# Generate API Secret (32 random alphanumeric characters)
api_secret = "xYzAbCdEfGhIjKlMnOpQrStUvWxYz789"

# Hash API Secret using SHA256
hashed_secret = hashlib.sha256(api_secret.encode()).hexdigest()
# Result: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6"
```

**Why hash the secret?**
- API Secret is never stored in plain text
- Only the hash is stored in database
- Even if database is compromised, secrets are protected
- Similar to password hashing

### Phase 3: GRA Credentials Encryption

```python
# app/utils/encryption.py - EncryptionManager

# Encrypt GRA TIN
encrypted_tin = encryption_manager.encrypt("C00XXXXXXXX")
# Result: "gAAAAABl8x9z_encrypted_data_here..."

# Encrypt GRA Company Name
encrypted_company_name = encryption_manager.encrypt("ABC COMPANY LTD")
# Result: "gAAAAABl8x9z_encrypted_data_here..."

# Encrypt GRA Security Key
encrypted_security_key = encryption_manager.encrypt("UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH")
# Result: "gAAAAABl8x9z_encrypted_data_here..."

# Encryption Details:
├── Algorithm: AES-256 (via Fernet)
├── Key Derivation: SHA256 from ENCRYPTION_KEY
├── Encoding: Base64 URL-safe
└── Storage: Encrypted in database
```

**Why encrypt GRA credentials?**
- GRA credentials are sensitive
- Never stored in plain text
- Encrypted at rest in database
- Only decrypted when needed for GRA API calls
- Protects against database breaches

### Phase 4: Business Record Creation

```python
# app/services/business_service.py - create_business()

business = Business(
    id=uuid.uuid4(),                          # Unique ID
    name="ABC Company Ltd",                   # Plain text (not sensitive)
    api_key="aBcDeFgHiJkLmNoPqRsTuVwXyZ123456",  # Plain text (public)
    api_secret="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6",  # HASHED
    gra_tin="gAAAAABl8x9z_encrypted_data_here...",  # ENCRYPTED
    gra_company_name="gAAAAABl8x9z_encrypted_data_here...",  # ENCRYPTED
    gra_security_key="gAAAAABl8x9z_encrypted_data_here...",  # ENCRYPTED
    status="active"
)

db.add(business)
db.commit()
```

### Phase 5: Duplicate TIN Check

```python
# Database constraint: UNIQUE(gra_tin)

# If business tries to register with same TIN:
try:
    db.commit()
except IntegrityError:
    # TIN already exists
    raise HTTPException(
        status_code=409,
        detail="Business with this TIN already exists"
    )
```

**Response if TIN already registered:**
```json
{
  "detail": "Business with this TIN already exists"
}
```

### Phase 6: Response Generation

```python
# Only return API Secret ONCE (never again)
return APIKeyResponse(
    api_key="aBcDeFgHiJkLmNoPqRsTuVwXyZ123456",
    api_secret="xYzAbCdEfGhIjKlMnOpQrStUvWxYz789",  # Plain text (only time shown)
    business_id="550e8400-e29b-41d4-a716-446655440000",
    business_name="ABC Company Ltd",
    created_at="2026-02-14T10:00:00Z"
)
```

---

## 3. Database Storage

### What Gets Stored

```
businesses table:
┌─────────────────────────────────────────────────────────────┐
│ id                  │ 550e8400-e29b-41d4-a716-446655440000  │
├─────────────────────────────────────────────────────────────┤
│ name                │ ABC Company Ltd                        │
├─────────────────────────────────────────────────────────────┤
│ api_key             │ aBcDeFgHiJkLmNoPqRsTuVwXyZ123456      │
├─────────────────────────────────────────────────────────────┤
│ api_secret          │ a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6...  │
│                     │ (HASHED - cannot be reversed)         │
├─────────────────────────────────────────────────────────────┤
│ gra_tin             │ gAAAAABl8x9z_encrypted_data_here...   │
│                     │ (ENCRYPTED - requires key to decrypt) │
├─────────────────────────────────────────────────────────────┤
│ gra_company_name    │ gAAAAABl8x9z_encrypted_data_here...   │
│                     │ (ENCRYPTED - requires key to decrypt) │
├─────────────────────────────────────────────────────────────┤
│ gra_security_key    │ gAAAAABl8x9z_encrypted_data_here...   │
│                     │ (ENCRYPTED - requires key to decrypt) │
├─────────────────────────────────────────────────────────────┤
│ status              │ active                                 │
├─────────────────────────────────────────────────────────────┤
│ created_at          │ 2026-02-14T10:00:00Z                  │
└─────────────────────────────────────────────────────────────┘
```

### Security Levels

```
┌─────────────────────────────────────────────────────────────┐
│ PLAIN TEXT (Public)                                         │
├─────────────────────────────────────────────────────────────┤
│ • id (UUID)                                                 │
│ • name (Business name)                                      │
│ • api_key (Used in X-API-Key header)                        │
│ • status (active/inactive)                                  │
│ • created_at (Timestamp)                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ HASHED (One-way, cannot be reversed)                        │
├─────────────────────────────────────────────────────────────┤
│ • api_secret (SHA256 hash)                                  │
│   - Used for verification only                              │
│   - Never returned to user after registration               │
│   - Cannot be recovered if lost                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ENCRYPTED (Two-way, can be decrypted with key)              │
├─────────────────────────────────────────────────────────────┤
│ • gra_tin (AES-256)                                         │
│ • gra_company_name (AES-256)                                │
│ • gra_security_key (AES-256)                                │
│   - Decrypted only when needed for GRA API calls            │
│   - Requires ENCRYPTION_KEY from environment                │
│   - Protected by database encryption                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Credential Verification During API Requests

### When Business Makes API Request

```
POST /api/v1/invoices/submit

Headers:
├── X-API-Key: aBcDeFgHiJkLmNoPqRsTuVwXyZ123456
├── X-API-Signature: <hmac_signature>
└── Content-Type: application/json

Body: {...invoice data...}
```

### Verification Steps

#### Step 1: Extract API Key from Header

```python
# app/middleware/auth.py - verify_api_key()

api_key = request.headers.get("X-API-Key")
# Result: "aBcDeFgHiJkLmNoPqRsTuVwXyZ123456"
```

#### Step 2: Look Up Business by API Key

```python
# Query database
business = db.query(Business).filter(
    Business.api_key == "aBcDeFgHiJkLmNoPqRsTuVwXyZ123456"
).first()

# If not found:
if not business:
    raise HTTPException(
        status_code=401,
        detail="Invalid API key"
    )
```

#### Step 3: Verify HMAC Signature

```python
# app/utils/hmac_signature.py

# Extract signature from header
signature = request.headers.get("X-API-Signature")

# Generate expected signature
expected_signature = HMAC-SHA256(
    key=api_secret,  # From database (hashed)
    message=request_body
)

# Compare signatures
if signature != expected_signature:
    raise HTTPException(
        status_code=401,
        detail="Invalid signature"
    )
```

#### Step 4: Decrypt GRA Credentials (if needed)

```python
# When submitting to GRA, decrypt credentials
decrypted_tin = encryption_manager.decrypt(business.gra_tin)
# Result: "C00XXXXXXXX"

decrypted_company_name = encryption_manager.decrypt(business.gra_company_name)
# Result: "ABC COMPANY LTD"

decrypted_security_key = encryption_manager.decrypt(business.gra_security_key)
# Result: "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"

# Use decrypted credentials to call GRA API
gra_response = gra_client.submit_invoice(
    tin=decrypted_tin,
    company_name=decrypted_company_name,
    security_key=decrypted_security_key,
    invoice_data=invoice
)
```

---

## 5. Security Features Summary

### At Registration

| Feature | Implementation | Benefit |
|---------|-----------------|---------|
| **Schema Validation** | Pydantic | Prevents invalid data |
| **TIN Uniqueness** | Database constraint | Prevents duplicate registrations |
| **API Secret Hashing** | SHA256 | Protects against database breaches |
| **GRA Credential Encryption** | AES-256 | Protects sensitive data at rest |
| **One-time Secret Display** | Return only once | Secret cannot be recovered if lost |

### During API Requests

| Feature | Implementation | Benefit |
|---------|-----------------|---------|
| **API Key Lookup** | Database query | Verifies business identity |
| **HMAC Signature** | SHA256 verification | Ensures request authenticity |
| **Credential Decryption** | On-demand decryption | Minimizes exposure of sensitive data |
| **Audit Logging** | All requests logged | Tracks all API usage |
| **Rate Limiting** | Per-business limits | Prevents abuse |

---

## 6. What Happens If Credentials Are Compromised

### If API Key is Compromised

```
Attacker has: API Key
Cannot do: Make valid requests (needs API Secret for signature)
Solution: Revoke API key, generate new credentials
```

### If API Secret is Compromised

```
Attacker has: API Secret
Can do: Generate valid HMAC signatures, make API requests
Solution: Revoke API key immediately, generate new credentials
```

### If GRA Credentials are Compromised

```
Attacker has: Encrypted GRA credentials
Cannot do: Use them (requires ENCRYPTION_KEY)
Solution: Update GRA credentials through API
```

### If Database is Compromised

```
Attacker has: Encrypted GRA credentials + Hashed API Secret
Cannot do: 
  - Decrypt GRA credentials (requires ENCRYPTION_KEY)
  - Reverse API Secret hash (one-way)
  - Use API Secret directly (it's hashed)
Solution: Rotate ENCRYPTION_KEY, revoke all API keys
```

---

## 7. Verification Checklist

### During Registration

- [x] Schema validation (Pydantic)
- [x] Field length validation
- [x] TIN uniqueness check
- [x] API credentials generation
- [x] API secret hashing
- [x] GRA credentials encryption
- [x] Database storage
- [x] Audit logging

### During API Requests

- [x] API key extraction
- [x] Business lookup
- [x] HMAC signature verification
- [x] GRA credentials decryption (when needed)
- [x] Request validation
- [x] Audit logging
- [x] Rate limiting

---

## 8. Configuration & Keys

### Environment Variables Required

```bash
# .env file

# Encryption key for GRA credentials
ENCRYPTION_KEY=your-secret-encryption-key-here

# Database connection
DATABASE_URL=postgresql://user:password@localhost/gra_api

# API configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### Key Management

```
ENCRYPTION_KEY:
├── Used to encrypt/decrypt GRA credentials
├── Must be stored securely (not in code)
├── Should be rotated periodically
├── Required for decryption (if lost, data cannot be recovered)
└── Length: At least 32 characters recommended
```

---

## 9. Audit Trail

### What Gets Logged

```
Every registration:
├── Timestamp
├── Business name
├── Business ID
├── API key (first 8 chars only)
├── Status (success/failure)
└── Error details (if failed)

Every API request:
├── Timestamp
├── Business ID
├── Endpoint
├── Method (GET/POST/etc)
├── Status code
├── Response time
└── Error details (if failed)
```

### Audit Log Storage

```
audit_logs table:
├── id (UUID)
├── business_id (FK to businesses)
├── action (REGISTER, SUBMIT_INVOICE, etc)
├── endpoint (/api/v1/invoices/submit)
├── method (POST)
├── request_payload (masked sensitive data)
├── response_code (200, 400, 401, etc)
├── response_status (SUCCESS, FAILED)
├── error_message (if failed)
├── ip_address
├── user_agent
└── created_at
```

---

## 10. Best Practices

### For Businesses

1. **Store API Secret Securely**
   - Use password manager
   - Never commit to version control
   - Never share with anyone

2. **Rotate Credentials Regularly**
   - Revoke old API keys
   - Generate new credentials
   - Update applications

3. **Monitor API Usage**
   - Check audit logs
   - Monitor rate limits
   - Alert on unusual activity

### For Administrators

1. **Protect ENCRYPTION_KEY**
   - Store in secure vault
   - Rotate periodically
   - Limit access

2. **Monitor Database**
   - Regular backups
   - Encryption at rest
   - Access controls

3. **Audit Logs**
   - Review regularly
   - Archive old logs
   - Alert on suspicious activity

---

## Summary

The credential verification process is **multi-layered and secure**:

1. **Registration**: Validates, encrypts, hashes, and stores credentials
2. **Storage**: Uses encryption for sensitive data, hashing for secrets
3. **Verification**: Checks API key, verifies signature, decrypts credentials
4. **Audit**: Logs all actions for compliance and security

**Result**: Businesses can securely register and use the API with confidence that their credentials are protected.

---

**Version**: 1.0.0  
**Last Updated**: February 2026

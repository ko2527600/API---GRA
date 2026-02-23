  # Credential Verification Flow - Visual Diagrams

## Registration Flow

```
Business Submits Form
    ↓
Client-side Validation (TIN length, required fields)
    ↓
POST /api/v1/api-keys/generate
    ↓
Pydantic Schema Validation
    ↓
Generate API Key (32 random chars)
Generate API Secret (32 random chars)
    ↓
Hash API Secret (SHA256)
    ↓
Encrypt GRA Credentials (AES-256)
    ├── gra_tin → encrypted
    ├── gra_company_name → encrypted
    └── gra_security_key → encrypted
    ↓
Check TIN Uniqueness (Database constraint)
    ↓
Store in Database
    ├── api_key (plain)
    ├── api_secret (HASHED)
    ├── gra_tin (ENCRYPTED)
    ├── gra_company_name (ENCRYPTED)
    └── gra_security_key (ENCRYPTED)
    ↓
Log Registration (Audit log)
    ↓
Return Credentials (Only time shown!)
    ├── API Key
    ├── API Secret (NEVER returned again)
    └── Business ID
    ↓
User Stores Credentials Securely
```

---

## API Request Verification Flow

```
Business Makes API Request
    ↓
Headers:
├── X-API-Key: aBcDeFgHiJkLmNoPqRsTuVwXyZ123456
├── X-API-Signature: <hmac_signature>
└── Content-Type: application/json
    ↓
Extract API Key from Header
    ↓
Query Database: Find business by API Key
    ↓
Business Found?
├── NO → 401 Unauthorized
└── YES → Continue
    ↓
Extract HMAC Signature from Header
    ↓
Generate Expected Signature:
├── message = METHOD + PATH + TIMESTAMP + BODY_HASH
└── expected_sig = HMAC-SHA256(api_secret, message)
    ↓
Signature Valid?
├── NO → 401 Unauthorized
└── YES → Continue
    ↓
Validate Request Data (Schema, business logic, taxes)
    ↓
Data Valid?
├── NO → 400 Bad Request
└── YES → Continue
    ↓
Decrypt GRA Credentials (if needed)
├── gra_tin → decrypted
├── gra_company_name → decrypted
└── gra_security_key → decrypted
    ↓
Call GRA API with Decrypted Credentials
    ↓
Log Request (Audit log)
    ↓
Return Response to Business
```

---

## Data Storage Security

```
PLAIN TEXT (Public)
├── id (UUID)
├── name (Business name)
├── api_key (Used in X-API-Key header)
├── status (active/inactive)
└── created_at (Timestamp)

HASHED (One-way, cannot be reversed)
├── api_secret (SHA256)
│   └── Used for verification only
│   └── Never returned after registration
│   └── Cannot be recovered if lost

ENCRYPTED (Two-way, can be decrypted with key)
├── gra_tin (AES-256)
├── gra_company_name (AES-256)
└── gra_security_key (AES-256)
    └── Decrypted only when needed
    └── Requires ENCRYPTION_KEY
    └── Protected by database encryption
```

---

## Security Layers

```
Layer 1: Transport
└── HTTPS (TLS 1.2+)
    └── Encrypts data in transit

Layer 2: Authentication
└── API Key + HMAC Signature
    └── Verifies business identity
    └── Proves request authenticity

Layer 3: Authorization
└── Business Isolation
    └── Each business accesses only their data

Layer 4: Data Encryption
└── Database Encryption
    └── GRA credentials encrypted at rest
    └── API secret hashed (one-way)

Layer 5: Audit & Monitoring
└── Comprehensive Logging
    └── All requests logged
    └── Suspicious activity tracked
```

---

## Credential Verification Checklist

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

## What Gets Stored Where

```
Database (PostgreSQL)
├── businesses table
│   ├── id: UUID
│   ├── name: "ABC Company Ltd"
│   ├── api_key: "aBcDeFgHiJkLmNoPqRsTuVwXyZ123456"
│   ├── api_secret: "a1b2c3d4e5f6g7h8..." (HASHED)
│   ├── gra_tin: "gAAAAABl8x9z..." (ENCRYPTED)
│   ├── gra_company_name: "gAAAAABl8x9z..." (ENCRYPTED)
│   ├── gra_security_key: "gAAAAABl8x9z..." (ENCRYPTED)
│   └── status: "active"
│
└── audit_logs table
    ├── business_id: UUID
    ├── action: "REGISTER" or "SUBMIT_INVOICE"
    ├── endpoint: "/api/v1/invoices/submit"
    ├── method: "POST"
    ├── response_code: 200
    ├── response_status: "SUCCESS"
    └── created_at: timestamp
```

---

## Key Points

1. **API Secret is shown ONLY ONCE**
   - After registration, it's never returned again
   - If lost, cannot be recovered
   - Business must store it securely

2. **GRA Credentials are ENCRYPTED**
   - Never stored in plain text
   - Decrypted only when needed
   - Requires ENCRYPTION_KEY to decrypt

3. **API Secret is HASHED**
   - One-way hash (cannot be reversed)
   - Used for verification only
   - Even if database is compromised, secret is protected

4. **Every Request is Verified**
   - API Key lookup
   - HMAC signature verification
   - Business isolation check
   - Audit logging

5. **All Actions are Logged**
   - Registration logged
   - Every API request logged
   - Suspicious activity tracked
   - 7-year retention for compliance

---

## Security Summary

```
Registration:
Business provides credentials
    ↓
System validates, encrypts, hashes, and stores
    ↓
Returns API Key + Secret (only time shown)

API Requests:
Business includes API Key + HMAC Signature
    ↓
System verifies identity and authenticity
    ↓
Decrypts GRA credentials if needed
    ↓
Processes request
    ↓
Logs everything

Result: Secure, auditable, compliant system
```

---

**Version**: 1.0.0  
**Last Updated**: February 2026

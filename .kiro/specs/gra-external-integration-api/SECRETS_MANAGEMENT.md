# Secrets Management for GRA Credentials

## Overview

The GRA External Integration API implements a comprehensive secrets management system for securely storing, retrieving, rotating, and revoking GRA credentials. This document outlines the implementation, configuration, and best practices.

## Architecture

### Components

1. **SecretsManager Service** (`app/services/secrets_manager.py`)
   - Core service for credential operations
   - Supports multiple backends (local, Vault, AWS Secrets Manager, Azure Key Vault)
   - Provides audit logging and compliance tracking

2. **SecretsConfig** (`app/config/secrets_config.py`)
   - Configuration management for secrets backends
   - Environment-based configuration
   - Support for multiple cloud providers

3. **EncryptionManager** (`app/utils/encryption.py`)
   - AES-256 encryption for local storage
   - Fernet-based encryption with key derivation
   - Secure encryption/decryption operations

4. **Business Model** (`app/models/models.py`)
   - Stores encrypted GRA credentials
   - Provides decryption methods
   - Supports credential versioning

## Features

### 1. Secure Credential Storage

GRA credentials are encrypted at rest using AES-256 encryption:

```python
from app.services.secrets_manager import SecretsManager

# Store credentials
result = SecretsManager.store_gra_credentials(
    db,
    business_id=business.id,
    gra_tin="P00123456789",
    gra_company_name="ABC Company Ltd",
    gra_security_key="SECURITY_KEY_12345"
)
```

**Storage Details:**
- Credentials encrypted using AES-256 via Fernet
- Encryption key derived from `ENCRYPTION_KEY` environment variable
- Encrypted data stored in PostgreSQL database
- Credentials never logged or exposed in responses

### 2. Credential Retrieval

Retrieve and decrypt credentials on-demand:

```python
# Retrieve credentials
credentials = SecretsManager.retrieve_gra_credentials(
    db,
    business_id=business.id,
    audit_log=True  # Log access for compliance
)

# Access individual credentials
tin = credentials["gra_tin"]
company_name = credentials["gra_company_name"]
security_key = credentials["gra_security_key"]
```

**Access Control:**
- Only active businesses can retrieve credentials
- All access is logged for audit trail
- Decryption happens on-demand (not cached)

### 3. Credential Rotation

Rotate credentials to implement key rotation strategy:

```python
# Rotate credentials
result = SecretsManager.rotate_gra_credentials(
    db,
    business_id=business.id,
    new_gra_tin="P00987654321",
    new_gra_company_name="Updated Company",
    new_gra_security_key="NEW_SECURITY_KEY"
)
```

**Rotation Process:**
- Old credentials stored for audit trail
- New credentials encrypted and stored
- Business status remains active
- All changes logged

### 4. Credential Revocation

Revoke credentials when needed:

```python
# Revoke credentials
result = SecretsManager.revoke_gra_credentials(
    db,
    business_id=business.id,
    reason="Security breach detected"
)
```

**Revocation Effects:**
- Business status set to "inactive"
- Credentials cannot be retrieved
- All future requests rejected
- Revocation logged with reason

### 5. Credential Validation

Validate credential integrity and accessibility:

```python
# Validate credentials
validation = SecretsManager.validate_gra_credentials(
    db,
    business_id=business.id
)

# Check validation results
if validation["status"] == "valid":
    print("All checks passed")
    for check, result in validation["checks"].items():
        print(f"  {check}: {result}")
```

**Validation Checks:**
- Business is active
- Credentials are encrypted
- Credentials can be decrypted
- All required fields present

### 6. Credential Metadata

Get credential metadata without exposing secrets:

```python
# Get metadata
metadata = SecretsManager.get_credential_metadata(
    db,
    business_id=business.id
)

# Metadata includes:
# - business_id, business_name, status
# - credentials_stored, credentials_encrypted
# - created_at, updated_at
```

## Configuration

### Environment Variables

```bash
# Secrets Backend Selection
SECRETS_BACKEND=local  # Options: local, vault, aws_secrets, azure_keyvault

# Local Backend (Default)
SECRETS_ENCRYPTION_KEY=your-encryption-key-change-in-production
SECRETS_KEY_ROTATION_ENABLED=False
SECRETS_KEY_ROTATION_DAYS=90

# Audit & Compliance
SECRETS_AUDIT_ENABLED=True
SECRETS_AUDIT_LOG_RETENTION_DAYS=2555  # 7 years

# Credential Rotation
SECRETS_CREDENTIAL_ROTATION_ENABLED=False
SECRETS_CREDENTIAL_ROTATION_DAYS=180

# Revocation
SECRETS_REVOCATION_ENABLED=True
```

### Backend Configuration

#### Local Backend (Default)

```python
from app.config.secrets_config import secrets_config

if secrets_config.is_local_backend():
    # Using local encrypted storage
    # Credentials encrypted with SECRETS_ENCRYPTION_KEY
    pass
```

#### HashiCorp Vault

```bash
SECRETS_BACKEND=vault
VAULT_ADDR=https://vault.example.com:8200
VAULT_TOKEN=s.xxxxxxxxxxxxxxxx
VAULT_ENGINE_PATH=secret
VAULT_SECRET_PATH=gra-credentials
```

#### AWS Secrets Manager

```bash
SECRETS_BACKEND=aws_secrets
AWS_REGION=us-east-1
AWS_SECRET_NAME_PREFIX=gra-api
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

#### Azure Key Vault

```bash
SECRETS_BACKEND=azure_keyvault
AZURE_VAULT_URL=https://myvault.vault.azure.net/
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Security Best Practices

### 1. Encryption Key Management

**Local Backend:**
- Store `ENCRYPTION_KEY` in secure vault (not in code)
- Use strong, random key (minimum 32 characters)
- Rotate encryption key periodically
- Never commit encryption key to version control

```bash
# Generate strong encryption key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Access Control

- Only authenticated businesses can retrieve their credentials
- Implement role-based access control (RBAC)
- Audit all credential access
- Restrict credential operations to authorized users

### 3. Audit Logging

All credential operations are logged:

```python
# Logged operations:
# - STORE_CREDENTIALS: New credentials stored
# - RETRIEVE_CREDENTIALS: Credentials retrieved
# - ROTATE_CREDENTIALS: Credentials rotated
# - REVOKE_CREDENTIALS: Credentials revoked
```

### 4. Credential Rotation

Implement regular credential rotation:

```python
# Enable automatic rotation
SECRETS_CREDENTIAL_ROTATION_ENABLED=True
SECRETS_CREDENTIAL_ROTATION_DAYS=180

# Manual rotation
SecretsManager.rotate_gra_credentials(
    db,
    business_id,
    new_gra_tin,
    new_gra_company_name,
    new_gra_security_key
)
```

### 5. HTTPS Only

- All API communication over HTTPS (TLS 1.2+)
- Certificate pinning recommended
- No HTTP fallback

### 6. Sensitive Data Masking

Credentials are masked in logs:

```python
# Logs show:
# - Action performed
# - Business ID
# - Timestamp
# - Status

# Logs do NOT show:
# - Actual credential values
# - Decrypted data
# - API secrets
```

## API Integration

### Using Credentials in Submissions

When submitting to GRA, credentials are retrieved and injected:

```python
from app.services.secrets_manager import SecretsManager

# Get credentials for submission
credentials = SecretsManager.retrieve_gra_credentials(db, business_id)

# Inject into GRA request
gra_request = {
    "company": {
        "COMPANY_TIN": credentials["gra_tin"],
        "COMPANY_NAMES": credentials["gra_company_name"],
        "COMPANY_SECURITY_KEY": credentials["gra_security_key"]
    },
    # ... rest of request
}

# Submit to GRA
response = submit_to_gra(gra_request)
```

## Testing

Comprehensive test suite included:

```bash
# Run secrets manager tests
pytest tests/test_secrets_manager.py -v

# Test coverage:
# - Credential storage and retrieval
# - Credential rotation
# - Credential revocation
# - Validation checks
# - Error handling
# - Edge cases
```

## Compliance

### Requirements Met

✅ **REQ-AUTH-004**: GRA credentials encrypted at rest using AES-256
✅ **REQ-AUTH-005**: GRA credentials never logged or exposed
✅ **REQ-SEC-006**: Encrypt GRA credentials at rest (AES-256)
✅ **REQ-SEC-009**: Implement key rotation strategy
✅ **REQ-SEC-010**: Support credential revocation
✅ **REQ-AUDIT-008**: Mask API secrets in logs
✅ **REQ-AUDIT-009**: Mask GRA security keys in logs

### Audit Trail

All credential operations logged:

```python
# Audit log includes:
# - Operation type (STORE, RETRIEVE, ROTATE, REVOKE)
# - Business ID
# - Timestamp
# - Status (success/failure)
# - Error details (if applicable)
```

## Troubleshooting

### Credential Retrieval Fails

**Issue**: "Decryption failed: Invalid token or corrupted data"

**Solution**:
1. Verify encryption key is correct
2. Check credentials are properly encrypted
3. Validate database integrity
4. Check encryption manager initialization

### Business Status Inactive

**Issue**: "Business is not active"

**Solution**:
1. Check if credentials were revoked
2. Verify business status in database
3. Contact administrator to reactivate

### Encryption Key Mismatch

**Issue**: Different encryption keys produce different encrypted values

**Solution**:
1. Ensure same encryption key used for encrypt/decrypt
2. Check environment variable configuration
3. Verify key hasn't been rotated

## Future Enhancements

1. **Automatic Key Rotation**
   - Scheduled key rotation
   - Graceful key migration
   - Versioned encryption keys

2. **External Secrets Managers**
   - HashiCorp Vault integration
   - AWS Secrets Manager integration
   - Azure Key Vault integration

3. **Advanced Audit**
   - Detailed access logs
   - Anomaly detection
   - Compliance reporting

4. **Credential Expiration**
   - Automatic credential expiration
   - Renewal notifications
   - Forced rotation on expiration

## References

- [OWASP: Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Cryptography: Fernet](https://cryptography.io/en/latest/fernet/)
- [HashiCorp Vault](https://www.vaultproject.io/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [Azure Key Vault](https://azure.microsoft.com/en-us/services/key-vault/)

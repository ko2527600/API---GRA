# GRA External Integration API - Design Document

## 1. Architecture Overview

### 1.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Business Systems (ERP/POS)                  │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   System A   │  │   System B   │  │   System N   │           │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘           │
│         │                 │                 │                    │
│         └─────────────────┼─────────────────┘                    │
│                           │                                      │
│                    HTTPS (TLS 1.2+)                              │
│                           │                                      │
├────────────r XML in GRA format)
Your External Integration API
    ├─ Authentication Layer (API Key + HMAC Signature)
    ├─ Validation Layer (Pre-GRA compliance checks)
    ├─ Format Handler (JSON/XML support)
    ├─ Submission Layer (Forward to GRA)
    ├─ Storage Layer (PostgreSQL)
    └─ Notification Layer (Webhooks)
    ↓
GRA E-VAT API (Official GRA System)
    ↓
GRA Backend (Record-keeping, auditing)
```

### 2.2 Data Flow

1. **Business submits invoice** in GRA format (JSON or XML)
2. **Your API authenticates** using API Key + HMAC Signature
3. **Your API validates** against all GRA error codes
4. **Your API stores** submission record in database
5. **Your API forwards** to GRA with business's GRA credentials
6. **GRA processes** and returns response
7. **Your API stores** GRA response
8. **Your API returns** status to business
9. **Your API sends** webhook notification (if configured)
10. **Business polls** or receives webhook for final status

### 2.3 Multi-Tenant Isolation

- Each business is a separate tenant
- Each business has unique API Key + Secret
- Each business stores their own GRA credentials (encrypted)
- Businesses can only access their own submissions
- Audit logs track all access per business

---

## 3. API Endpoints

### 3.1 Invoicing Module

#### 3.1.1 Submit Invoice
```
POST /api/v1/invoices/submit

Authentication:
  X-API-Key: <business_api_key>
  X-API-Signature: <hmac_sha256_signature>

Content-Type: application/json or application/xml

Request Format: GRA Invoice Format (JSON or XML)
Response: 202 Accepted
```

#### 3.1.2 Get Invoice Status
```
GET /api/v1/invoices/{submission_id}/status

Response: 200 OK
Returns: Current submission status, GRA response details
```

#### 3.1.3 Get Invoice Signature (Stamping Details)
```
POST /api/v1/invoices/{submission_id}/signature

Response: 200 OK
Returns: VSDC signature details (ysdcid, ysdcrecnum, QR code)
```

### 3.2 Refund Module

#### 3.2.1 Submit Refund
```
POST /api/v1/refunds/submit

Request Format: GRA Refund Format (FLAG: REFUND, REFUND_ID required)
Response: 202 Accepted
```

#### 3.2.2 Get Refund Status
```
GET /api/v1/refunds/{submission_id}/status

Response: 200 OK
```

### 3.3 Purchase Module

#### 3.3.1 Submit Purchase
```
POST /api/v1/purchases/submit

Request Format: GRA Purchase Format (FLAG: PURCHASE)
Response: 202 Accepted
```

#### 3.3.2 Get Purchase Status
```
GET /api/v1/purchases/{submission_id}/status

Response: 200 OK
```

### 3.4 Items Module

#### 3.4.1 Register Item Codes
```
POST /api/v1/items/register

Request Format: GRA Item Registration Format
Response: 202 Accepted
```

### 3.5 Inventory Module

#### 3.5.1 Update Inventory
```
POST /api/v1/inventory/update

Request Format: GRA Inventory Update Format
Response: 202 Accepted
```

### 3.6 TIN Validator Module

#### 3.6.1 Validate TIN
```
POST /api/v1/tin/validate

Request Format: GRA TIN Validator Format
Response: 200 OK
Returns: TIN validation status (VALID, INVALID, STOPPED, PROTECTED)
```

### 3.7 Tag Description Module

#### 3.7.1 Register Tag Description
```
POST /api/v1/tags/register

Request Body:
{
  "tags": [
    {
      "tag_code": "TAG001",
      "description": "Premium Product",
      "category": "PRODUCT_TYPE"
    }
  ]
}

Response: 200 OK
```

#### 3.7.2 Get Tag Description
```
GET /api/v1/tags/{tag_code}

Response: 200 OK
```

### 3.8 Z-Report Module

#### 3.8.1 Request Z-Report
```
POST /api/v1/reports/z-report

Request Format: GRA Z-Report Format
Response: 202 Accepted or 200 OK (if immediate)
```

#### 3.8.2 Get Z-Report
```
GET /api/v1/reports/z-report/{date}

Response: 200 OK
Returns: Z-Report data (inv_close, inv_count, inv_vat, etc)
```

### 3.9 VSDC Health Check Module

#### 3.9.1 Check VSDC Health
```
POST /api/v1/vsdc/health-check

Request Format: GRA Health Check Format
Response: 200 OK
Returns: VSDC status (UP, DOWN, DEGRADED)
```

#### 3.9.2 Get VSDC Status
```
GET /api/v1/vsdc/status

Response: 200 OK
Returns: Current VSDC status and uptime metrics
```

### 3.10 System Health Module

#### 3.10.1 API Health Check
```
GET /api/v1/health

Response: 200 OK
Returns: API health status, component status
```

---

## 4. Data Models

### 4.1 Business Model
```
businesses
├── id (UUID, PK)
├── name (string)
├── api_key (string, unique)
├── api_secret (string, hashed)
├── gra_tin (string, encrypted)
├── gra_company_name (string, encrypted)
├── gra_security_key (string, encrypted)
├── status (enum: active, inactive)
├── created_at (timestamp)
└── updated_at (timestamp)
```

### 4.2 Submission Model
```
submissions
├── id (UUID, PK)
├── business_id (UUID, FK)
├── submission_type (enum: INVOICE, REFUND, PURCHASE, ITEM, INVENTORY)
├── submission_status (enum: RECEIVED, PROCESSING, PENDING_GRA, SUCCESS, FAILED)
├── gra_response_code (string, nullable)
├── gra_response_message (string, nullable)
├── gra_invoice_id (string, nullable)
├── gra_qr_code (string, nullable)
├── gra_receipt_num (string, nullable)
├── submitted_at (timestamp)
├── completed_at (timestamp, nullable)
├── raw_request (JSON)
├── raw_response (JSON, nullable)
├── error_details (JSON, nullable)
└── created_at (timestamp)
```

### 4.3 Invoice Model
```
invoices
├── id (UUID, PK)
├── submission_id (UUID, FK)
├── invoice_num (string, unique per business)
├── client_name (string)
├── client_tin (string, nullable)
├── invoice_date (date)
├── computation_type (enum: INCLUSIVE, EXCLUSIVE)
├── total_vat (decimal)
├── total_levy (decimal)
├── total_amount (decimal)
├── items_count (integer)
└── created_at (timestamp)
```

### 4.4 Invoice Item Model
```
invoice_items
├── id (UUID, PK)
├── invoice_id (UUID, FK)
├── itmref (string)
├── itmdes (string)
├── quantity (decimal)
├── unityprice (decimal)
├── taxcode (enum: A, B, C, D, E)
├── taxrate (decimal)
├── levy_amount_a (decimal)
├── levy_amount_b (decimal)
├── levy_amount_c (decimal)
├── levy_amount_d (decimal)
├── itmdiscount (decimal)
├── item_total (decimal)
└── item_category (string)
```

### 4.5 Audit Log Model
```
audit_logs
├── id (UUID, PK)
├── business_id (UUID, FK)
├── action (string)
├── endpoint (string)
├── method (enum: GET, POST, PUT, DELETE)
├── request_payload (JSON, masked)
├── response_code (integer)
├── response_status (enum: SUCCESS, FAILED)
├── error_message (string, nullable)
├── ip_address (string)
├── user_agent (string)
└── created_at (timestamp)
```

---

## 5. Validation Rules

### 5.1 Pre-Submission Validation

Your API validates **before** sending to GRA:

#### 5.1.1 Authentication Validation
- API Key exists and is active
- API Signature is valid (HMAC-SHA256)
- Business account is active
- GRA credentials are stored and valid

#### 5.1.2 Schema Validation
- All required fields present
- Data types correct
- Field lengths valid
- Format compliance (JSON or XML well-formed)

#### 5.1.3 Business Logic Validation
- TOTAL_AMOUNT = sum of items + VAT + levies (B16)
- TOTAL_VAT = sum of item VATs (B18)
- TOTAL_LEVY = sum of item levies (B34)
- ITEMS_COUNTS matches item_list length (B15)
- Invoice NUM is unique per business (B20)
- CLIENT_TIN format: 11 or 15 characters (B051)
- TAXRATE in [0, 15, 3] (B13, A09)
- TAXCODE in [A, B, C, D, E] (A08)
- All levy amounts non-negative (B31-B35)
- CURRENCY must be GHS (B70)
- EXCHANGE_RATE must be 1 (B70)
- For REFUND: REFUND_ID must reference existing invoice (A05)
- CLIENT_NAME must be provided (B05)
- QUANTITY must be positive (B10, B11)
- UNITYPRICE must be positive (B21, A06)

#### 5.1.4 Tax/Levy Calculation Validation
- Verify levy calculations per GRA formula:
  - LEVY_A = UNITYPRICE × 2.5% (NHIL)
  - LEVY_B = UNITYPRICE × 2.5% (GETFund)
  - LEVY_C = UNITYPRICE × 1% (COVID - may be 0)
  - LEVY_D = varies (Tourism/CST)
- Verify VAT calculations:
  - For TAX_B: VAT = (UNITYPRICE + LEVY_A + LEVY_B + LEVY_C) × 15%
  - For TAX_A, C, D: VAT = 0%
  - For TAX_E: VAT = 3%

#### 5.1.5 GRA Compliance Checks
- FLAG must be valid (INVOICE, REFUND, PROFORMA, PARTIAL_REFUND, PURCHASE)
- COMPUTATION_TYPE must be INCLUSIVE or EXCLUSIVE
- SALE_TYPE must be valid (NORMAL, CREDIT_SALE)
- INVOICE_DATE format: YYYY-MM-DD
- No duplicate invoice numbers per business

### 5.2 GRA Error Code Handling

Your API maps all GRA error codes and returns meaningful responses:

**Authentication Errors**:
- A01: Company credentials do not exist
- B01: Incorrect client TIN PIN

**Invoice/Refund Errors**:
- B16: Total amount mismatch
- B18: Total VAT mismatch
- B19: Invoice reference missing
- B20: Invoice reference already sent
- B22: Zero total invoice not supported
- B70: Wrong currency
- A05: Missing original invoice number (for refunds)

**Item Errors**:
- B05: Client name missing
- B051: Tax number format not accepted
- B06: Client name different from previous
- B061: Item code different from previous
- B07: Code missing
- B09: Description missing
- B10: Quantity missing
- B11: Quantity is negative
- B12: Quantity not a number
- B13: Tax rate not accepted
- B15: Item count mismatch
- B21: Negative sale price
- B27: Tax rate different from previous
- B28: Client tax number different
- B29: Client tax number for another client
- B31-B35: Levy amount discrepancies
- A06: Invalid unit price
- A07: Invalid discount
- A08: Invalid tax code
- A09: Invalid tax rate
- A11: Item count not a number

**TIN Validator Errors**:
- T01: Invalid TIN number
- T03: TIN number not found
- T04: TIN stopped
- T05: TIN protected
- T06: Incorrect client TIN PIN

**System Errors**:
- D01: Invoice already exists
- D05: Invoice under stamping
- D06: Stamping engine is down
- IS100: Internal error
- A13: E-VAT unable to reach database

---

## 6. Format Support

### 6.1 JSON Format

Your API accepts and forwards JSON to GRA:

```json
{
  "company": {
    "COMPANY_NAMES": "ABC COMPANY LTD",
    "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
    "COMPANY_TIN": "C00XXXXXXXX"
  },
  "header": {
    "COMPUTATION_TYPE": "INCLUSIVE",
    "FLAG": "INVOICE",
    "SALE_TYPE": "NORMAL",
    "USER_NAME": "JOHN",
    "NUM": "INV-2026-001",
    "INVOICE_DATE": "2026-02-10",
    "CURRENCY": "GHS",
    "EXCHANGE_RATE": "1",
    "CLIENT_NAME": "Customer Ltd",
    "CLIENT_TIN": "C0022825405",
    "TOTAL_VAT": "159",
    "TOTAL_LEVY": "60",
    "TOTAL_AMOUNT": "3438",
    "ITEMS_COUNTS": "2"
  },
  "item_list": [
    {
      "ITMREF": "PROD001",
      "ITMDES": "Product Description",
      "TAXRATE": "15",
      "TAXCODE": "B",
      "LEVY_AMOUNT_A": "2.5",
      "LEVY_AMOUNT_B": "2.5",
      "LEVY_AMOUNT_C": "0",
      "LEVY_AMOUNT_D": "0",
      "QUANTITY": "10",
      "UNITYPRICE": "100",
      "ITEM_CATEGORY": "GOODS"
    }
  ]
}
```

### 6.2 XML Format

Your API accepts and forwards XML to GRA:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<root>
  <company>
    <COMPANY_NAMES>ABC COMPANY LTD</COMPANY_NAMES>
    <COMPANY_SECURITY_KEY>UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH</COMPANY_SECURITY_KEY>
    <COMPANY_TIN>C00XXXXXXXX</COMPANY_TIN>
  </company>
  <header>
    <COMPUTATION_TYPE>INCLUSIVE</COMPUTATION_TYPE>
    <FLAG>INVOICE</FLAG>
    <SALE_TYPE>NORMAL</SALE_TYPE>
    <USER_NAME>JOHN</USER_NAME>
    <NUM>INV-2026-001</NUM>
    <INVOICE_DATE>2026-02-10</INVOICE_DATE>
    <CURRENCY>GHS</CURRENCY>
    <EXCHANGE_RATE>1</EXCHANGE_RATE>
    <CLIENT_NAME>Customer Ltd</CLIENT_NAME>
    <CLIENT_TIN>C0022825405</CLIENT_TIN>
    <TOTAL_VAT>159</TOTAL_VAT>
    <TOTAL_LEVY>60</TOTAL_LEVY>
    <TOTAL_AMOUNT>3438</TOTAL_AMOUNT>
    <ITEMS_COUNTS>2</ITEMS_COUNTS>
  </header>
  <item_list>
    <item>
      <ITMREF>PROD001</ITMREF>
      <ITMDES>Product Description</ITMDES>
      <TAXRATE>15</TAXRATE>
      <TAXCODE>B</TAXCODE>
      <LEVY_AMOUNT_A>2.5</LEVY_AMOUNT_A>
      <LEVY_AMOUNT_B>2.5</LEVY_AMOUNT_B>
      <LEVY_AMOUNT_C>0</LEVY_AMOUNT_C>
      <LEVY_AMOUNT_D>0</LEVY_AMOUNT_D>
      <QUANTITY>10</QUANTITY>
      <UNITYPRICE>100</UNITYPRICE>
      <ITEM_CATEGORY>GOODS</ITEM_CATEGORY>
    </item>
  </item_list>
</root>
```

### 6.3 Format Handling Strategy

- **Accept**: Both JSON and XML from businesses
- **Detect**: Content-Type header (application/json or application/xml)
- **Parse**: Convert to internal model
- **Validate**: Against all GRA rules
- **Forward**: To GRA in same format received
- **Return**: Response in same format as request

---

## 7. Authentication & Security

### 7.1 API Key + HMAC Signature

Every request requires:

```
X-API-Key: <business_api_key>
X-API-Signature: <hmac_sha256_signature>
```

**Signature Generation**:
```
signature = HMAC-SHA256(
  key=api_secret,
  message=<request_method>|<request_path>|<timestamp>|<request_body_hash>
)
```

### 7.2 GRA Credentials Storage

- Store encrypted in database
- Use AES-256 encryption
- Rotate encryption keys regularly
- Never log or expose in responses
- Access only for GRA submission

### 7.3 Rate Limiting

- Per business: 1000 requests/hour
- Per endpoint: 100 requests/minute
- Return 429 Too Many Requests when exceeded
- Include Retry-After header

### 7.4 HTTPS Only

- All communication over HTTPS (TLS 1.2+)
- Certificate pinning recommended
- No HTTP fallback

---

## 8. Response Format

### 8.1 Success Response (202 Accepted)

```json
{
  "submission_id": "uuid-12345",
  "status": "RECEIVED",
  "message": "Invoice received and queued for GRA processing",
  "validation_passed": true,
  "invoice_num": "INV-2026-001",
  "next_action": "Check status using submission_id"
}
```

### 8.2 Success Response (200 OK)

```json
{
  "submission_id": "uuid-12345",
  "invoice_num": "INV-2026-001",
  "status": "SUCCESS",
  "gra_response_code": null,
  "gra_invoice_id": "GRA-INV-2026-001",
  "gra_qr_code": "https://gra.gov.gh/qr/...",
  "gra_receipt_num": "VSDC-REC-12345",
  "submitted_at": "2026-02-10T10:00:00Z",
  "completed_at": "2026-02-10T10:05:00Z",
  "processing_time_ms": 5000
}
```

### 8.3 Error Response (400 Bad Request)

```json
{
  "error_code": "VALIDATION_FAILED",
  "message": "Validation failed: TOTAL_AMOUNT mismatch",
  "submission_id": "uuid-12345",
  "gra_response_code": "B16",
  "gra_response_message": "INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
  "validation_errors": [
    {
      "field": "TOTAL_AMOUNT",
      "error": "B16 - INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT",
      "expected": 3438,
      "actual": 3400
    }
  ],
  "timestamp": "2026-02-10T10:00:00Z"
}
```

### 8.4 Error Response (401 Unauthorized)

```json
{
  "error_code": "AUTH_FAILED",
  "message": "Invalid API Key or signature",
  "timestamp": "2026-02-10T10:00:00Z"
}
```

### 8.5 Error Response (500 Internal Server Error)

```json
{
  "error_code": "SERVER_ERROR",
  "message": "An unexpected error occurred",
  "submission_id": "uuid-12345",
  "timestamp": "2026-02-10T10:00:00Z"
}
```

---

## 9. Submission Status Lifecycle

```
RECEIVED
  ↓ (Validation passed)
PROCESSING
  ↓ (Sent to GRA)
PENDING_GRA
  ↓ (GRA response received)
SUCCESS (or FAILED)
```

**Status Meanings**:
- **RECEIVED**: Submission received by your API, queued for processing
- **PROCESSING**: Being validated and prepared for GRA submission
- **PENDING_GRA**: Sent to GRA, awaiting their response
- **SUCCESS**: GRA accepted and stamped the invoice
- **FAILED**: GRA rejected (check gra_response_code for reason)

---

## 10. Async Processing & Retry Logic

### 10.1 Async Processing

- All submissions are asynchronous (202 Accepted)
- Submissions queued for background processing
- Business polls status or receives webhook notification
- Retry failed submissions with exponential backoff

### 10.2 Retry Strategy

- **Transient Errors** (5xx, 429, network timeouts):
  - Retry up to 5 times
  - Exponential backoff: 1s, 2s, 4s, 8s, 16s
  - Total retry window: ~30 seconds

- **Permanent Errors** (4xx validation errors):
  - Do not retry
  - Return error to business immediately
  - Business must fix and resubmit

- **GRA Unavailable** (D06, A13):
  - Retry up to 10 times
  - Exponential backoff: 5s, 10s, 20s, 40s, 80s, 160s, 320s, 640s, 1280s, 2560s
  - Total retry window: ~1 hour

---

## 11. Webhooks (Optional)

### 11.1 Webhook Registration

```
POST /api/v1/webhooks

Request:
{
  "webhook_url": "https://yourbusiness.com/gra-updates",
  "events": ["invoice.success", "invoice.failed", "refund.success"]
}

Response:
{
  "webhook_id": "uuid-webhook-001",
  "webhook_url": "https://yourbusiness.com/gra-updates",
  "events": ["invoice.success", "invoice.failed", "refund.success"],
  "is_active": true
}
```

### 11.2 Webhook Payload

```json
{
  "event_type": "invoice.success",
  "timestamp": "2026-02-10T10:05:00Z",
  "submission_id": "uuid-12345",
  "data": {
    "invoice_num": "INV-2026-001",
    "status": "SUCCESS",
    "gra_invoice_id": "GRA-INV-2026-001",
    "gra_qr_code": "https://gra.gov.gh/qr/...",
    "completed_at": "2026-02-10T10:05:00Z"
  }
}
```

### 11.3 Webhook Delivery

- Retry failed deliveries up to 5 times
- Exponential backoff between retries
- Signature verification (X-Webhook-Signature header)
- Business must return 200 OK to acknowledge

---

## 12. Audit & Compliance

### 12.1 Audit Logging

Log all API requests:
- Business ID
- Action (SUBMIT_INVOICE, GET_STATUS, etc)
- Endpoint and method
- Request payload (masked sensitive data)
- Response code and status
- Error messages
- IP address and user agent
- Timestamp

### 12.2 Data Retention

- Submissions: Retain indefinitely (compliance requirement)
- Audit logs: Retain for 7 years (tax compliance)
- Webhooks: Retain delivery logs for 90 days
- Sensitive data: Encrypt at rest

### 12.3 Compliance Requirements

- GDPR: Support data deletion requests
- GRA: Maintain audit trail for all submissions
- PCI DSS: If handling payment data
- SOC 2: Security and availability controls

---

## 13. Error Handling Strategy

### 13.1 Validation Errors (Your API)

```
400 Bad Request
- Validation failed
- Don't send to GRA
- Return specific error details
- Business fixes and resubmits
```

### 13.2 GRA Errors

```
200 OK (with error details)
- GRA rejected submission
- Store GRA error code
- Return to business
- Business must fix and resubmit
```

### 13.3 System Errors

```
500 Internal Server Error
- Network, database, or system issue
- Implement retry logic
- Alert administrators
- Business can retry
```

### 13.4 Rate Limit Errors

```
429 Too Many Requests
- Business exceeded rate limit
- Return Retry-After header
- Business should implement backoff
```

---

## 14. Technology Stack

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache**: Redis (optional, for rate limiting)
- **Message Queue**: Celery + Redis (for async processing)
- **Encryption**: AES-256 (credentials), HMAC-SHA256 (signatures)
- **Logging**: Structured logging (JSON format)
- **Monitoring**: Prometheus + Grafana
- **Testing**: pytest + property-based testing

---

## 15. Deployment & Infrastructure

- **Containerization**: Docker
- **Orchestration**: Kubernetes (optional)
- **Load Balancing**: Nginx or AWS ALB
- **Database**: PostgreSQL with replication
- **Backup**: Daily automated backups
- **Monitoring**: Health checks, alerting
- **Scaling**: Horizontal scaling for API servers

---

## 16. Testing Strategy

### 16.1 Unit Tests
- Validation logic
- Tax/levy calculations
- Format conversion (JSON/XML)
- Error handling

### 16.2 Integration Tests
- End-to-end submission flow
- GRA API integration (mock)
- Database operations
- Webhook delivery

### 16.3 Property-Based Tests
- Tax calculations across all scenarios
- Validation rules consistency
- Format conversion correctness

### 16.4 Load Testing
- 1000+ concurrent submissions
- Response time under load
- Database performance

---

## 17. Success Criteria

✅ All GRA error codes handled correctly
✅ 100% validation accuracy
✅ <5 second average response time
✅ 99.9% uptime
✅ Zero data loss
✅ Full audit trail
✅ Multi-tenant isolation
✅ Secure credential storage
✅ Comprehensive error messages
✅ Webhook reliability

---

## 18. Future Enhancements

- Mobile app for submission tracking
- Advanced analytics dashboard
- Bulk submission support
- API rate tier management
- Custom validation rules per business
- Integration with accounting software
- Real-time notifications via SMS/Email
- Machine learning for fraud detection

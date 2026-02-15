# GRA External Integration API - Quick Reference Guide

## Project at a Glance

**What**: Compliance gateway for GRA E-VAT invoice submissions
**Who**: Registered businesses in Ghana
**Why**: Simplify GRA compliance, ensure data accuracy, prevent rejections
**How**: Validate + Forward to GRA + Track status

---

## 10 Core Modules

| Module | Purpose | Key Endpoints |
|--------|---------|---------------|
| **Invoicing** | Submit & track invoices | POST /invoices/submit, GET /invoices/{id}/status |
| **Refunds** | Submit & track refunds | POST /refunds/submit, GET /refunds/{id}/status |
| **Purchases** | Submit & track purchases | POST /purchases/submit, GET /purchases/{id}/status |
| **Items** | Register item codes | POST /items/register, GET /items/{ref} |
| **Inventory** | Update stock levels | POST /inventory/update |
| **TIN Validator** | Validate customer TINs | POST /tin/validate |
| **Tags** | Custom tag descriptions | POST /tags/register, GET /tags/{code} |
| **Z-Reports** | End-of-day reports | POST /reports/z-report, GET /reports/z-report/{date} |
| **VSDC Health** | Check GRA system status | POST /vsdc/health-check, GET /vsdc/status |
| **System Health** | API health check | GET /health |

---

## Authentication

Every request needs:
```
X-API-Key: <business_api_key>
X-API-Signature: HMAC-SHA256(api_secret, request_body)
```

---

## Validation Checklist

Before submitting to GRA, validate:

- [ ] Company credentials (A01)
- [ ] Client name provided (B05)
- [ ] Client TIN format: 11 or 15 chars (B051)
- [ ] Invoice number unique (B20)
- [ ] TOTAL_AMOUNT = sum of items + VAT + levies (B16)
- [ ] TOTAL_VAT = sum of item VATs (B18)
- [ ] TOTAL_LEVY = sum of item levies (B34)
- [ ] ITEMS_COUNTS matches item_list length (B15)
- [ ] All quantities positive (B10, B11)
- [ ] All prices positive (B21, A06)
- [ ] TAXCODE in [A, B, C, D, E] (A08)
- [ ] TAXRATE in [0, 15, 3] (A09)
- [ ] CURRENCY = GHS (B70)
- [ ] EXCHANGE_RATE = 1 (B70)
- [ ] For refunds: REFUND_ID provided (A05)
- [ ] Levy calculations correct (B31-B35)

---

## Tax & Levy Rates

| Type | Rate | Formula |
|------|------|---------|
| LEVY_A (NHIL) | 2.5% | base_amount × 0.025 |
| LEVY_B (GETFund) | 2.5% | base_amount × 0.025 |
| LEVY_C (COVID) | 1% | base_amount × 0.01 |
| LEVY_D (Tourism/CST) | 1-5% | varies |
| VAT (TAX_B) | 15% | (base + levies) × 0.15 |
| VAT (TAX_A/C/D) | 0% | - |
| VAT (TAX_E) | 3% | base × 0.03 |

---

## GRA Error Codes (Quick Lookup)

### Authentication (A01, B01)
- A01: Company credentials invalid
- B01: Client TIN PIN incorrect

### Amounts (B16, B18, B34)
- B16: Total amount mismatch
- B18: Total VAT mismatch
- B34: Total levy mismatch

### Items (B05-B15, B21, B27-B29)
- B05: Client name missing
- B07: Code missing
- B09: Description missing
- B10: Quantity missing
- B11: Negative quantity
- B15: Item count mismatch
- B21: Negative price

### Levies (B31-B35)
- B31: LEVY_A mismatch
- B32: LEVY_B mismatch
- B33: LEVY_C mismatch
- B34: Total levy mismatch
- B35: LEVY_D mismatch

### Refunds (A05)
- A05: Missing original invoice number

### Currency (B70)
- B70: Wrong currency or exchange rate

### Duplicates (B20, D01)
- B20: Invoice already sent
- D01: Invoice already exists

### System (D05, D06, IS100, A13)
- D05: Invoice under stamping
- D06: Stamping engine down
- IS100: Internal error
- A13: Database unavailable

---

## Response Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 202 | Accepted (async) | Poll for status |
| 200 | Success | Use returned data |
| 400 | Validation failed | Fix data, resubmit |
| 401 | Auth failed | Check API key/signature |
| 403 | Forbidden | Check business status |
| 404 | Not found | Check submission ID |
| 429 | Rate limited | Wait and retry |
| 500 | Server error | Retry with backoff |
| 503 | GRA unavailable | Retry later |

---

## Submission Lifecycle

```
1. Business submits invoice (JSON/XML)
   ↓
2. Your API authenticates (API Key + Signature)
   ↓
3. Your API validates (50+ error codes)
   ↓
4. Your API stores submission (database)
   ↓
5. Your API returns 202 Accepted (submission_id)
   ↓
6. Background job processes submission
   ↓
7. Your API submits to GRA (with business's GRA credentials)
   ↓
8. GRA processes and responds
   ↓
9. Your API stores GRA response
   ↓
10. Your API updates status (SUCCESS or FAILED)
   ↓
11. Your API sends webhook (if configured)
   ↓
12. Business polls or receives webhook notification
```

---

## Retry Logic

### Transient Errors (Retry)
- Network timeouts
- 5xx server errors
- 429 rate limits
- GRA unavailable (D06, A13)

**Strategy**: Exponential backoff (1s, 2s, 4s, 8s, 16s, 32s)
**Max Attempts**: 5
**Total Window**: ~30 seconds

### Permanent Errors (Don't Retry)
- 400 validation errors
- 401 authentication errors
- 403 authorization errors
- GRA business logic errors (B16, B18, etc)

**Strategy**: Return error to business immediately
**Action**: Business must fix and resubmit

---

## Data Format Support

### JSON
```
Content-Type: application/json
Request: GRA JSON format
Response: JSON
```

### XML
```
Content-Type: application/xml
Request: GRA XML format
Response: XML
```

**Strategy**: Accept both, validate internally, forward in same format

---

## Security Checklist

- [ ] HTTPS only (TLS 1.2+)
- [ ] API Key + HMAC signature on every request
- [ ] GRA credentials encrypted at rest (AES-256)
- [ ] Sensitive data masked in logs
- [ ] Rate limiting enabled (1000 req/hour per business)
- [ ] Multi-tenant isolation enforced
- [ ] Audit logs retained (7 years)
- [ ] Request timeout (30 seconds)
- [ ] CORS configured
- [ ] Security headers set

---

## Performance Targets

| Metric | Target |
|--------|--------|
| API Response Time | <500ms |
| Status Check | <1s |
| GRA Processing | <30s |
| Webhook Delivery | <5s |
| Throughput | 1000+ submissions/hour |
| Concurrent Requests | 100+ |
| Uptime | 99.5% |

---

## Database Tables (Quick Reference)

| Table | Purpose |
|-------|---------|
| businesses | Business registration |
| submissions | All submission records |
| invoices | Invoice details |
| invoice_items | Invoice line items |
| refunds | Refund details |
| refund_items | Refund line items |
| purchases | Purchase details |
| purchase_items | Purchase line items |
| items | Item master data |
| inventory | Stock levels |
| tin_validations | TIN validation cache |
| tag_descriptions | Custom tags |
| z_reports | Z-Report history |
| vsdc_health_checks | Health check history |
| audit_logs | Complete audit trail |
| webhooks | Webhook configs |
| webhook_deliveries | Webhook delivery logs |

---

## Common Error Scenarios

### Scenario 1: Total Amount Mismatch
```
Error: B16 - INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT
Fix: Recalculate TOTAL_AMOUNT = sum(items) + TOTAL_VAT + TOTAL_LEVY
```

### Scenario 2: Levy Amount Mismatch
```
Error: B31-B35 - LEVY AMOUNT ARE DIFFERENT
Fix: Verify levy calculations:
  LEVY_A = UNITYPRICE × 2.5%
  LEVY_B = UNITYPRICE × 2.5%
  LEVY_C = UNITYPRICE × 1%
```

### Scenario 3: Duplicate Invoice
```
Error: B20 - INVOICE REFERENCE ALREADY SENT
Fix: Use unique invoice number (NUM field)
```

### Scenario 4: Missing Refund Reference
```
Error: A05 - MISSING ORIGINAL INVOICE NUMBER
Fix: Provide REFUND_ID = original invoice NUM
```

### Scenario 5: Invalid TIN Format
```
Error: B051 - TAX NUMBER FORMAT NOT ACCEPTED
Fix: Ensure CLIENT_TIN is 11 or 15 characters
```

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] FastAPI project setup
- [ ] PostgreSQL database
- [ ] Project structure
- [ ] Security framework

### Phase 2: Models & Schemas
- [ ] SQLAlchemy models
- [ ] Pydantic schemas
- [ ] Format converters

### Phase 3: Validation
- [ ] Error code validation
- [ ] Tax/levy calculations
- [ ] Business logic validation

### Phase 4: GRA Integration
- [ ] GRA API client
- [ ] Invoice submission
- [ ] Items & inventory
- [ ] TIN validation
- [ ] Z-Reports & health

### Phase 5: API Endpoints
- [ ] All 20+ endpoints
- [ ] Request/response handling
- [ ] Error handling

### Phase 6: Async Processing
- [ ] Task queue
- [ ] Background processing
- [ ] Retry logic

### Phase 7: Webhooks
- [ ] Webhook management
- [ ] Webhook delivery
- [ ] Event types

### Phase 8: Audit & Compliance
- [ ] Audit logging
- [ ] Data security
- [ ] Compliance checks

### Phase 9: Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] End-to-end tests
- [ ] Performance tests
- [ ] Security tests

### Phase 10: Documentation & Deployment
- [ ] API documentation
- [ ] Integration guide
- [ ] Deployment guide
- [ ] Operations guide

---

## Key Files

| File | Purpose |
|------|---------|
| design.md | Complete system design |
| requirements.md | Detailed requirements |
| tasks.md | Implementation tasks |
| SUMMARY.md | Project overview |
| QUICK_REFERENCE.md | This file |

---

## GRA API Endpoints

### Test Environment
```
Invoice/Refund (JSON): https://apitest.e-vatgh.com/evat_apiqa/post_receipt_Json.jsp
Invoice/Refund (XML): https://apitest.e-vatgh.com/evat_apiqa/post_receipt.jsp
Items (JSON): https://apitest.e-vatgh.com/evat_apiqa/post_item_JSON.jsp
Items (XML): https://apitest.e-vatgh.com/evat_apiqa/post_item.jsp
Inventory (JSON): https://apitest.e-vatgh.com/evat_apiqa/post_inventory_JSON.jsp
Inventory (XML): https://apitest.e-vatgh.com/evat_apiqa/post_inventory.jsp
TIN Validator (JSON): https://apitest.e-vatgh.com/evat_apiqa/tin_validator_JSON.jsp
TIN Validator (XML): https://apitest.e-vatgh.com/evat_apiqa/tin_validator.jsp
Z-Report (JSON): https://apitest.e-vatgh.com/evat_apiqa/requestZd_report_Json.jsp
Z-Report (XML): https://apitest.e-vatgh.com/evat_apiqa/zReport.jsp
Health Check (JSON): https://apitest.e-vatgh.com/evat_apiqa/health_check_request_JSON.jsp
Health Check (XML): https://apitest.e-vatgh.com/evat_apiqa/health_check_request.jsp
Signature Request (JSON): https://apitest.e-vatgh.com/evat_apiqa/get_Response_JSON.jsp
```

### Production Environment
```
Replace "apitest.e-vatgh.com/evat_apiqa" with "api.e-vatgh.com/evat_api"
```

---

## Useful Commands (Future)

```bash
# Start development server
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_validation.py::test_levy_calculation -v

# Database migrations
alembic upgrade head
alembic downgrade -1

# Generate API docs
python -m mkdocs serve

# Docker build
docker build -t gra-api:latest .

# Docker run
docker run -p 8000:8000 gra-api:latest
```

---

## Support & Resources

- **GRA E-VAT API Docs**: https://documenter.getpostman.com/view/20074551/2s8Z76xVYR
- **GRA Official Website**: https://www.gra.gov.gh
- **Project Specification**: See design.md, requirements.md, tasks.md

---

**Last Updated**: February 10, 2026
**Status**: Ready for Implementation ✅

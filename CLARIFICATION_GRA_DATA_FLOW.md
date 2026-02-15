# GRA Data Flow Clarification

## Question: Is our data hitting the GRA server?

**Answer: YES, but only during invoice/refund/purchase SUBMISSION, NOT during signature retrieval.**

---

## Data Flow Breakdown

### 1. **Invoice Submission Flow** (Data DOES hit GRA)
When a user submits an invoice via `POST /api/v1/invoices`:

```
User Request → Your API → GRA Server (https://apitest.e-vatgh.com/evat_apiqa/)
                              ↓
                        GRA validates & stamps
                              ↓
                        Returns signature data
                              ↓
                        Your API stores in DB
```

**What happens:**
- Your API calls `SubmissionProcessor.process_json_submission()` (app/services/submission_processor.py)
- This injects GRA credentials (TIN, company name, security key) into the payload
- Calls `gra_client.submit_json()` which makes an HTTP request to GRA's sandbox
- GRA returns signature details: `ysdcid`, `ysdcrecnum`, `ysdcintdata`, `ysdcnrc`, QR code, etc.
- Your API stores these in the database
- Your API starts polling GRA for final response status

**GRA Endpoints Used:**
- JSON: `https://apitest.e-vatgh.com/evat_apiqa/post_receipt_Json.jsp`
- XML: `https://apitest.e-vatgh.com/evat_apiqa/post_receipt.jsp`

---

### 2. **Signature Retrieval Flow** (Data does NOT hit GRA)
When a user retrieves a signature via `GET /api/v1/invoices/{submission_id}/signature`:

```
User Request → Your API → Database Query
                              ↓
                        Return cached signature
                              ↓
                        (No GRA call)
```

**What happens:**
- Your API queries the database for the submission
- Returns the previously stored signature data
- **No call to GRA** - it's just reading from your database

**This is why the tests pass:**
- Tests create mock data in the database
- Tests call the signature endpoint
- Endpoint returns the mock data
- No actual GRA server interaction needed

---

## Test vs. Production

### Tests (Current)
```
✅ Create mock submission in DB
✅ Call GET /api/v1/invoices/{submission_id}/signature
✅ Return mock data from DB
✅ All 10 tests PASSING
```

### Production (Real GRA Integration)
```
1. User submits invoice via POST /api/v1/invoices
   → Data hits GRA server
   → GRA stamps and returns signature
   → Signature stored in DB

2. User retrieves signature via GET /api/v1/invoices/{submission_id}/signature
   → Data retrieved from DB
   → No GRA call
```

---

## Key Points

1. **Signature Endpoint is Read-Only**: The `GET /api/v1/invoices/{submission_id}/signature` endpoint only reads from your database. It doesn't make any GRA calls.

2. **GRA Integration Happens at Submission**: The actual GRA server interaction happens when invoices/refunds/purchases are submitted via `POST` endpoints.

3. **Polling Service**: After initial submission, your API automatically polls GRA for the final response status (see `GRAPollingService.poll_for_response()` in app/services/gra_polling.py).

4. **Test Data**: The tests use mock data stored in PostgreSQL. They simulate what would happen after a real GRA submission.

5. **Sandbox vs. Production**: 
   - Tests use: `https://apitest.e-vatgh.com/evat_apiqa/` (GRA Sandbox)
   - Credentials: `C00XXXXXXXX` (test TIN)
   - This is configured in `.env` as `GRA_API_BASE_URL`

---

## Test Results Summary

✅ **All 10 Signature Endpoint Tests PASSING**
- Test 1: Successful retrieval with all VSDC fields
- Test 2: Missing submission returns 404
- Test 3: Invalid API key returns 401
- Test 4: Cross-tenant isolation enforced
- Test 5: Pending status handled correctly
- Test 6: Failed status with error details
- Test 7: QR code format validation
- Test 8: All VSDC fields populated
- Test 9: Refund submissions return 404
- Test 10: Response schema validation

**Database**: PostgreSQL (`API_s_GRA` at `localhost:5432`)
**Pass Rate**: 100% (10/10)

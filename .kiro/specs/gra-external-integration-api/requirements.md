# GRA External Integration API - Detailed Requirements Specification

## 1. Executive Summary

The GRA External Integration API is a comprehensive compliance gateway that enables registered businesses in Ghana to securely submit invoices, refunds, purchases, and other tax-related documents to the Ghana Revenue Authority (GRA) E-VAT system. The API acts as an intermediary, validating all submissions against GRA rules before forwarding them to the official GRA E-VAT API.

**Key Objectives:**
- Provide a simplified, standardized interface for businesses
- Ensure 100% compliance with GRA E-VAT API specifications
- Maintain strict multi-tenant isolation
- Implement comprehensive audit trails for compliance
- Handle all GRA error codes and validation rules
- Support both JSON and XML data formats
- Provide real-time status tracking and notifications

---

## 2. Functional Requirements

### 2.1 Authentication & Authorization

#### 2.1.1 Business Registration
- **REQ-AUTH-001**: Each business must register with the platform and receive unique API credentials
- **REQ-AUTH-002**: API credentials consist of API Key (public) and API Secret (private)
- **REQ-AUTH-003**: Businesses must provide their GRA credentials (TIN, Company Name, Security Key)
- **REQ-AUTH-004**: GRA credentials must be encrypted at rest using AES-256
- **REQ-AUTH-005**: GRA credentials must never be logged or exposed in responses

#### 2.1.2 Request Authentication
- **REQ-AUTH-006**: Every API request must include X-API-Key header
- **REQ-AUTH-007**: Every API request must include X-API-Signature header (HMAC-SHA256)
- **REQ-AUTH-008**: Signature must be calculated as: HMAC-SHA256(API_SECRET, request_body)
- **REQ-AUTH-009**: Invalid signatures must result in 401 Unauthorized response
- **REQ-AUTH-010**: Expired or revoked API keys must result in 403 Forbidden response

#### 2.1.3 Multi-Tenant Isolation
- **REQ-AUTH-011**: Businesses can only access their own submissions
- **REQ-AUTH-012**: Businesses can only access their own items and inventory
- **REQ-AUTH-013**: Businesses can only access their own audit logs
- **REQ-AUTH-014**: Cross-tenant data access attempts must be logged and rejected

### 2.2 Invoice Management

#### 2.2.1 Invoice Submission
- **REQ-INV-001**: Accept invoice submissions in JSON or XML format
- **REQ-INV-002**: Validate all required fields per GRA specification
- **REQ-INV-003**: Calculate and verify all tax and levy amounts
- **REQ-INV-004**: Ensure invoice numbers are unique per business
- **REQ-INV-005**: Support both INCLUSIVE and EXCLUSIVE computation types
- **REQ-INV-006**: Support all FLAG types: INVOICE, REFUND, PROFORMA, PARTIAL_REFUND, PURCHASE
- **REQ-INV-007**: Return 202 Accepted with submission_id for async processing
- **REQ-INV-008**: Store complete request and response for audit trail

#### 2.2.2 Invoice Validation
- **REQ-INV-009**: Validate TOTAL_AMOUNT = sum of all items + VAT + levies
- **REQ-INV-010**: Validate TOTAL_VAT = sum of all item VATs
- **REQ-INV-011**: Validate TOTAL_LEVY = sum of all item levies
- **REQ-INV-012**: Validate ITEMS_COUNTS matches actual item_list length
- **REQ-INV-013**: Validate all item quantities are positive
- **REQ-INV-014**: Validate all item prices are positive
- **REQ-INV-015**: Validate CLIENT_NAME is provided
- **REQ-INV-016**: Validate CLIENT_TIN format (11 or 15 characters)
- **REQ-INV-017**: Validate CURRENCY is GHS
- **REQ-INV-018**: Validate EXCHANGE_RATE is 1 for GHS
- **REQ-INV-019**: Validate INVOICE_DATE format (YYYY-MM-DD)
- **REQ-INV-020**: Validate TAXCODE values (A, B, C, D, E)
- **REQ-INV-021**: Validate TAXRATE values (0, 15, 3)

#### 2.2.3 Invoice Status Tracking
- **REQ-INV-022**: Provide endpoint to check submission status
- **REQ-INV-023**: Return GRA-issued invoice ID upon success
- **REQ-INV-024**: Return GRA QR code upon success
- **REQ-INV-025**: Return GRA receipt number upon success
- **REQ-INV-026**: Return error code and message upon failure
- **REQ-INV-027**: Support status values: RECEIVED, PROCESSING, PENDING_GRA, SUCCESS, FAILED

#### 2.2.4 Invoice Signature Retrieval
- **REQ-INV-028**: Provide endpoint to retrieve GRA signature details
- **REQ-INV-029**: Return ysdcid, ysdcrecnum, ysdcintdata, ysdcnrc
- **REQ-INV-030**: Return GRA QR code for printing

### 2.3 Refund Management

#### 2.3.1 Refund Submission
- **REQ-REF-001**: Accept refund submissions in JSON or XML format
- **REQ-REF-002**: Require REFUND_ID field linking to original invoice
- **REQ-REF-003**: Validate original invoice exists and belongs to business
- **REQ-REF-004**: Validate refund amount does not exceed original invoice
- **REQ-REF-005**: Support partial refunds
- **REQ-REF-006**: Return 202 Accepted with submission_id

#### 2.3.2 Refund Validation
- **REQ-REF-007**: Validate REFUND_ID is not empty (error A05)
- **REQ-REF-008**: Validate REFUND_ID references existing invoice
- **REQ-REF-009**: Validate refund totals match item calculations
- **REQ-REF-010**: Validate refund date is after original invoice date

#### 2.3.3 Refund Status Tracking
- **REQ-REF-011**: Provide endpoint to check refund status
- **REQ-REF-012**: Return GRA refund ID upon success
- **REQ-REF-013**: Return error details upon failure

### 2.4 Purchase Management

#### 2.4.1 Purchase Submission
- **REQ-PUR-001**: Accept purchase submissions in JSON or XML format
- **REQ-PUR-002**: Validate all required fields per GRA specification
- **REQ-PUR-003**: Support supplier TIN validation
- **REQ-PUR-004**: Return 202 Accepted with submission_id

#### 2.4.2 Purchase Status Tracking
- **REQ-PUR-005**: Provide endpoint to check purchase status
- **REQ-PUR-006**: Return GRA purchase ID upon success

### 2.5 Items Management

#### 2.5.1 Item Registration
- **REQ-ITEM-001**: Accept item registration in JSON or XML format
- **REQ-ITEM-002**: Validate ITEM_REF is unique per business
- **REQ-ITEM-003**: Validate ITEM_NAME is provided
- **REQ-ITEM-004**: Validate TAX_CODE is valid (A, B, C, D, E)
- **REQ-ITEM-005**: Store item details in database
- **REQ-ITEM-006**: Submit items to GRA for registration
- **REQ-ITEM-007**: Track item registration status

#### 2.5.2 Item Retrieval
- **REQ-ITEM-008**: Provide endpoint to retrieve item details
- **REQ-ITEM-009**: Return item details including GRA registration status

### 2.6 Inventory Management

#### 2.6.1 Inventory Update
- **REQ-INV-001**: Accept inventory updates in JSON or XML format
- **REQ-INV-002**: Validate NIKI_CODE is provided
- **REQ-INV-003**: Validate ITEM_CODE references registered item
- **REQ-INV-004**: Validate QTY is numeric and non-negative
- **REQ-INV-005**: Update inventory levels in database
- **REQ-INV-006**: Submit inventory updates to GRA

### 2.7 TIN Validation

#### 2.7.1 TIN Validator
- **REQ-TIN-001**: Accept TIN validation requests in JSON or XML format
- **REQ-TIN-002**: Validate TIN format (11 or 15 characters)
- **REQ-TIN-003**: Submit TIN to GRA for validation
- **REQ-TIN-004**: Return validation status (VALID, INVALID, STOPPED, PROTECTED)
- **REQ-TIN-005**: Cache TIN validation results for 24 hours
- **REQ-TIN-006**: Return taxpayer name upon successful validation

### 2.8 Tag Descriptions

#### 2.8.1 Tag Management
- **REQ-TAG-001**: Allow businesses to register custom tag descriptions
- **REQ-TAG-002**: Store tag code, description, and category
- **REQ-TAG-003**: Provide endpoint to retrieve tag descriptions
- **REQ-TAG-004**: Support tag updates

### 2.9 Z-Reports

#### 2.9.1 Z-Report Retrieval
- **REQ-ZREP-001**: Accept Z-Report requests in JSON or XML format
- **REQ-ZREP-002**: Validate ZD_DATE format (YYYY-MM-DD)
- **REQ-ZREP-003**: Submit Z-Report request to GRA
- **REQ-ZREP-004**: Return aggregated data: inv_close, inv_count, inv_open, inv_vat, inv_total, inv_levy
- **REQ-ZREP-005**: Store Z-Report in database for historical tracking

### 2.10 VSDC Health Check

#### 2.10.1 Health Check
- **REQ-HEALTH-001**: Accept health check requests in JSON or XML format
- **REQ-HEALTH-002**: Submit health check to GRA VSDC
- **REQ-HEALTH-003**: Return VSDC status (UP, DOWN, DEGRADED)
- **REQ-HEALTH-004**: Return SDC_ID upon successful check
- **REQ-HEALTH-005**: Cache health status for 5 minutes
- **REQ-HEALTH-006**: Provide endpoint to retrieve cached health status

### 2.11 System Health

#### 2.11.1 API Health Check
- **REQ-SYS-001**: Provide /health endpoint
- **REQ-SYS-002**: Return API status, database status, GRA API status
- **REQ-SYS-003**: Return uptime information
- **REQ-SYS-004**: Return API version

---

## 3. Data Format Requirements

### 3.1 JSON Format Support
- **REQ-FMT-001**: Accept Content-Type: application/json
- **REQ-FMT-002**: Parse JSON request bodies
- **REQ-FMT-003**: Validate JSON schema against GRA specification
- **REQ-FMT-004**: Return JSON responses

### 3.2 XML Format Support
- **REQ-FMT-005**: Accept Content-Type: application/xml
- **REQ-FMT-006**: Parse XML request bodies
- **REQ-FMT-007**: Validate XML schema against GRA specification
- **REQ-FMT-008**: Return XML responses
- **REQ-FMT-009**: Convert between JSON and XML internally

### 3.3 Format Conversion
- **REQ-FMT-010**: Automatically detect request format from Content-Type
- **REQ-FMT-011**: Return response in same format as request
- **REQ-FMT-012**: Handle format conversion errors gracefully

---

## 4. Tax & Levy Calculation Requirements

### 4.1 Levy Calculations
- **REQ-TAX-001**: Calculate LEVY_A (NHIL) = base_amount × 2.5%
- **REQ-TAX-002**: Calculate LEVY_B (GETFund) = base_amount × 2.5%
- **REQ-TAX-003**: Calculate LEVY_C (COVID) = base_amount × 1%
- **REQ-TAX-004**: Calculate LEVY_D (Tourism/CST) = base_amount × 1% or 5%
- **REQ-TAX-005**: Verify levy calculations match business-provided values
- **REQ-TAX-006**: Return error B31-B35 if levy amounts differ

### 4.2 VAT Calculations
- **REQ-TAX-007**: Calculate VAT for TAX_B (Taxable) = 15%
- **REQ-TAX-008**: Calculate VAT for TAX_A (Exempted) = 0%
- **REQ-TAX-009**: Calculate VAT for TAX_C (Export) = 0%
- **REQ-TAX-010**: Calculate VAT for TAX_D (Non-Taxable) = 0%
- **REQ-TAX-011**: Calculate VAT for TAX_E (Non-VAT) = 3%
- **REQ-TAX-012**: Verify VAT calculations match business-provided values
- **REQ-TAX-013**: Return error B18 if total VAT differs

### 4.3 Computation Types
- **REQ-TAX-014**: Support INCLUSIVE computation (VAT/levies included in unit price)
- **REQ-TAX-015**: Support EXCLUSIVE computation (VAT/levies added to unit price)
- **REQ-TAX-016**: Correctly extract net price for INCLUSIVE type
- **REQ-TAX-017**: Correctly add taxes for EXCLUSIVE type

### 4.4 Rounding & Precision
- **REQ-TAX-018**: Use 2 decimal places for all monetary values
- **REQ-TAX-019**: Round using standard rounding (0.5 rounds up)
- **REQ-TAX-020**: Detect and report rounding errors

---

## 5. Validation & Error Handling Requirements

### 5.1 GRA Error Code Handling
- **REQ-ERR-001**: Implement all 50+ GRA error codes
- **REQ-ERR-002**: Return appropriate HTTP status codes (400, 401, 403, 404, 429, 500, 503)
- **REQ-ERR-003**: Include GRA error code in response
- **REQ-ERR-004**: Include human-readable error message
- **REQ-ERR-005**: Include field-level validation errors where applicable

### 5.2 Pre-Submission Validation
- **REQ-ERR-006**: Validate all data before submitting to GRA
- **REQ-ERR-007**: Reject invalid submissions with 400 Bad Request
- **REQ-ERR-008**: Provide specific validation error details
- **REQ-ERR-009**: Do not submit invalid data to GRA

### 5.3 GRA Response Handling
- **REQ-ERR-010**: Parse GRA error responses
- **REQ-ERR-011**: Map GRA error codes to business-friendly messages
- **REQ-ERR-012**: Store GRA error details for audit trail
- **REQ-ERR-013**: Implement retry logic for transient errors (D06, IS100, A13)

### 5.4 Error Response Format
- **REQ-ERR-014**: Return consistent error response format
- **REQ-ERR-015**: Include error_code, message, submission_id, timestamp
- **REQ-ERR-016**: Include validation_errors array for validation failures
- **REQ-ERR-017**: Include gra_response_code for GRA-originated errors

---

## 6. Async Processing Requirements

### 6.1 Submission Processing
- **REQ-ASYNC-001**: Process submissions asynchronously
- **REQ-ASYNC-002**: Return 202 Accepted immediately upon receipt
- **REQ-ASYNC-003**: Queue submission for background processing
- **REQ-ASYNC-004**: Validate submission in background
- **REQ-ASYNC-005**: Submit to GRA in background
- **REQ-ASYNC-006**: Poll GRA for response
- **REQ-ASYNC-007**: Update submission status upon completion

### 6.2 Retry Logic
- **REQ-ASYNC-008**: Implement exponential backoff (1s, 2s, 4s, 8s, 16s, 32s)
- **REQ-ASYNC-009**: Maximum 5 retry attempts
- **REQ-ASYNC-010**: Retry only transient errors (network, timeout, GRA unavailable)
- **REQ-ASYNC-011**: Do not retry validation errors
- **REQ-ASYNC-012**: Move failed submissions to dead letter queue after max retries

### 6.3 Status Tracking
- **REQ-ASYNC-013**: Track submission status throughout processing
- **REQ-ASYNC-014**: Update status in database
- **REQ-ASYNC-015**: Provide status endpoint for businesses
- **REQ-ASYNC-016**: Include processing time in status response

---

## 7. Webhook Requirements

### 7.1 Webhook Management
- **REQ-WEBHOOK-001**: Allow businesses to register webhook URLs
- **REQ-WEBHOOK-002**: Support webhook updates
- **REQ-WEBHOOK-003**: Support webhook deletion
- **REQ-WEBHOOK-004**: Support webhook listing
- **REQ-WEBHOOK-005**: Validate webhook URLs before registration

### 7.2 Webhook Delivery
- **REQ-WEBHOOK-006**: Send webhook notifications upon status changes
- **REQ-WEBHOOK-007**: Include submission details in webhook payload
- **REQ-WEBHOOK-008**: Sign webhook payloads with HMAC-SHA256
- **REQ-WEBHOOK-009**: Implement webhook delivery retry logic
- **REQ-WEBHOOK-010**: Maximum 5 webhook delivery attempts
- **REQ-WEBHOOK-011**: Log all webhook deliveries

### 7.3 Webhook Events
- **REQ-WEBHOOK-012**: Support invoice.success event
- **REQ-WEBHOOK-013**: Support invoice.failed event
- **REQ-WEBHOOK-014**: Support refund.success event
- **REQ-WEBHOOK-015**: Support refund.failed event
- **REQ-WEBHOOK-016**: Support purchase.success event
- **REQ-WEBHOOK-017**: Support purchase.failed event

---

## 8. Audit & Compliance Requirements

### 8.1 Audit Logging
- **REQ-AUDIT-001**: Log all API requests with timestamp
- **REQ-AUDIT-002**: Log all API responses with status code
- **REQ-AUDIT-003**: Log all GRA submissions
- **REQ-AUDIT-004**: Log all GRA responses
- **REQ-AUDIT-005**: Log all validation errors
- **REQ-AUDIT-006**: Log all authentication attempts
- **REQ-AUDIT-007**: Log all authorization failures

### 8.2 Sensitive Data Protection
- **REQ-AUDIT-008**: Mask API secrets in logs
- **REQ-AUDIT-009**: Mask GRA security keys in logs
- **REQ-AUDIT-010**: Mask customer TINs in logs (show only last 4 digits)
- **REQ-AUDIT-011**: Never log full request/response bodies for sensitive endpoints
- **REQ-AUDIT-012**: Encrypt sensitive data at rest

### 8.3 Data Retention
- **REQ-AUDIT-013**: Retain audit logs for minimum 7 years
- **REQ-AUDIT-014**: Retain submission records for minimum 7 years
- **REQ-AUDIT-015**: Implement data archival strategy
- **REQ-AUDIT-016**: Support audit log retrieval by date range

---

## 9. Security Requirements

### 9.1 Authentication & Authorization
- **REQ-SEC-001**: Enforce HTTPS for all endpoints
- **REQ-SEC-002**: Implement API key authentication
- **REQ-SEC-003**: Implement HMAC signature verification
- **REQ-SEC-004**: Implement rate limiting (100 requests/minute per business)
- **REQ-SEC-005**: Implement request timeout (30 seconds)

### 9.2 Data Protection
- **REQ-SEC-006**: Encrypt GRA credentials at rest (AES-256)
- **REQ-SEC-007**: Encrypt sensitive fields in database
- **REQ-SEC-008**: Use secure password hashing for internal credentials
- **REQ-SEC-009**: Implement key rotation strategy
- **REQ-SEC-010**: Support credential revocation

### 9.3 Input Validation
- **REQ-SEC-011**: Validate all input data
- **REQ-SEC-012**: Prevent SQL injection attacks
- **REQ-SEC-013**: Prevent XML injection attacks
- **REQ-SEC-014**: Prevent XSS attacks
- **REQ-SEC-015**: Sanitize all user inputs

### 9.4 CORS & Headers
- **REQ-SEC-016**: Implement CORS policy
- **REQ-SEC-017**: Set security headers (X-Content-Type-Options, X-Frame-Options, etc)
- **REQ-SEC-018**: Implement CSRF protection

---

## 10. Performance Requirements

### 10.1 Response Times
- **REQ-PERF-001**: API response time < 500ms for validation endpoints
- **REQ-PERF-002**: API response time < 1s for status check endpoints
- **REQ-PERF-003**: GRA submission processing < 30 seconds
- **REQ-PERF-004**: Webhook delivery < 5 seconds

### 10.2 Throughput
- **REQ-PERF-005**: Support minimum 100 concurrent requests
- **REQ-PERF-006**: Support minimum 1000 submissions per hour
- **REQ-PERF-007**: Support minimum 10,000 audit log entries per day

### 10.3 Availability
- **REQ-PERF-008**: Target 99.5% uptime
- **REQ-PERF-009**: Support graceful degradation when GRA API is unavailable
- **REQ-PERF-010**: Implement health checks every 5 minutes

---

## 11. Integration Requirements

### 11.1 GRA API Integration
- **REQ-INT-001**: Support GRA test environment (apitest.e-vatgh.com)
- **REQ-INT-002**: Support GRA production environment (api.e-vatgh.com)
- **REQ-INT-003**: Implement environment switching
- **REQ-INT-004**: Handle GRA API timeouts (30 seconds)
- **REQ-INT-005**: Handle GRA API errors gracefully

### 11.2 Database Integration
- **REQ-INT-006**: Use PostgreSQL 12+
- **REQ-INT-007**: Implement connection pooling
- **REQ-INT-008**: Support database migrations
- **REQ-INT-009**: Implement database backups

---

## 12. Reporting & Analytics Requirements

### 12.1 Submission Reporting
- **REQ-REPORT-001**: Track submission success rate
- **REQ-REPORT-002**: Track submission failure rate
- **REQ-REPORT-003**: Track average processing time
- **REQ-REPORT-004**: Track error code frequency

### 12.2 Business Reporting
- **REQ-REPORT-005**: Provide submission history per business
- **REQ-REPORT-006**: Provide error summary per business
- **REQ-REPORT-007**: Provide audit trail per business

---

## 13. Documentation Requirements

### 13.1 API Documentation
- **REQ-DOC-001**: Create OpenAPI/Swagger documentation
- **REQ-DOC-002**: Document all endpoints with examples
- **REQ-DOC-003**: Document all error codes
- **REQ-DOC-004**: Document authentication method
- **REQ-DOC-005**: Document rate limiting

### 13.2 Integration Guide
- **REQ-DOC-006**: Create integration guide for businesses
- **REQ-DOC-007**: Provide code examples (Python, JavaScript, Java)
- **REQ-DOC-008**: Document webhook implementation
- **REQ-DOC-009**: Document error handling best practices

### 13.3 Operations Guide
- **REQ-DOC-010**: Create deployment guide
- **REQ-DOC-011**: Create troubleshooting guide
- **REQ-DOC-012**: Create runbook for common issues

---

## 14. Compliance Requirements

### 14.1 GRA Compliance
- **REQ-COMP-001**: Implement all GRA E-VAT API specifications
- **REQ-COMP-002**: Support all GRA error codes
- **REQ-COMP-003**: Implement all GRA validation rules
- **REQ-COMP-004**: Maintain audit trail for GRA audits

### 14.2 Data Protection
- **REQ-COMP-005**: Comply with Ghana Data Protection Act
- **REQ-COMP-006**: Implement data retention policies
- **REQ-COMP-007**: Support data deletion requests
- **REQ-COMP-008**: Implement data export functionality

---

## 15. Non-Functional Requirements

### 15.1 Scalability
- **REQ-NF-001**: Design for horizontal scaling
- **REQ-NF-002**: Use stateless API design
- **REQ-NF-003**: Implement caching where appropriate
- **REQ-NF-004**: Use database connection pooling

### 15.2 Maintainability
- **REQ-NF-005**: Use clean code principles
- **REQ-NF-006**: Implement comprehensive logging
- **REQ-NF-007**: Use dependency injection
- **REQ-NF-008**: Implement unit and integration tests

### 15.3 Reliability
- **REQ-NF-009**: Implement error handling
- **REQ-NF-010**: Implement retry logic
- **REQ-NF-011**: Implement circuit breaker pattern
- **REQ-NF-012**: Implement graceful shutdown

## 1. Overview

The GRA External Integration API is a secure, multi-tenant gateway that allows registered businesses in Ghana to submit invoices and related transactions to the Ghana Revenue Authority (GRA) E-VAT system. The API acts as a compliance layer, validating all business data against GRA rules before forwarding to the official GRA E-VAT API.

**Core Purpose**: Simplify invoice submission for businesses by abstracting GRA's complex API while ensuring 100% compliance with GRA validation rules and tax calculations.

---

## 2. Functional Requirements

### 2.1 Authentication & Authorization

**REQ-2.1.1**: The API must support API Key + HMAC Signature authentication
- Businesses authenticate using `X-API-Key` header and `X-API-Signature` header
- Signature generated using HMAC-SHA256 of request payload + API Secret
- Each business is a separate tenant with isolated data

**REQ-2.1.2**: Businesses must securely store their GRA credentials
- GRA credentials: `COMPANY_TIN`, `COMPANY_NAMES`, `COMPANY_SECURITY_KEY`
- Credentials encrypted at rest in database
- Credentials never exposed in logs or responses

**REQ-2.1.3**: Multi-tenant isolation must be enforced
- Business A cannot access Business B's submissions
- Business A cannot access Business B's GRA credentials
- All queries filtered by authenticated business_id

### 2.2 Invoice Submission Module

**REQ-2.2.1**: Accept invoice submissions in GRA format (JSON or XML)
- Endpoint: `POST /api/v1/invoices/submit`
- Support both `application/json` and `application/xml` Content-Type
- Request body must match GRA E-VAT API specification exactly

**REQ-2.2.2**: Validate all invoice data before GRA submission
- Validate all required fields present
- Validate data types and formats
- Validate business logic (totals match, item counts match, etc)
- Validate tax/levy calculations per GRA rules
- Return specific validation errors with GRA error codes

**REQ-2.2.3**: Transform and submit to GRA
- Inject business's GRA credentials into request
- Forward to appropriate GRA endpoint (JSON or XML)
- Handle GRA responses and error codes
- Store submission record with full request/response

**REQ-2.2.4**: Return submission status
- Return 202 Accepted with submission_id
- Business can query status using submission_id
- Status values: RECEIVED, PROCESSING, PENDING_GRA, SUCCESS, FAILED

**REQ-2.2.5**: Support invoice status tracking
- Endpoint: `GET /api/v1/invoices/{submission_id}/status`
- Return current status, GRA invoice ID, QR code, timestamps
- Return GRA error codes if submission failed

### 2.3 Refund Module

**REQ-2.3.1**: Accept refund submissions in GRA format
- Endpoint: `POST /api/v1/refunds/submit`
- Support both JSON and XML formats
- Refund must reference original invoice via `REFUND_ID` field

**REQ-2.3.2**: Validate refund data
- Validate `REFUND_ID` references existing invoice
- Validate refund amount doesn't exceed original invoice
- Validate all GRA validation rules for refunds
- Return error A05 if `REFUND_ID` missing

**REQ-2.3.3**: Track refund status
- Endpoint: `GET /api/v1/refunds/{submission_id}/status`
- Return refund status and GRA response details

### 2.4 Purchase Module

**REQ-2.4.1**: Accept purchase invoice submissions
- Endpoint: `POST /api/v1/purchases/submit`
- Support both JSON and XML formats
- FLAG field must be set to "PURCHASE"

**REQ-2.4.2**: Validate and submit purchases
- Apply same validation rules as invoices
- Submit to GRA with PURCHASE flag
- Track purchase status

**REQ-2.4.3**: Track purchase status
- Endpoint: `GET /api/v1/purchases/{submission_id}/status`

### 2.5 Items Management Module

**REQ-2.5.1**: Register item codes with GRA
- Endpoint: `POST /api/v1/items/register`
- Support both JSON and XML formats
- Accept item_list with ITEM_NAME, ITEM_CATEGORY, ITEM_REF, TAX_CODE

**REQ-2.5.2**: Validate item data
- Validate ITEM_REF is unique per business
- Validate TAX_CODE is valid (A, B, C, D, E)
- Validate ITEM_NAME and ITEM_CATEGORY provided

**REQ-2.5.3**: Store registered items
- Store item registration in database
- Track GRA registration status
- Allow retrieval of registered items

### 2.6 Inventory Management Module

**REQ-2.6.1**: Update inventory levels with GRA
- Endpoint: `POST /api/v1/inventory/update`
- Support both JSON and XML formats
- Accept item_list with NIKI_CODE, ITEM_CODE, QTY

**REQ-2.6.2**: Validate inventory data
- Validate ITEM_CODE references registered item
- Validate QTY is positive number
- Validate NIKI_CODE format

**REQ-2.6.3**: Track inventory updates
- Store inventory update records
- Track GRA response status

### 2.7 TIN Validator Module

**REQ-2.7.1**: Validate customer TIN before invoice submission
- Endpoint: `POST /api/v1/tin/validate`
- Support both JSON and XML formats
- Accept TIN and CLIENT_TIN_PIN

**REQ-2.7.2**: Validate TIN format and status
- Validate TIN is 11 or 15 characters
- Submit to GRA for validation
- Return validation status: VALID, INVALID, STOPPED, PROTECTED

**REQ-2.7.3**: Cache TIN validation results
- Store validation results in database
- Cache for 24 hours to reduce GRA API calls
- Allow manual refresh

### 2.8 Tag Description Module

**REQ-2.8.1**: Register tag descriptions
- Endpoint: `POST /api/v1/tags/register`
- Accept tag_code, description, category
- Store per business

**REQ-2.8.2**: Retrieve tag descriptions
- Endpoint: `GET /api/v1/tags/{tag_code}`
- Return tag details for business

### 2.9 Z-Report Module

**REQ-2.9.1**: Request Z-Report from GRA
- Endpoint: `POST /api/v1/reports/z-report`
- Support both JSON and XML formats
- Accept ZD_DATE parameter

**REQ-2.9.2**: Retrieve Z-Report data
- Endpoint: `GET /api/v1/reports/z-report/{date}`
- Return aggregated sales data: inv_close, inv_count, inv_open, inv_vat, inv_total, inv_levy

### 2.10 Signature/Stamping Module

**REQ-2.10.1**: Retrieve invoice signature details
- Endpoint: `POST /api/v1/invoices/{submission_id}/signature`
- Return GRA stamping details: ysdcid, ysdcrecnum, ysdcintdata, ysdcnrc, QR code

### 2.11 VSDC Health Check Module

**REQ-2.11.1**: Check GRA VSDC operational status
- Endpoint: `POST /api/v1/vsdc/health-check`
- Support both JSON and XML formats
- Return VSDC status: UP, DOWN, DEGRADED

**REQ-2.11.2**: Get VSDC status history
- Endpoint: `GET /api/v1/vsdc/status`
- Return last check status and uptime percentage

### 2.12 System Health Module

**REQ-2.12.1**: API health check endpoint
- Endpoint: `GET /api/v1/health`
- Return API status and component health (database, GRA API, cache)

---

## 3. Data Validation Requirements

### 3.1 GRA Error Code Validation

**REQ-3.1.1**: Validate all GRA error codes before submission
- Authentication errors: A01, B01
- Invoice/Refund errors: B16, B18, B19, B20, B22, B70, A05
- Item errors: B05, B051, B06, B061, B07, B09, B10, B11, B12, B13, B15, B21, B27, B28, B29, B31-B35, A06, A07, A08, A09, A11
- TIN errors: T01, T03, T04, T05, T06
- System errors: D01, D05, D06, IS100, A13

**REQ-3.1.2**: Return specific validation errors
- Include GRA error code in response
- Include field name that failed validation
- Include expected vs actual values
- Include remediation guidance

### 3.2 Tax & Levy Calculation Validation

**REQ-3.2.1**: Validate tax calculations per GRA rules
- VAT rates: 0% (TAX_A, TAX_C, TAX_D), 15% (TAX_B), 3% (TAX_E)
- Levy rates: LEVY_A 2.5%, LEVY_B 2.5%, LEVY_C 1%, LEVY_D 1-5%
- Calculation order: Base → Levies → VAT → Total

**REQ-3.2.2**: Validate total amounts
- TOTAL_AMOUNT = sum of all item totals
- TOTAL_VAT = sum of all item VATs
- TOTAL_LEVY = sum of all item levies
- Allow for rounding errors (±0.01)

**REQ-3.2.3**: Validate item-level calculations
- Each item total = UNITYPRICE + levies + VAT
- Levy amounts match calculated values
- VAT amount matches calculated value

### 3.3 Format Validation

**REQ-3.3.1**: Validate required fields
- All mandatory GRA fields must be present
- No null or empty required fields
- Field lengths must match GRA specifications

**REQ-3.3.2**: Validate data types
- Numeric fields must be valid numbers
- Date fields must be YYYY-MM-DD format
- String fields must not contain invalid characters

**REQ-3.3.3**: Validate field formats
- COMPANY_TIN: 11 or 15 characters
- CLIENT_TIN: 11 or 15 characters
- INVOICE_DATE: YYYY-MM-DD format
- CURRENCY: Must be "GHS"
- EXCHANGE_RATE: Must be "1" for GHS

---

## 4. Non-Functional Requirements

### 4.1 Security

**REQ-4.1.1**: HTTPS only communication
- All API endpoints must use HTTPS (TLS 1.2+)
- Enforce HTTPS redirect for HTTP requests

**REQ-4.1.2**: Credential encryption
- GRA credentials encrypted at rest using AES-256
- API secrets hashed using bcrypt
- Encryption keys stored in secure vault

**REQ-4.1.3**: Audit logging
- Log all API requests and responses
- Mask sensitive data in logs (GRA credentials, API secrets)
- Store audit logs for minimum 2 years
- Include timestamp, business_id, action, status, IP address

**REQ-4.1.4**: Rate limiting
- Implement rate limiting per business
- Limit: 100 requests per minute per business
- Return 429 Too Many Requests when exceeded

**REQ-4.1.5**: Input validation & sanitization
- Validate all input data
- Sanitize data to prevent injection attacks
- Reject requests with invalid data

### 4.2 Performance

**REQ-4.2.1**: Response time targets
- Health check: < 100ms
- Validation: < 500ms
- Status check: < 200ms
- GRA submission: < 5 seconds (async)

**REQ-4.2.2**: Throughput
- Support minimum 1000 submissions per hour per business
- Support minimum 100 concurrent businesses

**REQ-4.2.3**: Database performance
- Query response time: < 100ms
- Support minimum 1 million submission records

### 4.3 Reliability

**REQ-4.3.1**: Error handling
- Graceful error handling for all failure scenarios
- Retry logic for transient errors (exponential backoff)
- Maximum 3 retries for GRA API calls
- Distinguish between transient and permanent errors

**REQ-4.3.2**: Data persistence
- All submissions stored in database
- No data loss on API restart
- Database backups minimum daily

**REQ-4.3.3**: Availability
- Target 99.5% uptime
- Graceful degradation if GRA API unavailable
- Health check endpoint for monitoring

### 4.4 Scalability

**REQ-4.4.1**: Horizontal scalability
- Stateless API design for easy scaling
- Support load balancing across multiple instances
- Database connection pooling

**REQ-4.4.2**: Async processing
- Queue submissions for async processing
- Background workers process submissions
- Webhook notifications for status updates

### 4.5 Compliance

**REQ-4.5.1**: GRA compliance
- 100% compliance with GRA E-VAT API specification v7.0
- All validation rules enforced
- All error codes handled correctly

**REQ-4.5.2**: Data retention
- Store submission records for minimum 7 years
- Store audit logs for minimum 2 years
- Implement data archival strategy

**REQ-4.5.3**: Regulatory compliance
- GDPR compliance for EU data
- Ghana data protection compliance
- PCI DSS compliance for payment data (if applicable)

---

## 5. API Response Format Requirements

### 5.1 Success Responses

**REQ-5.1.1**: Successful submission response (202 Accepted)
- Include submission_id (UUID)
- Include status (RECEIVED)
- Include message
- Include validation_passed (boolean)
- Include next_action guidance

**REQ-5.1.2**: Successful status check response (200 OK)
- Include submission_id
- Include current status
- Include GRA response details (if available)
- Include timestamps (submitted_at, completed_at)
- Include GRA invoice ID and QR code (if SUCCESS)

### 5.2 Error Responses

**REQ-5.2.1**: Validation error response (400 Bad Request)
- Include error_code
- Include message
- Include validation_errors array
- Include field names and specific errors
- Include expected vs actual values

**REQ-5.2.2**: Authentication error response (401 Unauthorized)
- Include error_code (AUTH_FAILED)
- Include message
- Do not expose sensitive details

**REQ-5.2.3**: GRA error response (varies by error)
- Include gra_response_code
- Include gra_response_message
- Include submission_id for tracking
- Include remediation guidance

---

## 6. Database Requirements

### 6.1 Data Storage

**REQ-6.1.1**: Store business credentials
- business_id, api_key, api_secret
- gra_tin, gra_company_name, gra_security_key (encrypted)
- status, created_at, updated_at

**REQ-6.1.2**: Store submissions
- submission_id, business_id, submission_type
- submission_status, gra_response_code, gra_response_message
- raw_request, raw_response (JSON)
- submitted_at, completed_at

**REQ-6.1.3**: Store submission items
- submission_id, item details (itmref, itmdes, quantity, etc)
- Tax and levy amounts
- Item totals

**REQ-6.1.4**: Store audit logs
- business_id, action, endpoint, method
- request_payload (masked), response_code
- timestamp, ip_address, user_agent

**REQ-6.1.5**: Store TIN validations
- business_id, tin, tin_pin
- validation_status, taxpayer_name
- validated_at, expires_at

**REQ-6.1.6**: Store registered items
- business_id, item_ref, item_name, item_category
- tax_code, gra_registered status
- created_at, updated_at

**REQ-6.1.7**: Store inventory records
- business_id, item_id, niki_code, item_code
- quantity, last_updated

**REQ-6.1.8**: Store Z-Reports
- business_id, report_date
- inv_close, inv_count, inv_open, inv_vat, inv_total, inv_levy
- generated_at

**REQ-6.1.9**: Store VSDC health checks
- business_id, check_timestamp
- vsdc_status, sdc_id, response_time_ms
- raw_response

**REQ-6.1.10**: Store webhooks
- business_id, webhook_url, events (JSON)
- is_active, created_at, updated_at

**REQ-6.1.11**: Store webhook deliveries
- webhook_id, event_type, payload
- delivery_status, retry_count, last_retry_at
- response_code, response_body

---

## 7. Integration Requirements

### 7.1 GRA API Integration

**REQ-7.1.1**: Connect to GRA E-VAT API
- Use GRA test environment: `https://apitest.e-vatgh.com/evat_apiqa/`
- Support both JSON and XML endpoints
- Handle GRA response formats

**REQ-7.1.2**: Implement retry logic
- Retry transient errors (5xx, timeouts)
- Exponential backoff: 1s, 2s, 4s
- Maximum 3 retries
- Log all retry attempts

**REQ-7.1.3**: Handle GRA errors
- Parse GRA error codes
- Map to business-friendly messages
- Store error details for debugging

### 7.2 Webhook Integration

**REQ-7.2.1**: Send webhook notifications
- Endpoint: `POST /api/v1/webhooks`
- Allow business to register webhook URL
- Support event filtering (invoice.success, refund.failed, etc)

**REQ-7.2.2**: Deliver webhooks reliably
- Retry failed webhook deliveries
- Exponential backoff for retries
- Maximum 5 retries over 24 hours
- Include signature for webhook verification

**REQ-7.2.3**: Webhook payload format
- Include event_type, timestamp, data
- Include submission_id for tracking
- Include status and GRA response details

---

## 8. Acceptance Criteria

### 8.1 Invoice Submission
- ✅ Accept invoice in JSON format
- ✅ Accept invoice in XML format
- ✅ Validate all required fields
- ✅ Validate tax/levy calculations
- ✅ Submit to GRA with business credentials
- ✅ Return submission_id and status
- ✅ Allow status tracking
- ✅ Handle GRA errors gracefully

### 8.2 Refund Submission
- ✅ Accept refund in JSON format
- ✅ Accept refund in XML format
- ✅ Validate REFUND_ID references original invoice
- ✅ Validate refund amount
- ✅ Submit to GRA
- ✅ Return submission_id and status
- ✅ Allow status tracking

### 8.3 Data Validation
- ✅ Validate all GRA error codes
- ✅ Return specific validation errors
- ✅ Prevent invalid data from reaching GRA
- ✅ Support business error remediation

### 8.4 Security
- ✅ Authenticate all requests
- ✅ Enforce multi-tenant isolation
- ✅ Encrypt sensitive data
- ✅ Log all actions
- ✅ Rate limit requests

### 8.5 Reliability
- ✅ Handle GRA API failures
- ✅ Retry transient errors
- ✅ Persist all submissions
- ✅ Provide status tracking
- ✅ Send webhook notifications

---

## 9. Out of Scope

- Payment processing
- Invoice printing
- Business registration/onboarding (manual process)
- GRA credential generation (business responsibility)
- Email notifications (webhook-based only)
- SMS notifications
- Mobile app

---

## 10. Assumptions

- Businesses have valid GRA credentials
- Businesses understand GRA E-VAT format
- GRA API is available and stable
- PostgreSQL database available
- HTTPS/TLS infrastructure available
- Businesses have webhook endpoints for notifications


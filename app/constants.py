"""
GRA External Integration API - Constants

This module contains all constants used throughout the application including:
- GRA error codes and their descriptions
- API endpoints
- Submission types and statuses
- Tax codes and rates
- Computation types
- HTTP status codes
"""

# ============================================================================
# GRA ERROR CODES
# ============================================================================

class GRAErrorCode:
    """GRA error codes and their descriptions"""

    # Authentication Errors
    A01 = "A01"
    A01_DESC = "Company credentials do not exist"

    B01 = "B01"
    B01_DESC = "Incorrect client TIN PIN"

    # Invoice/Refund Errors
    A05 = "A05"
    A05_DESC = "Missing original invoice number (for refunds)"

    B16 = "B16"
    B16_DESC = "INVOICE TOTAL AMOUNT DIFFERENT TO GROSS_AMOUNT"

    B18 = "B18"
    B18_DESC = "TOTAL VAT MISMATCH"

    B19 = "B19"
    B19_DESC = "Invoice reference missing"

    B20 = "B20"
    B20_DESC = "INVOICE REFERENCE ALREADY SENT"

    B22 = "B22"
    B22_DESC = "Zero total invoice not supported"

    B70 = "B70"
    B70_DESC = "Wrong currency or exchange rate"

    # Item Errors
    B05 = "B05"
    B05_DESC = "Client name missing"

    B051 = "B051"
    B051_DESC = "Tax number format not accepted"

    B06 = "B06"
    B06_DESC = "Client name different from previous"

    B061 = "B061"
    B061_DESC = "Item code different from previous"

    B07 = "B07"
    B07_DESC = "Code missing"

    B09 = "B09"
    B09_DESC = "Description missing"

    B10 = "B10"
    B10_DESC = "Quantity missing"

    B11 = "B11"
    B11_DESC = "Quantity is negative"

    B12 = "B12"
    B12_DESC = "Quantity not a number"

    B13 = "B13"
    B13_DESC = "Tax rate not accepted"

    B15 = "B15"
    B15_DESC = "Item count mismatch"

    B21 = "B21"
    B21_DESC = "Negative sale price"

    B27 = "B27"
    B27_DESC = "Tax rate different from previous"

    B28 = "B28"
    B28_DESC = "Client tax number different"

    B29 = "B29"
    B29_DESC = "Client tax number for another client"

    B31 = "B31"
    B31_DESC = "Levy amount A discrepancy"

    B32 = "B32"
    B32_DESC = "Levy amount B discrepancy"

    B33 = "B33"
    B33_DESC = "Levy amount C discrepancy"

    B34 = "B34"
    B34_DESC = "Levy amount D discrepancy / Total levy mismatch"

    B35 = "B35"
    B35_DESC = "Levy amount discrepancy"

    # Unit Price and Discount Errors
    A06 = "A06"
    A06_DESC = "Invalid unit price"

    A07 = "A07"
    A07_DESC = "Invalid discount"

    # Tax Code and Rate Errors
    A08 = "A08"
    A08_DESC = "Invalid tax code"

    A09 = "A09"
    A09_DESC = "Invalid tax rate"

    A11 = "A11"
    A11_DESC = "Item count not a number"

    # TIN Validator Errors
    T01 = "T01"
    T01_DESC = "Invalid TIN number"

    T03 = "T03"
    T03_DESC = "TIN number not found"

    T04 = "T04"
    T04_DESC = "TIN stopped"

    T05 = "T05"
    T05_DESC = "TIN protected"

    T06 = "T06"
    T06_DESC = "Incorrect client TIN PIN"

    # System Errors
    D01 = "D01"
    D01_DESC = "Invoice already exists"

    D05 = "D05"
    D05_DESC = "Invoice under stamping"

    D06 = "D06"
    D06_DESC = "Stamping engine is down"

    IS100 = "IS100"
    IS100_DESC = "Internal error"

    A13 = "A13"
    A13_DESC = "E-VAT unable to reach database"

    # Error code to description mapping
    ERROR_CODES = {
        A01: A01_DESC,
        B01: B01_DESC,
        A05: A05_DESC,
        B16: B16_DESC,
        B18: B18_DESC,
        B19: B19_DESC,
        B20: B20_DESC,
        B22: B22_DESC,
        B70: B70_DESC,
        B05: B05_DESC,
        B051: B051_DESC,
        B06: B06_DESC,
        B061: B061_DESC,
        B07: B07_DESC,
        B09: B09_DESC,
        B10: B10_DESC,
        B11: B11_DESC,
        B12: B12_DESC,
        B13: B13_DESC,
        B15: B15_DESC,
        B21: B21_DESC,
        B27: B27_DESC,
        B28: B28_DESC,
        B29: B29_DESC,
        B31: B31_DESC,
        B32: B32_DESC,
        B33: B33_DESC,
        B34: B34_DESC,
        B35: B35_DESC,
        A06: A06_DESC,
        A07: A07_DESC,
        A08: A08_DESC,
        A09: A09_DESC,
        A11: A11_DESC,
        T01: T01_DESC,
        T03: T03_DESC,
        T04: T04_DESC,
        T05: T05_DESC,
        T06: T06_DESC,
        D01: D01_DESC,
        D05: D05_DESC,
        D06: D06_DESC,
        IS100: IS100_DESC,
        A13: A13_DESC,
    }

    @classmethod
    def get_description(cls, error_code: str) -> str:
        """Get description for an error code"""
        return cls.ERROR_CODES.get(error_code, "Unknown error")


# ============================================================================
# API ENDPOINTS
# ============================================================================

class APIEndpoints:
    """API endpoint paths"""

    # Base path
    API_V1_BASE = "/api/v1"

    # Invoice endpoints
    INVOICES_SUBMIT = f"{API_V1_BASE}/invoices/submit"
    INVOICES_STATUS = f"{API_V1_BASE}/invoices/{{submission_id}}/status"
    INVOICES_SIGNATURE = f"{API_V1_BASE}/invoices/{{submission_id}}/signature"

    # Refund endpoints
    REFUNDS_SUBMIT = f"{API_V1_BASE}/refunds/submit"
    REFUNDS_STATUS = f"{API_V1_BASE}/refunds/{{submission_id}}/status"

    # Purchase endpoints
    PURCHASES_SUBMIT = f"{API_V1_BASE}/purchases/submit"
    PURCHASES_STATUS = f"{API_V1_BASE}/purchases/{{submission_id}}/status"

    # Items endpoints
    ITEMS_REGISTER = f"{API_V1_BASE}/items/register"
    ITEMS_GET = f"{API_V1_BASE}/items/{{item_ref}}"

    # Inventory endpoints
    INVENTORY_UPDATE = f"{API_V1_BASE}/inventory/update"

    # TIN Validator endpoints
    TIN_VALIDATE = f"{API_V1_BASE}/tin/validate"

    # Tag Description endpoints
    TAGS_REGISTER = f"{API_V1_BASE}/tags/register"
    TAGS_GET = f"{API_V1_BASE}/tags/{{tag_code}}"

    # Z-Report endpoints
    ZREPORT_REQUEST = f"{API_V1_BASE}/reports/z-report"
    ZREPORT_GET = f"{API_V1_BASE}/reports/z-report/{{date}}"

    # VSDC Health Check endpoints
    VSDC_HEALTH_CHECK = f"{API_V1_BASE}/vsdc/health-check"
    VSDC_STATUS = f"{API_V1_BASE}/vsdc/status"

    # System endpoints
    HEALTH = f"{API_V1_BASE}/health"
    WEBHOOKS_REGISTER = f"{API_V1_BASE}/webhooks"
    WEBHOOKS_UPDATE = f"{API_V1_BASE}/webhooks/{{webhook_id}}"
    WEBHOOKS_DELETE = f"{API_V1_BASE}/webhooks/{{webhook_id}}"
    WEBHOOKS_LIST = f"{API_V1_BASE}/webhooks"


# ============================================================================
# GRA API ENDPOINTS (External)
# ============================================================================

class GRAEndpoints:
    """GRA E-VAT API endpoints"""

    # Test environment
    TEST_BASE_URL = "https://apitest.e-vatgh.com"
    TEST_INVOICE_JSON = f"{TEST_BASE_URL}/api/invoice/json"
    TEST_INVOICE_XML = f"{TEST_BASE_URL}/api/invoice/xml"
    TEST_REFUND_JSON = f"{TEST_BASE_URL}/api/refund/json"
    TEST_REFUND_XML = f"{TEST_BASE_URL}/api/refund/xml"
    TEST_PURCHASE_JSON = f"{TEST_BASE_URL}/api/purchase/json"
    TEST_PURCHASE_XML = f"{TEST_BASE_URL}/api/purchase/xml"
    TEST_ITEM_JSON = f"{TEST_BASE_URL}/api/item/json"
    TEST_ITEM_XML = f"{TEST_BASE_URL}/api/item/xml"
    TEST_INVENTORY_JSON = f"{TEST_BASE_URL}/api/inventory/json"
    TEST_INVENTORY_XML = f"{TEST_BASE_URL}/api/inventory/xml"
    TEST_TIN_VALIDATE_JSON = f"{TEST_BASE_URL}/api/tin/validate/json"
    TEST_TIN_VALIDATE_XML = f"{TEST_BASE_URL}/api/tin/validate/xml"
    TEST_ZREPORT_JSON = f"{TEST_BASE_URL}/api/zreport/json"
    TEST_ZREPORT_XML = f"{TEST_BASE_URL}/api/zreport/xml"
    TEST_VSDC_HEALTH_JSON = f"{TEST_BASE_URL}/api/vsdc/health/json"
    TEST_VSDC_HEALTH_XML = f"{TEST_BASE_URL}/api/vsdc/health/xml"

    # Production environment
    PROD_BASE_URL = "https://api.e-vatgh.com"
    PROD_INVOICE_JSON = f"{PROD_BASE_URL}/api/invoice/json"
    PROD_INVOICE_XML = f"{PROD_BASE_URL}/api/invoice/xml"
    PROD_REFUND_JSON = f"{PROD_BASE_URL}/api/refund/json"
    PROD_REFUND_XML = f"{PROD_BASE_URL}/api/refund/xml"
    PROD_PURCHASE_JSON = f"{PROD_BASE_URL}/api/purchase/json"
    PROD_PURCHASE_XML = f"{PROD_BASE_URL}/api/purchase/xml"
    PROD_ITEM_JSON = f"{PROD_BASE_URL}/api/item/json"
    PROD_ITEM_XML = f"{PROD_BASE_URL}/api/item/xml"
    PROD_INVENTORY_JSON = f"{PROD_BASE_URL}/api/inventory/json"
    PROD_INVENTORY_XML = f"{PROD_BASE_URL}/api/inventory/xml"
    PROD_TIN_VALIDATE_JSON = f"{PROD_BASE_URL}/api/tin/validate/json"
    PROD_TIN_VALIDATE_XML = f"{PROD_BASE_URL}/api/tin/validate/xml"
    PROD_ZREPORT_JSON = f"{PROD_BASE_URL}/api/zreport/json"
    PROD_ZREPORT_XML = f"{PROD_BASE_URL}/api/zreport/xml"
    PROD_VSDC_HEALTH_JSON = f"{PROD_BASE_URL}/api/vsdc/health/json"
    PROD_VSDC_HEALTH_XML = f"{PROD_BASE_URL}/api/vsdc/health/xml"


# ============================================================================
# SUBMISSION TYPES
# ============================================================================

class SubmissionType:
    """Submission type constants"""

    INVOICE = "INVOICE"
    REFUND = "REFUND"
    PURCHASE = "PURCHASE"
    ITEM = "ITEM"
    INVENTORY = "INVENTORY"
    TIN_VALIDATION = "TIN_VALIDATION"
    ZREPORT = "ZREPORT"
    VSDC_HEALTH_CHECK = "VSDC_HEALTH_CHECK"

    ALL_TYPES = [INVOICE, REFUND, PURCHASE, ITEM, INVENTORY, TIN_VALIDATION, ZREPORT, VSDC_HEALTH_CHECK]


# ============================================================================
# SUBMISSION STATUS
# ============================================================================

class SubmissionStatus:
    """Submission status constants"""

    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    PENDING_GRA = "PENDING_GRA"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"

    ALL_STATUSES = [RECEIVED, PROCESSING, PENDING_GRA, SUCCESS, FAILED]


# ============================================================================
# FLAG TYPES
# ============================================================================

class FlagType:
    """FLAG field values for submissions"""

    INVOICE = "INVOICE"
    REFUND = "REFUND"
    PROFORMA = "PROFORMA"
    PARTIAL_REFUND = "PARTIAL_REFUND"
    PURCHASE = "PURCHASE"

    ALL_FLAGS = [INVOICE, REFUND, PROFORMA, PARTIAL_REFUND, PURCHASE]


# ============================================================================
# TAX CODES
# ============================================================================

class TaxCode:
    """Tax code constants"""

    A = "A"  # Exempted
    B = "B"  # Taxable
    C = "C"  # Export
    D = "D"  # Non-Taxable
    E = "E"  # Non-VAT

    ALL_CODES = [A, B, C, D, E]

    # Tax code descriptions
    DESCRIPTIONS = {
        A: "Exempted",
        B: "Taxable",
        C: "Export",
        D: "Non-Taxable",
        E: "Non-VAT",
    }


# ============================================================================
# TAX RATES
# ============================================================================

class TaxRate:
    """Tax rate constants (in percentage)"""

    ZERO = 0
    THREE = 3
    FIFTEEN = 15

    ALL_RATES = [ZERO, THREE, FIFTEEN]

    # Tax rate to VAT percentage mapping
    VAT_RATES = {
        "A": ZERO,      # Exempted: 0%
        "B": FIFTEEN,   # Taxable: 15%
        "C": ZERO,      # Export: 0%
        "D": ZERO,      # Non-Taxable: 0%
        "E": THREE,     # Non-VAT: 3%
    }


# ============================================================================
# LEVY RATES
# ============================================================================

class LevyRate:
    """Levy rate constants (in percentage)"""

    LEVY_A_RATE = 2.5   # NHIL
    LEVY_B_RATE = 2.5   # GETFund
    LEVY_C_RATE = 1.0   # COVID
    LEVY_D_RATE = 1.0   # Tourism/CST (can be 5%)

    # Levy descriptions
    LEVY_A_DESC = "NHIL (National Health Insurance Levy)"
    LEVY_B_DESC = "GETFund (Ghana Education Trust Fund)"
    LEVY_C_DESC = "COVID-19 Levy"
    LEVY_D_DESC = "Tourism/CST Levy"


# ============================================================================
# COMPUTATION TYPES
# ============================================================================

class ComputationType:
    """Computation type constants"""

    INCLUSIVE = "INCLUSIVE"   # VAT/levies included in unit price
    EXCLUSIVE = "EXCLUSIVE"   # VAT/levies added to unit price

    ALL_TYPES = [INCLUSIVE, EXCLUSIVE]


# ============================================================================
# SALE TYPES
# ============================================================================

class SaleType:
    """Sale type constants"""

    NORMAL = "NORMAL"
    CREDIT_SALE = "CREDIT_SALE"

    ALL_TYPES = [NORMAL, CREDIT_SALE]


# ============================================================================
# CURRENCY
# ============================================================================

class Currency:
    """Currency constants"""

    GHS = "GHS"  # Ghana Cedis (only supported currency)
    EXCHANGE_RATE_GHS = 1  # Exchange rate for GHS must be 1


# ============================================================================
# TIN VALIDATION STATUS
# ============================================================================

class TINValidationStatus:
    """TIN validation status constants"""

    VALID = "VALID"
    INVALID = "INVALID"
    STOPPED = "STOPPED"
    PROTECTED = "PROTECTED"

    ALL_STATUSES = [VALID, INVALID, STOPPED, PROTECTED]


# ============================================================================
# VSDC HEALTH STATUS
# ============================================================================

class VSDCHealthStatus:
    """VSDC health check status constants"""

    UP = "UP"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"

    ALL_STATUSES = [UP, DOWN, DEGRADED]


# ============================================================================
# HTTP STATUS CODES
# ============================================================================

class HTTPStatus:
    """HTTP status codes"""

    OK = 200
    ACCEPTED = 202
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# ============================================================================
# VALIDATION CONSTANTS
# ============================================================================

class ValidationConstants:
    """Validation-related constants"""

    # TIN format
    TIN_MIN_LENGTH = 11
    TIN_MAX_LENGTH = 15

    # Invoice number
    INVOICE_NUM_MAX_LENGTH = 50

    # Quantity and price
    MIN_QUANTITY = 0
    MIN_PRICE = 0

    # Monetary precision
    DECIMAL_PLACES = 2

    # Rounding tolerance (for comparing calculated vs provided amounts)
    ROUNDING_TOLERANCE = 0.01

    # Date format
    DATE_FORMAT = "%Y-%m-%d"

    # Item count
    MIN_ITEM_COUNT = 1
    MAX_ITEM_COUNT = 10000


# ============================================================================
# RETRY CONSTANTS
# ============================================================================

class RetryConstants:
    """Retry logic constants"""

    # Exponential backoff delays (in seconds)
    BACKOFF_DELAYS = [1, 2, 4, 8, 16, 32]

    # Maximum retry attempts
    MAX_RETRIES = 5

    # Transient error codes that should be retried
    TRANSIENT_ERROR_CODES = [D06, IS100, A13]

    # Request timeout (in seconds)
    REQUEST_TIMEOUT = 30

    # GRA API timeout (in seconds)
    GRA_API_TIMEOUT = 30


# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimitConstants:
    """Rate limiting constants"""

    # Per business: requests per hour
    REQUESTS_PER_HOUR = 1000

    # Per endpoint: requests per minute
    REQUESTS_PER_MINUTE = 100

    # Cache TTL for rate limit counters (in seconds)
    RATE_LIMIT_CACHE_TTL = 3600


# ============================================================================
# CACHING
# ============================================================================

class CacheConstants:
    """Caching constants"""

    # TIN validation cache TTL (in seconds)
    TIN_VALIDATION_CACHE_TTL = 86400  # 24 hours

    # VSDC health check cache TTL (in seconds)
    VSDC_HEALTH_CACHE_TTL = 300  # 5 minutes

    # Webhook delivery cache TTL (in seconds)
    WEBHOOK_DELIVERY_CACHE_TTL = 7776000  # 90 days


# ============================================================================
# AUTHENTICATION
# ============================================================================

class AuthConstants:
    """Authentication constants"""

    # API Key header
    API_KEY_HEADER = "X-API-Key"

    # API Signature header
    API_SIGNATURE_HEADER = "X-API-Signature"

    # Webhook signature header
    WEBHOOK_SIGNATURE_HEADER = "X-Webhook-Signature"

    # Signature algorithm
    SIGNATURE_ALGORITHM = "sha256"

    # API Key length
    API_KEY_LENGTH = 32

    # API Secret length
    API_SECRET_LENGTH = 64


# ============================================================================
# ENCRYPTION
# ============================================================================

class EncryptionConstants:
    """Encryption constants"""

    # Encryption algorithm
    ENCRYPTION_ALGORITHM = "AES-256"

    # Encryption key length (in bytes)
    ENCRYPTION_KEY_LENGTH = 32


# ============================================================================
# AUDIT LOGGING
# ============================================================================

class AuditConstants:
    """Audit logging constants"""

    # Audit log retention period (in years)
    AUDIT_LOG_RETENTION_YEARS = 7

    # Submission record retention period (in years)
    SUBMISSION_RETENTION_YEARS = 7

    # Webhook delivery log retention period (in days)
    WEBHOOK_LOG_RETENTION_DAYS = 90

    # Sensitive fields to mask in logs
    SENSITIVE_FIELDS = [
        "api_secret",
        "gra_security_key",
        "gra_credentials",
        "password",
        "client_tin",
        "company_tin",
    ]


# ============================================================================
# WEBHOOK CONSTANTS
# ============================================================================

class WebhookConstants:
    """Webhook-related constants"""

    # Webhook event types
    EVENT_INVOICE_SUCCESS = "invoice.success"
    EVENT_INVOICE_FAILED = "invoice.failed"
    EVENT_REFUND_SUCCESS = "refund.success"
    EVENT_REFUND_FAILED = "refund.failed"
    EVENT_PURCHASE_SUCCESS = "purchase.success"
    EVENT_PURCHASE_FAILED = "purchase.failed"

    ALL_EVENTS = [
        EVENT_INVOICE_SUCCESS,
        EVENT_INVOICE_FAILED,
        EVENT_REFUND_SUCCESS,
        EVENT_REFUND_FAILED,
        EVENT_PURCHASE_SUCCESS,
        EVENT_PURCHASE_FAILED,
    ]

    # Webhook delivery retry attempts
    MAX_DELIVERY_ATTEMPTS = 5

    # Webhook delivery timeout (in seconds)
    DELIVERY_TIMEOUT = 5


# ============================================================================
# CONTENT TYPES
# ============================================================================

class ContentType:
    """Content type constants"""

    JSON = "application/json"
    XML = "application/xml"
    FORM_URLENCODED = "application/x-www-form-urlencoded"


# ============================================================================
# API VERSION
# ============================================================================

API_VERSION = "1.0.0"
API_TITLE = "GRA External Integration API"
API_DESCRIPTION = "Secure gateway for submitting invoices and tax documents to GRA E-VAT system"

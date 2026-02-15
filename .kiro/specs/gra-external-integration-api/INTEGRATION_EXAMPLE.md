# Authentication Middleware Integration Example

This document shows how to integrate the authentication middleware into your FastAPI routes.

## Example 1: Basic Route Protection

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
    """
    Submit an invoice to GRA.
    
    Authentication:
        X-API-Key: business_api_key
        X-API-Signature: hmac_sha256_signature
        X-API-Timestamp: iso_format_timestamp
    
    Args:
        request: FastAPI request object
        business: Authenticated business data
        db: Database session
        
    Returns:
        Submission response
    """
    # Get business ID from authenticated business data
    business_id = business["id"]
    business_name = business["name"]
    
    # Read request body
    body = await request.body()
    invoice_data = json.loads(body)
    
    # Process invoice...
    # Store in database...
    # Forward to GRA...
    
    return {
        "submission_id": "uuid-12345",
        "status": "RECEIVED",
        "message": "Invoice received and queued for GRA processing",
        "invoice_num": invoice_data.get("header", {}).get("NUM")
    }
```

## Example 2: Multiple Protected Routes

```python
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
import json

from app.middleware.auth_dependency import verify_auth, get_db
from app.services.business_service import BusinessService

router = APIRouter()

@router.post("/api/v1/invoices/submit")
async def submit_invoice(
    request: Request,
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Submit invoice"""
    business_id = business["id"]
    # ... implementation ...
    return {"status": "success"}

@router.get("/api/v1/invoices/{submission_id}/status")
async def get_invoice_status(
    submission_id: str,
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Get invoice submission status"""
    business_id = business["id"]
    # ... implementation ...
    return {"status": "SUCCESS"}

@router.post("/api/v1/refunds/submit")
async def submit_refund(
    request: Request,
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Submit refund"""
    business_id = business["id"]
    # ... implementation ...
    return {"status": "success"}

@router.post("/api/v1/tin/validate")
async def validate_tin(
    request: Request,
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Validate TIN"""
    business_id = business["id"]
    # ... implementation ...
    return {"status": "VALID"}
```

## Example 3: With Additional Validation

```python
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
import json

from app.middleware.auth_dependency import verify_auth, get_db
from app.services.business_service import BusinessService
from app.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.post("/api/v1/invoices/submit")
async def submit_invoice(
    request: Request,
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Submit invoice with additional validation"""
    
    # Get business ID
    business_id = business["id"]
    logger.info(f"Invoice submission from business: {business_id}")
    
    # Read and parse request body
    body = await request.body()
    try:
        invoice_data = json.loads(body)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON from business: {business_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON in request body"
        )
    
    # Validate invoice structure
    if "header" not in invoice_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'header' in request"
        )
    
    if "item_list" not in invoice_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'item_list' in request"
        )
    
    # Get business GRA credentials
    business_obj = BusinessService.get_business_by_id(db, business_id)
    if not business_obj:
        logger.error(f"Business not found: {business_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Business not found"
        )
    
    # Process invoice...
    logger.info(f"Processing invoice for business: {business_id}")
    
    return {
        "submission_id": "uuid-12345",
        "status": "RECEIVED",
        "message": "Invoice received and queued for GRA processing"
    }
```

## Example 4: With Rate Limiting

```python
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from app.middleware.auth_dependency import verify_auth, get_db
from app.logger import get_logger

logger = get_logger(__name__)

# Simple in-memory rate limiting (use Redis for production)
request_counts = {}

def check_rate_limit(business_id: str, limit: int = 100, window: int = 60) -> bool:
    """Check if business has exceeded rate limit"""
    now = datetime.utcnow()
    key = f"{business_id}:{now.minute}"
    
    if key not in request_counts:
        request_counts[key] = 0
    
    request_counts[key] += 1
    
    # Clean old entries
    for k in list(request_counts.keys()):
        if k.split(":")[0] == business_id:
            old_minute = int(k.split(":")[1])
            if now.minute - old_minute > 1:
                del request_counts[k]
    
    return request_counts[key] <= limit

router = APIRouter()

@router.post("/api/v1/invoices/submit")
async def submit_invoice(
    request: Request,
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Submit invoice with rate limiting"""
    
    business_id = business["id"]
    
    # Check rate limit
    if not check_rate_limit(business_id, limit=100):
        logger.warning(f"Rate limit exceeded for business: {business_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"}
        )
    
    # Process invoice...
    return {"status": "success"}
```

## Example 5: With Audit Logging

```python
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
import json

from app.middleware.auth_dependency import verify_auth, get_db
from app.models.models import AuditLog
from app.logger import get_logger
from datetime import datetime
import uuid

logger = get_logger(__name__)

router = APIRouter()

def log_audit(
    db: Session,
    business_id: str,
    action: str,
    endpoint: str,
    method: str,
    request_payload: dict,
    response_code: int,
    response_status: str,
    error_message: str = None
):
    """Log audit event"""
    audit_log = AuditLog(
        id=uuid.uuid4(),
        business_id=business_id,
        action=action,
        endpoint=endpoint,
        method=method,
        request_payload=request_payload,
        response_code=response_code,
        response_status=response_status,
        error_message=error_message,
        created_at=datetime.utcnow()
    )
    db.add(audit_log)
    db.commit()

@router.post("/api/v1/invoices/submit")
async def submit_invoice(
    request: Request,
    business: dict = Depends(verify_auth),
    db: Session = Depends(get_db)
):
    """Submit invoice with audit logging"""
    
    business_id = business["id"]
    
    # Read request body
    body = await request.body()
    try:
        invoice_data = json.loads(body)
    except json.JSONDecodeError:
        log_audit(
            db=db,
            business_id=business_id,
            action="SUBMIT_INVOICE",
            endpoint="/api/v1/invoices/submit",
            method="POST",
            request_payload={},
            response_code=400,
            response_status="FAILED",
            error_message="Invalid JSON"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON"
        )
    
    try:
        # Process invoice...
        submission_id = "uuid-12345"
        
        # Log successful submission
        log_audit(
            db=db,
            business_id=business_id,
            action="SUBMIT_INVOICE",
            endpoint="/api/v1/invoices/submit",
            method="POST",
            request_payload=invoice_data,
            response_code=202,
            response_status="SUCCESS"
        )
        
        return {
            "submission_id": submission_id,
            "status": "RECEIVED"
        }
    
    except Exception as e:
        logger.error(f"Error processing invoice: {str(e)}")
        
        # Log failed submission
        log_audit(
            db=db,
            business_id=business_id,
            action="SUBMIT_INVOICE",
            endpoint="/api/v1/invoices/submit",
            method="POST",
            request_payload=invoice_data,
            response_code=500,
            response_status="FAILED",
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

## Example 6: Public Endpoint

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/v1/health")
async def health_check():
    """
    Health check endpoint (no authentication required).
    
    This endpoint is in AuthMiddleware.PUBLIC_ENDPOINTS,
    so it doesn't require authentication.
    """
    return {
        "status": "ok",
        "timestamp": "2026-02-10T10:30:45Z"
    }
```

## Example 7: Client-Side Usage

```python
import requests
import hmac
import hashlib
import json
from datetime import datetime

class GRAAPIClient:
    """Client for GRA External Integration API"""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
    
    def _generate_signature(
        self,
        method: str,
        path: str,
        body: bytes,
        timestamp: str
    ) -> str:
        """Generate HMAC-SHA256 signature"""
        body_hash = hashlib.sha256(body).hexdigest()
        message = f"{method}|{path}|{timestamp}|{body_hash}"
        signature = hmac.new(
            key=self.api_secret.encode(),
            msg=message.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(
        self,
        method: str,
        path: str,
        data: dict = None
    ) -> dict:
        """Make authenticated request"""
        
        # Prepare body
        if data:
            body = json.dumps(data).encode()
        else:
            body = b""
        
        # Generate timestamp
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Generate signature
        signature = self._generate_signature(method, path, body, timestamp)
        
        # Prepare headers
        headers = {
            "X-API-Key": self.api_key,
            "X-API-Signature": signature,
            "X-API-Timestamp": timestamp,
            "Content-Type": "application/json"
        }
        
        # Make request
        url = f"{self.base_url}{path}"
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, data=body, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        return response.json()
    
    def submit_invoice(self, invoice_data: dict) -> dict:
        """Submit invoice"""
        return self._make_request(
            method="POST",
            path="/api/v1/invoices/submit",
            data=invoice_data
        )
    
    def get_invoice_status(self, submission_id: str) -> dict:
        """Get invoice status"""
        return self._make_request(
            method="GET",
            path=f"/api/v1/invoices/{submission_id}/status"
        )

# Usage
client = GRAAPIClient(
    api_key="your_api_key",
    api_secret="your_api_secret",
    base_url="https://api.example.com"
)

# Submit invoice
response = client.submit_invoice({
    "company": {...},
    "header": {...},
    "item_list": [...]
})

print(response)
```

## Integration Checklist

- [ ] Add `verify_auth` dependency to all protected routes
- [ ] Update route handlers to use `business` data
- [ ] Add rate limiting (optional)
- [ ] Add audit logging (optional)
- [ ] Test with authentication
- [ ] Test with invalid credentials
- [ ] Test with expired timestamps
- [ ] Test with invalid signatures
- [ ] Document API endpoints
- [ ] Provide client libraries/examples
- [ ] Monitor authentication failures
- [ ] Set up alerts for suspicious activity

## Testing Integration

```bash
# Run all tests
pytest tests/ -v

# Run only auth tests
pytest tests/test_auth_middleware.py -v

# Run with coverage
pytest tests/test_auth_middleware.py --cov=app.middleware
```

## Deployment Checklist

- [ ] All tests passing
- [ ] No security warnings
- [ ] HTTPS enabled
- [ ] Rate limiting configured
- [ ] Audit logging enabled
- [ ] Monitoring set up
- [ ] Documentation updated
- [ ] Client libraries provided
- [ ] Support team trained
- [ ] Rollback plan ready

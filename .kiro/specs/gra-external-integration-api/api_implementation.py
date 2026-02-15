from fastapi import FastAPI, Header, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import hashlib
import hmac

app = FastAPI(title="GRA External Integration API", version="1.0.0")

# --- Mock Database and Security ---
# In a real implementation, these would be in the PostgreSQL database
MOCK_BUSINESSES = {
    "biz_key_123": {
        "id": "business-uuid-1",
        "name": "ABC Company Ltd",
        "secret": "biz_secret_456",
        "status": "active"
    }
}

MOCK_SUBMISSIONS = {}

# --- Models ---
class InvoiceItem(BaseModel):
    item_code: str
    description: str
    quantity: float
    unit_price: float
    discount: float = 0.0

class InvoiceSubmission(BaseModel):
    invoice_number: str
    customer_name: str
    customer_tin: Optional[str] = None
    transaction_date: str
    transaction_type: str = "INVOICE"
    sale_type: str = "NORMAL"
    items: List[InvoiceItem]
    base_amount: float
    total_vat: float
    total_levy: float
    total_amount: float
    erp_reference_id: Optional[str] = None

class SubmissionResponse(BaseModel):
    submission_id: str
    status: str
    message: str

class SubmissionStatusResponse(BaseModel):
    submission_id: str
    invoice_number: str
    status: str
    gra_invoice_id: Optional[str] = None
    gra_qr_code: Optional[str] = None
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

# --- Security Dependency ---
def verify_api_key(x_api_key: str = Header(...), x_api_signature: str = Header(...)):
    if x_api_key not in MOCK_BUSINESSES:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
    
    business = MOCK_BUSINESSES[x_api_key]
    if business["status"] != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Business account is inactive")
    
    # In a real implementation, we would verify the signature here
    # For this example, we'll assume the signature is valid if it matches a simple hash of the key and secret
    expected_signature = hashlib.sha256(f"{x_api_key}{business['secret']}".encode()).hexdigest()
    if x_api_signature != expected_signature:
         # For demonstration purposes, we'll accept a "valid_signature" string or the real one
         if x_api_signature != "valid_signature":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Signature")
    
    return business

# --- Endpoints ---

@app.post("/api/v1/external/invoices", response_model=SubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_invoice(invoice: InvoiceSubmission, business: dict = Depends(verify_api_key)):
    submission_id = str(uuid.uuid4())
    
    # --- Data Transformation Logic (Simplified) ---
    # 1. Calculate Levies based on 2026 reforms
    # NHIL (2.5%), GETFund (2.5%)
    levy_a = round(invoice.base_amount * 0.025, 2)
    levy_b = round(invoice.base_amount * 0.025, 2)
    
    # 2. Prepare internal transaction record
    transaction_record = {
        "id": submission_id,
        "business_id": business["id"],
        "invoice_number": invoice.invoice_number,
        "status": "RECEIVED",
        "levy_amount_a": levy_a,
        "levy_amount_b": levy_b,
        "levy_amount_c": 0.00, # COVID levy abolished
        "levy_amount_d": 0.00,
        "levy_amount_e": 0.00,
        "created_at": datetime.now()
    }
    
    # 3. Store in mock database
    MOCK_SUBMISSIONS[submission_id] = {
        "submission_id": submission_id,
        "invoice_number": invoice.invoice_number,
        "status": "SUCCESS", # Mocking immediate success for this example
        "gra_invoice_id": f"GRA-{invoice.invoice_number}",
        "gra_qr_code": f"https://gra.gov.gh/qr/{submission_id}",
        "submitted_at": datetime.now(),
        "completed_at": datetime.now(),
        "error_message": None
    }
    
    return {
        "submission_id": submission_id,
        "status": "RECEIVED",
        "message": "Invoice received and queued for processing."
    }

@app.get("/api/v1/external/invoices/{submission_id}/status", response_model=SubmissionStatusResponse)
async def get_submission_status(submission_id: str, business: dict = Depends(verify_api_key)):
    if submission_id not in MOCK_SUBMISSIONS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    
    return MOCK_SUBMISSIONS[submission_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

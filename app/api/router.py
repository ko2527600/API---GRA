"""Main API router - aggregates all endpoint routes"""
from fastapi import APIRouter
from app.api.endpoints import api_keys, invoices, refunds, purchases, items, z_reports, webhooks, audit_logs

# Create main API router
api_router = APIRouter()

# Include routers from individual modules
api_router.include_router(api_keys.router)
api_router.include_router(invoices.router)
api_router.include_router(refunds.router)
api_router.include_router(purchases.router)
api_router.include_router(items.router)
api_router.include_router(z_reports.router)
api_router.include_router(webhooks.router)
api_router.include_router(audit_logs.router)

# Example placeholder
@api_router.get("/")
async def root():
    """API root endpoint"""
    return {"message": "GRA External Integration API v1.0"}

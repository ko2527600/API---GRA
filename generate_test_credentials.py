#!/usr/bin/env python
"""Generate test API credentials"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.api_key_service import APIKeyService
from app.services.business_service import BusinessService
from app.database import SessionLocal

def main():
    """Generate test credentials"""
    # Generate API key and secret
    api_key, api_secret = APIKeyService.generate_credentials()
    
    print("\n" + "="*60)
    print("TEST API CREDENTIALS GENERATED")
    print("="*60)
    print(f"\nAPI Key:    {api_key}")
    print(f"API Secret: {api_secret}")
    print("\n" + "="*60)
    print("USAGE IN API TESTER:")
    print("="*60)
    print(f"X-API-Key: {api_key}")
    print(f"X-API-Secret: {api_secret}")
    print("\n" + "="*60)
    
    # Also try to create a business record
    try:
        db = SessionLocal()
        business, secret = BusinessService.create_business(
            db=db,
            business_name="TEST TAXPAYER 15 PERCENT VAT",
            gra_tin="C00XXXXXXXX",
            gra_company_name="TEST TAXPAYER 15 PERCENT VAT",
            gra_security_key="UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
        )
        print("\nBusiness created in database:")
        print(f"Business ID: {business.id}")
        print(f"API Key: {business.api_key}")
        print(f"API Secret (one-time): {secret}")
        db.close()
    except Exception as e:
        print(f"\nNote: Could not create business in DB: {e}")
        print("This is OK for testing - use the generated credentials above")

if __name__ == "__main__":
    main()

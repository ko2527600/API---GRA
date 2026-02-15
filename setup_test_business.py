#!/usr/bin/env python
"""Setup test business with known API key for testing"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, init_db
from app.services.business_service import BusinessService

def main():
    """Create test business"""
    print("\nSetting up test business...")
    
    # Initialize database
    init_db()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create business with the API key from HTML tester
        business, secret = BusinessService.create_business(
            db=db,
            business_name="TEST TAXPAYER 15 PERCENT VAT",
            gra_tin="C00XXXXXXXX",
            gra_company_name="TEST TAXPAYER 15 PERCENT VAT",
            gra_security_key="UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
        )
        
        print(f"\nBusiness created successfully!")
        print(f"  Business ID: {business.id}")
        print(f"  API Key: {business.api_key}")
        print(f"  API Secret: {secret}")
        print(f"\nUse these credentials in the API tester:")
        print(f"  X-API-Key: {business.api_key}")
        print(f"  X-API-Secret: {secret}")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()

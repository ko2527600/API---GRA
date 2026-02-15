#!/usr/bin/env python
"""Direct test without HTTP - tests the service layer directly"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, init_db
from app.services.business_service import BusinessService
from app.services.api_key_service import APIKeyService

def main():
    """Test API key generation directly"""
    print("\n" + "="*60)
    print("Direct API Key Generation Test")
    print("="*60)
    
    # Initialize database
    print("\nInitializing database...")
    init_db()
    print("✓ Database initialized")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Test 1: Generate credentials
        print("\n1. Generating API credentials...")
        api_key, api_secret = APIKeyService.generate_credentials()
        print(f"✓ API Key: {api_key}")
        print(f"✓ API Secret: {api_secret[:20]}... (truncated)")
        
        # Test 2: Create business
        print("\n2. Creating business in database...")
        business, secret = BusinessService.create_business(
            db=db,
            business_name="TEST TAXPAYER 15 PERCENT VAT",
            gra_tin="C00XXXXXXXX",
            gra_company_name="TEST TAXPAYER 15 PERCENT VAT",
            gra_security_key="UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
        )
        print(f"✓ Business created: {business.id}")
        print(f"✓ API Key: {business.api_key}")
        print(f"✓ API Secret (one-time): {secret[:20]}... (truncated)")
        
        # Test 3: Retrieve business
        print("\n3. Retrieving business...")
        retrieved = BusinessService.get_business_by_api_key(db, business.api_key)
        if retrieved:
            print(f"✓ Business retrieved: {retrieved.name}")
        else:
            print("✗ Failed to retrieve business")
        
        # Test 4: Verify credentials
        print("\n4. Verifying credentials...")
        verified = BusinessService.verify_api_credentials(db, business.api_key, secret[:72])
        if verified:
            print(f"✓ Credentials verified for: {verified.name}")
        else:
            print("✗ Credential verification failed")
        
        print("\n" + "="*60)
        print("All tests passed!")
        print("="*60)
        print(f"\nUse these credentials for testing:")
        print(f"  API Key: {business.api_key}")
        print(f"  API Secret: {secret}")
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()

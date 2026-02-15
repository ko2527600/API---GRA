#!/usr/bin/env python
"""Simple API test script"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n1. Testing Health Endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_generate_api_key():
    """Test API key generation"""
    print("\n2. Testing API Key Generation...")
    payload = {
        "business_name": "TEST TAXPAYER 15 PERCENT VAT",
        "gra_tin": "C00XXXXXXXX",
        "gra_company_name": "TEST TAXPAYER 15 PERCENT VAT",
        "gra_security_key": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/api-keys/generate",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        return response.json()
    return None

def test_purchase_cancel(api_key, api_secret):
    """Test purchase cancellation"""
    print("\n3. Testing Purchase Cancellation...")
    
    payload = {
        "company": {
            "COMPANY_NAMES": "TEST TAXPAYER 15 PERCENT VAT",
            "COMPANY_TIN": "C00XXXXXXXX",
            "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH"
        },
        "header": {
            "FLAG": "CANCEL",
            "NUM": "PUR-2026-001",
            "PURCHASE_DATE": "2026-02-11",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1"
        }
    }
    
    headers = {
        "X-API-Key": api_key,
        "X-API-Signature": "test-signature"  # In real scenario, generate HMAC
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/purchases/cancel",
        json=payload,
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 202

if __name__ == "__main__":
    print("=" * 60)
    print("GRA API Test Suite")
    print("=" * 60)
    
    # Test health
    if not test_health():
        print("Health check failed!")
        exit(1)
    
    # Generate API key
    credentials = test_generate_api_key()
    if not credentials:
        print("Failed to generate API key!")
        exit(1)
    
    api_key = credentials["api_key"]
    api_secret = credentials["api_secret"]
    
    print(f"\nGenerated Credentials:")
    print(f"  API Key: {api_key}")
    print(f"  API Secret: {api_secret}")
    
    # Test purchase cancellation
    test_purchase_cancel(api_key, api_secret)
    
    print("\n" + "=" * 60)
    print("Tests Complete!")
    print("=" * 60)

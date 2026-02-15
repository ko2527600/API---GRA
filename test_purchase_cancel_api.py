#!/usr/bin/env python
"""
Test script for Purchase Cancellation API endpoint
Tests the POST /api/v1/purchases/cancel endpoint
"""

import requests
import json
import hmac
import hashlib
import time
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key-123"
API_SECRET = "test-api-secret-456"

def generate_signature(request_body):
    """Generate HMAC-SHA256 signature for request"""
    message = request_body.encode('utf-8')
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        message,
        hashlib.sha256
    ).hexdigest()
    return signature

def test_purchase_cancellation():
    """Test the purchase cancellation endpoint"""
    
    print("=" * 80)
    print("Testing Purchase Cancellation Endpoint")
    print("=" * 80)
    
    # Test 1: Valid purchase cancellation request
    print("\n[TEST 1] Valid Purchase Cancellation Request")
    print("-" * 80)
    
    cancellation_data = {
        "company": {
            "COMPANY_NAMES": "ABC COMPANY LTD",
            "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
            "COMPANY_TIN": "C00XXXXXXXX"
        },
        "header": {
            "FLAG": "CANCEL",
            "NUM": "PUR-2026-001",
            "PURCHASE_DATE": "2026-02-11",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1"
        }
    }
    
    request_body = json.dumps(cancellation_data)
    signature = generate_signature(request_body)
    
    headers = {
        "X-API-Key": API_KEY,
        "X-API-Signature": signature,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/purchases/cancel",
            data=request_body,
            headers=headers,
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 202:
            print("✅ TEST PASSED: Received 202 Accepted")
            response_data = response.json()
            submission_id = response_data.get("submission_id")
            print(f"Submission ID: {submission_id}")
            return submission_id
        else:
            print(f"❌ TEST FAILED: Expected 202, got {response.status_code}")
            return None
    
    except requests.exceptions.ConnectionError:
        print("❌ TEST FAILED: Could not connect to API server")
        print("Make sure the server is running on http://localhost:8000")
        return None
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")
        return None

def test_invalid_flag():
    """Test with invalid FLAG"""
    print("\n[TEST 2] Invalid FLAG (should fail)")
    print("-" * 80)
    
    cancellation_data = {
        "company": {
            "COMPANY_NAMES": "ABC COMPANY LTD",
            "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
            "COMPANY_TIN": "C00XXXXXXXX"
        },
        "header": {
            "FLAG": "PURCHASE",  # Invalid - should be CANCEL
            "NUM": "PUR-2026-001",
            "PURCHASE_DATE": "2026-02-11",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1"
        }
    }
    
    request_body = json.dumps(cancellation_data)
    signature = generate_signature(request_body)
    
    headers = {
        "X-API-Key": API_KEY,
        "X-API-Signature": signature,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/purchases/cancel",
            data=request_body,
            headers=headers,
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 422:
            print("✅ TEST PASSED: Validation error returned (422)")
        else:
            print(f"⚠️ TEST WARNING: Expected 422, got {response.status_code}")
    
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")

def test_invalid_currency():
    """Test with invalid CURRENCY"""
    print("\n[TEST 3] Invalid CURRENCY (should fail)")
    print("-" * 80)
    
    cancellation_data = {
        "company": {
            "COMPANY_NAMES": "ABC COMPANY LTD",
            "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
            "COMPANY_TIN": "C00XXXXXXXX"
        },
        "header": {
            "FLAG": "CANCEL",
            "NUM": "PUR-2026-001",
            "PURCHASE_DATE": "2026-02-11",
            "CURRENCY": "USD",  # Invalid - should be GHS
            "EXCHANGE_RATE": "1"
        }
    }
    
    request_body = json.dumps(cancellation_data)
    signature = generate_signature(request_body)
    
    headers = {
        "X-API-Key": API_KEY,
        "X-API-Signature": signature,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/purchases/cancel",
            data=request_body,
            headers=headers,
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 422:
            print("✅ TEST PASSED: Validation error returned (422)")
        else:
            print(f"⚠️ TEST WARNING: Expected 422, got {response.status_code}")
    
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")

def test_missing_purchase_number():
    """Test with missing purchase number"""
    print("\n[TEST 4] Missing Purchase Number (should fail)")
    print("-" * 80)
    
    cancellation_data = {
        "company": {
            "COMPANY_NAMES": "ABC COMPANY LTD",
            "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
            "COMPANY_TIN": "C00XXXXXXXX"
        },
        "header": {
            "FLAG": "CANCEL",
            # NUM is missing
            "PURCHASE_DATE": "2026-02-11",
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1"
        }
    }
    
    request_body = json.dumps(cancellation_data)
    signature = generate_signature(request_body)
    
    headers = {
        "X-API-Key": API_KEY,
        "X-API-Signature": signature,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/purchases/cancel",
            data=request_body,
            headers=headers,
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 422:
            print("✅ TEST PASSED: Validation error returned (422)")
        else:
            print(f"⚠️ TEST WARNING: Expected 422, got {response.status_code}")
    
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")

def test_invalid_date_format():
    """Test with invalid date format"""
    print("\n[TEST 5] Invalid Date Format (should fail)")
    print("-" * 80)
    
    cancellation_data = {
        "company": {
            "COMPANY_NAMES": "ABC COMPANY LTD",
            "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
            "COMPANY_TIN": "C00XXXXXXXX"
        },
        "header": {
            "FLAG": "CANCEL",
            "NUM": "PUR-2026-001",
            "PURCHASE_DATE": "11-02-2026",  # Invalid format
            "CURRENCY": "GHS",
            "EXCHANGE_RATE": "1"
        }
    }
    
    request_body = json.dumps(cancellation_data)
    signature = generate_signature(request_body)
    
    headers = {
        "X-API-Key": API_KEY,
        "X-API-Signature": signature,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/purchases/cancel",
            data=request_body,
            headers=headers,
            timeout=5
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 422:
            print("✅ TEST PASSED: Validation error returned (422)")
        else:
            print(f"⚠️ TEST WARNING: Expected 422, got {response.status_code}")
    
    except Exception as e:
        print(f"❌ TEST FAILED: {str(e)}")

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  GRA External Integration API - Purchase Cancellation Endpoint Tests".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    # Give server time to start if needed
    print("\nWaiting for API server to be ready...")
    time.sleep(2)
    
    # Run tests
    submission_id = test_purchase_cancellation()
    test_invalid_flag()
    test_invalid_currency()
    test_missing_purchase_number()
    test_invalid_date_format()
    
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print("✅ All tests completed!")
    print("\nNote: If tests failed with connection errors, make sure to:")
    print("1. Start the API server: python -m uvicorn app.main:app --reload")
    print("2. Ensure the server is running on http://localhost:8000")
    print("=" * 80)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Test purchase submission endpoint"""
import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "qee1UeuqIjgpcBQRuPkjLv6fUhX5zZFe"
API_SECRET = "DAS5qwFHw6czuPL1bqwPtbI1EiilHvoI"

# Generate unique purchase number
purchase_num = f"PUR-{int(time.time())}"

# Test purchase submission
purchase_data = {
    "company": {
        "COMPANY_NAMES": "TEST TAXPAYER 15 PERCENT VAT",
        "COMPANY_SECURITY_KEY": "UUAKE3NVOTLRMQWCVUDIPOUT395KTCTH",
        "COMPANY_TIN": "C00XXXXXXXX"
    },
    "header": {
        "COMPUTATION_TYPE": "INCLUSIVE",
        "FLAG": "PURCHASE",
        "PURCHASE_TYPE": "NORMAL",
        "USER_NAME": "JOHN",
        "NUM": purchase_num,
        "SUPPLIER_NAME": "Supplier Ltd",
        "SUPPLIER_TIN": "C0022825405",
        "PURCHASE_DATE": "2026-02-12",
        "CURRENCY": "GHS",
        "EXCHANGE_RATE": "1",
        "PURCHASE_DESCRIPTION": "Office supplies purchase",
        "TOTAL_VAT": "79",
        "TOTAL_LEVY": "30",
        "TOTAL_AMOUNT": "1719",
        "ITEMS_COUNTS": "1"
    },
    "item_list": [
        {
            "ITMREF": "SUPP001",
            "ITMDES": "Office Supplies",
            "QUANTITY": "5",
            "UNITYPRICE": "100",
            "TAXCODE": "B",
            "TAXRATE": "15",
            "LEVY_AMOUNT_A": "1.25",
            "LEVY_AMOUNT_B": "1.25",
            "LEVY_AMOUNT_C": "0",
            "LEVY_AMOUNT_D": "0",
            "ITMDISCOUNT": "0",
            "ITEM_CATEGORY": "SUPPLIES"
        }
    ]
}

print("=" * 80)
print("PURCHASE SUBMISSION TEST")
print("=" * 80)
print(f"\nPurchase Number: {purchase_num}")
print(f"Endpoint: POST {API_BASE_URL}/purchases/submit")
print(f"API Key: {API_KEY}")

# Make request
headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

try:
    print("\nSending purchase submission...")
    response = requests.post(
        f"{API_BASE_URL}/purchases/submit",
        json=purchase_data,
        headers=headers,
        timeout=10
    )
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    try:
        response_data = response.json()
        print(f"\nResponse Body:")
        print(json.dumps(response_data, indent=2))
        
        if response.status_code == 202:
            submission_id = response_data.get("submission_id")
            print(f"\n✓ Purchase submission accepted!")
            print(f"  Submission ID: {submission_id}")
            print(f"  Status: {response_data.get('status')}")
            print(f"  Message: {response_data.get('message')}")
            
            # Wait a bit for async processing
            print("\nWaiting 3 seconds for async processing...")
            time.sleep(3)
            
            # Check status
            print(f"\nChecking submission status...")
            status_response = requests.get(
                f"{API_BASE_URL}/purchases/{submission_id}/status",
                headers=headers,
                timeout=10
            )
            
            print(f"Status Response: {status_response.status_code}")
            status_data = status_response.json()
            print(f"Status Data:")
            print(json.dumps(status_data, indent=2))
            
        else:
            print(f"\n✗ Unexpected status code: {response.status_code}")
    
    except json.JSONDecodeError:
        print(f"\nResponse Text: {response.text}")

except requests.exceptions.RequestException as e:
    print(f"\n✗ Request failed: {str(e)}")

print("\n" + "=" * 80)

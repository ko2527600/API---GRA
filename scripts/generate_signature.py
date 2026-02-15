#!/usr/bin/env python3
"""
Utility script to generate HMAC-SHA256 signatures for API requests.

Usage:
    python scripts/generate_signature.py \
        --api-key "your_api_key" \
        --api-secret "your_api_secret" \
        --method "POST" \
        --path "/api/v1/invoices/submit" \
        --body '{"invoice": "data"}'
"""

import argparse
import json
import hmac
import hashlib
from datetime import datetime
import sys


def generate_body_hash(body: str) -> str:
    """Generate SHA256 hash of request body"""
    if not body:
        body = ""
    return hashlib.sha256(body.encode()).hexdigest()


def generate_signature_message(
    method: str,
    path: str,
    timestamp: str,
    body_hash: str
) -> str:
    """Generate the message to be signed"""
    return f"{method}|{path}|{timestamp}|{body_hash}"


def generate_signature(api_secret: str, message: str) -> str:
    """Generate HMAC-SHA256 signature"""
    signature = hmac.new(
        key=api_secret.encode(),
        msg=message.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    return signature


def main():
    parser = argparse.ArgumentParser(
        description="Generate HMAC-SHA256 signature for API requests"
    )
    parser.add_argument(
        "--api-key",
        required=True,
        help="API key"
    )
    parser.add_argument(
        "--api-secret",
        required=True,
        help="API secret"
    )
    parser.add_argument(
        "--method",
        required=True,
        choices=["GET", "POST", "PUT", "DELETE", "PATCH"],
        help="HTTP method"
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Request path (e.g., /api/v1/invoices/submit)"
    )
    parser.add_argument(
        "--body",
        default="",
        help="Request body (JSON string or empty for GET)"
    )
    parser.add_argument(
        "--timestamp",
        default=None,
        help="ISO format timestamp (defaults to current time)"
    )
    parser.add_argument(
        "--output",
        choices=["json", "curl", "python"],
        default="json",
        help="Output format"
    )
    
    args = parser.parse_args()
    
    # Generate timestamp if not provided
    if args.timestamp is None:
        timestamp = datetime.utcnow().isoformat() + "Z"
    else:
        timestamp = args.timestamp
    
    # Generate body hash
    body_hash = generate_body_hash(args.body)
    
    # Generate message
    message = generate_signature_message(
        method=args.method,
        path=args.path,
        timestamp=timestamp,
        body_hash=body_hash
    )
    
    # Generate signature
    signature = generate_signature(args.api_secret, message)
    
    # Output in requested format
    if args.output == "json":
        output = {
            "api_key": args.api_key,
            "signature": signature,
            "timestamp": timestamp,
            "body_hash": body_hash,
            "message": message,
            "headers": {
                "X-API-Key": args.api_key,
                "X-API-Signature": signature,
                "X-API-Timestamp": timestamp,
                "Content-Type": "application/json"
            }
        }
        print(json.dumps(output, indent=2))
    
    elif args.output == "curl":
        curl_cmd = (
            f"curl -X {args.method} https://api.example.com{args.path} \\\n"
            f"  -H 'X-API-Key: {args.api_key}' \\\n"
            f"  -H 'X-API-Signature: {signature}' \\\n"
            f"  -H 'X-API-Timestamp: {timestamp}' \\\n"
            f"  -H 'Content-Type: application/json'"
        )
        if args.body:
            curl_cmd += f" \\\n  -d '{args.body}'"
        print(curl_cmd)
    
    elif args.output == "python":
        python_code = f"""
import requests
import hmac
import hashlib
from datetime import datetime
import json

# Configuration
API_KEY = "{args.api_key}"
API_SECRET = "{args.api_secret}"
BASE_URL = "https://api.example.com"

# Request data
method = "{args.method}"
path = "{args.path}"
body = {repr(args.body)}
timestamp = "{timestamp}"

# Generate signature
body_hash = hashlib.sha256(body.encode()).hexdigest()
message = f"{{method}}|{{path}}|{{timestamp}}|{{body_hash}}"
signature = hmac.new(
    key=API_SECRET.encode(),
    msg=message.encode(),
    digestmod=hashlib.sha256
).hexdigest()

# Make request
headers = {{
    "X-API-Key": API_KEY,
    "X-API-Signature": signature,
    "X-API-Timestamp": timestamp,
    "Content-Type": "application/json"
}}

response = requests.{args.method.lower()}(
    f"{{BASE_URL}}{{path}}",
    data=body,
    headers=headers
)

print(f"Status: {{response.status_code}}")
print(f"Response: {{response.json()}}")
"""
        print(python_code)


if __name__ == "__main__":
    main()

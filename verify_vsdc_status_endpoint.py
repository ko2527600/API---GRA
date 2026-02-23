#!/usr/bin/env python
"""Verify VSDC status retrieval endpoint implementation"""
import sys
from datetime import datetime, timedelta

# Check endpoint implementation
print("=" * 60)
print("VSDC Status Retrieval Endpoint Verification")
print("=" * 60)

# 1. Check endpoint exists
print("\n1. Checking endpoint implementation...")
try:
    from app.api.endpoints.vsdc import get_vsdc_status
    print("   ✓ Endpoint function exists: get_vsdc_status")
except ImportError as e:
    print(f"   ✗ Failed to import endpoint: {e}")
    sys.exit(1)

# 2. Check response schema
p
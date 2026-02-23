#!/usr/bin/env python
"""Test VSDC schemas without database connection"""
import sys
import os

# Set environment to use SQLite for testing
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

try:
    print("Testing VSDC schema imports...")
    from app.schemas.vsdc import (
        VSDCHealthCheckRequestSchema,
        VSDCHealthCheckResponseSchema,
        VSDCStatusRetrievalSchema
    )
    print("✓ VSDC schemas imported successfully")
    
    # Test schema validation
    print("\nTesting schema validation...")
    from datetime import datetime
    
    response_schema = VSDCHealthCheckResponseSchema(
        status="UP",
        sdc_id="SDC-001",
        gra_response_code=None,
        checked_at=datetime.utcnow(),
        expires_at=datetime.utcnow(),
        message="VSDC is up"
    )
    print("✓ VSDCHealthCheckResponseSchema created successfully")
    print(f"  - Status: {response_schema.status}")
    print(f"  - SDC ID: {response_schema.sdc_id}")
    print(f"  - Message: {response_schema.message}")
    
    status_schema = VSDCStatusRetrievalSchema(
        status="UP",
        sdc_id="SDC-001",
        last_checked_at=datetime.utcnow(),
        uptime_percentage=100.0,
        is_cached=True
    )
    print("✓ VSDCStatusRetrievalSchema created successfully")
    print(f"  - Status: {status_schema.status}")
    print(f"  - Uptime: {status_schema.uptime_percentage}%")
    print(f"  - Is Cached: {status_schema.is_cached}")
    
    # Test all status values
    print("\nTesting all status values...")
    for status_val in ["UP", "DOWN", "DEGRADED"]:
        schema = VSDCHealthCheckResponseSchema(
            status=status_val,
            sdc_id="SDC-001" if status_val == "UP" else None,
            gra_response_code=None if status_val == "UP" else "D06",
            checked_at=datetime.utcnow(),
            expires_at=datetime.utcnow(),
            message=f"VSDC is {status_val.lower()}"
        )
        print(f"✓ Status '{status_val}' validated")
    
    print("\n✅ All schema tests passed!")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

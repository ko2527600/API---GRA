#!/usr/bin/env python
"""Simple test to verify VSDC endpoint implementation"""
import sys

try:
    # Test imports
    print("Testing imports...")
    from app.api.endpoints import vsdc
    print("✓ VSDC endpoint imported successfully")
    
    from app.schemas.vsdc import (
        VSDCHealthCheckRequestSchema,
        VSDCHealthCheckResponseSchema,
        VSDCStatusRetrievalSchema
    )
    print("✓ VSDC schemas imported successfully")
    
    from app.models.models import VSDCHealthCheck
    print("✓ VSDCHealthCheck model imported successfully")
    
    # Test schema validation
    print("\nTesting schema validation...")
    request_schema = VSDCHealthCheckRequestSchema()
    print("✓ VSDCHealthCheckRequestSchema created successfully")
    
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
    
    status_schema = VSDCStatusRetrievalSchema(
        status="UP",
        sdc_id="SDC-001",
        last_checked_at=datetime.utcnow(),
        uptime_percentage=100.0,
        is_cached=True
    )
    print("✓ VSDCStatusRetrievalSchema created successfully")
    
    # Test router
    print("\nTesting router...")
    assert hasattr(vsdc, 'router'), "VSDC router not found"
    print("✓ VSDC router found")
    
    assert len(vsdc.router.routes) > 0, "No routes in VSDC router"
    print(f"✓ VSDC router has {len(vsdc.router.routes)} routes")
    
    # List routes
    for route in vsdc.router.routes:
        print(f"  - {route.path} ({route.methods})")
    
    print("\n✅ All tests passed!")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

#!/usr/bin/env python
"""Minimal test"""
import sys
print("Starting test...")
sys.stdout.flush()

try:
    print("Importing datetime...")
    from datetime import datetime
    print("✓ datetime imported")
    
    print("Importing pydantic...")
    from pydantic import BaseModel, Field
    print("✓ pydantic imported")
    
    print("Creating test schema...")
    class TestSchema(BaseModel):
        status: str = Field(..., description="Status")
        checked_at: datetime = Field(..., description="Timestamp")
    
    print("✓ Schema created")
    
    print("Creating schema instance...")
    schema = TestSchema(status="UP", checked_at=datetime.utcnow())
    print(f"✓ Schema instance created: {schema.status}")
    
    print("\n✅ All tests passed!")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

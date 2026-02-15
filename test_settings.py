#!/usr/bin/env python
"""Test settings loading"""
import os
import sys

# Set environment variables before importing app
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/API_s_GRA"
os.environ["ENCRYPTION_KEY"] = "your-encryption-key-change-in-production"
os.environ["API_SECRET_KEY"] = "your-secret-key-change-in-production"

# Clear any previously imported app modules
for module in list(sys.modules.keys()):
    if module.startswith('app'):
        del sys.modules[module]

print("Testing Settings class...")
try:
    from app.config import Settings
    print(f"✓ Settings class imported successfully")
    
    # Check if DATABASE_URL field exists
    print(f"✓ Settings fields: {Settings.model_fields.keys()}")
    
    # Try to create an instance
    settings = Settings()
    print(f"✓ Settings instance created")
    print(f"✓ DATABASE_URL: {settings.DATABASE_URL}")
    print(f"✓ ENCRYPTION_KEY: {settings.ENCRYPTION_KEY}")
    print(f"✓ API_SECRET_KEY: {settings.API_SECRET_KEY}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

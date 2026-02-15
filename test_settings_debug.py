#!/usr/bin/env python
"""Test settings loading with debug"""
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
    
    # Check the class definition
    import inspect
    print(f"\nSettings class source file: {inspect.getfile(Settings)}")
    
    # Get all annotations
    print(f"\nAll annotations in Settings:")
    for name, annotation in Settings.model_fields.items():
        print(f"  - {name}: {annotation}")
    
    # Try to create an instance with debug
    print(f"\nCreating Settings instance...")
    settings = Settings()
    print(f"✓ Settings instance created")
    
    # Try to access fields
    print(f"\nTrying to access fields:")
    print(f"  APP_NAME: {settings.APP_NAME}")
    print(f"  ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"  DEBUG: {settings.DEBUG}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

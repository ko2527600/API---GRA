import os
import sys

# Set environment variables BEFORE importing anything from app
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENCRYPTION_KEY"] = "test-encryption-key-for-testing-only-12345"

print("Environment variables set")

print("Step 1: Import encryption_manager")
from app.utils.encryption import encryption_manager
print(f"OK: {encryption_manager}")

print("Step 2: Import business_service")
from app.services.business_service import BusinessService
print("OK")

print("All imports successful!")

import sys
import traceback

print("Step 1: Import sqlalchemy")
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
print("OK")

print("Step 2: Import uuid")
from uuid import UUID
from typing import Optional
import uuid
print("OK")

print("Step 3: Import models")
from app.models.models import Business
print("OK")

print("Step 4: Import api_key_service")
from app.services.api_key_service import APIKeyService
print("OK")

print("Step 5: Import encryption_manager")
from app.utils.encryption import encryption_manager
print("OK")

print("Step 6: Import logger")
from app.logger import logger
print("OK")

print("Step 7: Import business_service module")
import app.services.business_service
print("OK")

print("Step 8: Check what's in the module")
print(dir(app.services.business_service))

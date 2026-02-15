#!/usr/bin/env python
"""Initialize the database by creating all tables"""
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

from app.database import engine, init_db
from app.models.models import Base

print("Creating database tables...")
try:
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully!")
    print("\nTables created:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")
except Exception as e:
    print(f"✗ Error creating tables: {str(e)}")
    sys.exit(1)

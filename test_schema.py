#!/usr/bin/env python
"""Test script to verify database schema"""
from app.models.models import *
from app.models.base import Base

# Get all table names
tables = sorted([table.name for table in Base.metadata.tables.values()])

print("Database Schema Verification")
print("=" * 50)
print(f"Total tables: {len(tables)}")
print("\nTables created:")
for table in tables:
    print(f"  - {table}")

# Expected tables from requirements
expected_tables = [
    'businesses',
    'submissions',
    'invoices',
    'invoice_items',
    'refunds',
    'refund_items',
    'purchases',
    'purchase_items',
    'items',
    'inventory',
    'tin_validations',
    'tag_descriptions',
    'z_reports',
    'vsdc_health_checks',
    'audit_logs',
    'webhooks',
    'webhook_deliveries',
]

print("\n" + "=" * 50)
print("Verification Results:")
print("=" * 50)

missing_tables = set(expected_tables) - set(tables)
extra_tables = set(tables) - set(expected_tables)

if not missing_tables:
    print("✓ All required tables are present")
else:
    print(f"✗ Missing tables: {missing_tables}")

if not extra_tables:
    print("✓ No extra tables")
else:
    print(f"ℹ Extra tables: {extra_tables}")

print("\n" + "=" * 50)
if not missing_tables:
    print("✓ Database schema is complete and correct!")
else:
    print("✗ Database schema is incomplete")

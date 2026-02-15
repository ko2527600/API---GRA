#!/usr/bin/env python
"""Test script to verify database schema details"""
from app.models.models import *
from app.models.base import Base
from sqlalchemy import inspect

print("Database Schema Details Verification")
print("=" * 70)

# Get all tables
tables = Base.metadata.tables

# Expected table structure
expected_structure = {
    'businesses': {
        'columns': ['id', 'name', 'api_key', 'api_secret', 'gra_tin', 'gra_company_name', 'gra_security_key', 'status', 'created_at', 'updated_at'],
        'indexes': ['idx_business_api_key', 'idx_business_status'],
        'unique_constraints': ['uq_api_key']
    },
    'submissions': {
        'columns': ['id', 'business_id', 'submission_type', 'submission_status', 'gra_response_code', 'gra_response_message', 'gra_invoice_id', 'gra_qr_code', 'gra_receipt_num', 'submitted_at', 'completed_at', 'raw_request', 'raw_response', 'error_details', 'created_at', 'updated_at'],
        'indexes': ['idx_submission_business_id', 'idx_submission_status', 'idx_submission_type', 'idx_submission_created_at'],
    },
    'invoices': {
        'columns': ['id', 'submission_id', 'business_id', 'invoice_num', 'client_name', 'client_tin', 'invoice_date', 'computation_type', 'total_vat', 'total_levy', 'total_amount', 'items_count', 'created_at', 'updated_at'],
        'indexes': ['idx_invoice_business_id', 'idx_invoice_num', 'idx_invoice_date'],
        'unique_constraints': ['uq_business_invoice_num']
    },
    'invoice_items': {
        'columns': ['id', 'invoice_id', 'itmref', 'itmdes', 'quantity', 'unityprice', 'taxcode', 'taxrate', 'levy_amount_a', 'levy_amount_b', 'levy_amount_c', 'levy_amount_d', 'itmdiscount', 'item_total', 'item_category', 'created_at', 'updated_at'],
        'indexes': ['idx_invoice_item_invoice_id', 'idx_invoice_item_itmref'],
    },
    'refunds': {
        'columns': ['id', 'submission_id', 'business_id', 'refund_id', 'original_invoice_id', 'refund_date', 'total_vat', 'total_levy', 'total_amount', 'items_count', 'created_at', 'updated_at'],
        'indexes': ['idx_refund_business_id', 'idx_refund_id'],
    },
    'refund_items': {
        'columns': ['id', 'refund_id', 'itmref', 'it
"""Initial schema creation

Revision ID: 001
Revises: 
Create Date: 2026-02-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create businesses table
    op.create_table(
        'businesses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('api_key', sa.String(255), nullable=False),
        sa.Column('api_secret', sa.String(255), nullable=False),
        sa.Column('gra_tin', sa.String(255), nullable=False),
        sa.Column('gra_company_name', sa.String(255), nullable=False),
        sa.Column('gra_security_key', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_key', name='uq_api_key')
    )
    op.create_index('idx_business_api_key', 'businesses', ['api_key'])
    op.create_index('idx_business_status', 'businesses', ['status'])

    # Create submissions table
    op.create_table(
        'submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submission_type', sa.String(50), nullable=False),
        sa.Column('submission_status', sa.String(50), nullable=False, server_default='RECEIVED'),
        sa.Column('gra_response_code', sa.String(50), nullable=True),
        sa.Column('gra_response_message', sa.Text(), nullable=True),
        sa.Column('gra_invoice_id', sa.String(255), nullable=True),
        sa.Column('gra_qr_code', sa.Text(), nullable=True),
        sa.Column('gra_receipt_num', sa.String(255), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('raw_request', sa.JSON(), nullable=False),
        sa.Column('raw_response', sa.JSON(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_submission_business_id', 'submissions', ['business_id'])
    op.create_index('idx_submission_status', 'submissions', ['submission_status'])
    op.create_index('idx_submission_type', 'submissions', ['submission_type'])
    op.create_index('idx_submission_created_at', 'submissions', ['created_at'])

    # Create invoices table
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invoice_num', sa.String(255), nullable=False),
        sa.Column('client_name', sa.String(255), nullable=False),
        sa.Column('client_tin', sa.String(50), nullable=True),
        sa.Column('invoice_date', sa.String(10), nullable=False),
        sa.Column('computation_type', sa.String(50), nullable=False),
        sa.Column('total_vat', sa.Float(), nullable=False),
        sa.Column('total_levy', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('items_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('submission_id', name='uq_submission_id'),
        sa.UniqueConstraint('business_id', 'invoice_num', name='uq_business_invoice_num')
    )
    op.create_index('idx_invoice_business_id', 'invoices', ['business_id'])
    op.create_index('idx_invoice_num', 'invoices', ['invoice_num'])
    op.create_index('idx_invoice_date', 'invoices', ['invoice_date'])

    # Create invoice_items table
    op.create_table(
        'invoice_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('itmref', sa.String(255), nullable=False),
        sa.Column('itmdes', sa.String(255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unityprice', sa.Float(), nullable=False),
        sa.Column('taxcode', sa.String(10), nullable=False),
        sa.Column('taxrate', sa.Float(), nullable=False),
        sa.Column('levy_amount_a', sa.Float(), nullable=False),
        sa.Column('levy_amount_b', sa.Float(), nullable=False),
        sa.Column('levy_amount_c', sa.Float(), nullable=False),
        sa.Column('levy_amount_d', sa.Float(), nullable=False),
        sa.Column('itmdiscount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('item_total', sa.Float(), nullable=False),
        sa.Column('item_category', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_invoice_item_invoice_id', 'invoice_items', ['invoice_id'])
    op.create_index('idx_invoice_item_itmref', 'invoice_items', ['itmref'])

    # Create refunds table
    op.create_table(
        'refunds',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('refund_id', sa.String(255), nullable=False),
        sa.Column('original_invoice_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('refund_date', sa.String(10), nullable=False),
        sa.Column('total_vat', sa.Float(), nullable=False),
        sa.Column('total_levy', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('items_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.ForeignKeyConstraint(['original_invoice_id'], ['invoices.id'], ),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('submission_id', name='uq_refund_submission_id')
    )
    op.create_index('idx_refund_business_id', 'refunds', ['business_id'])
    op.create_index('idx_refund_id', 'refunds', ['refund_id'])

    # Create refund_items table
    op.create_table(
        'refund_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('refund_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('itmref', sa.String(255), nullable=False),
        sa.Column('itmdes', sa.String(255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unityprice', sa.Float(), nullable=False),
        sa.Column('taxcode', sa.String(10), nullable=False),
        sa.Column('taxrate', sa.Float(), nullable=False),
        sa.Column('levy_amount_a', sa.Float(), nullable=False),
        sa.Column('levy_amount_b', sa.Float(), nullable=False),
        sa.Column('levy_amount_c', sa.Float(), nullable=False),
        sa.Column('levy_amount_d', sa.Float(), nullable=False),
        sa.Column('item_total', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['refund_id'], ['refunds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_refund_item_refund_id', 'refund_items', ['refund_id'])

    # Create purchases table
    op.create_table(
        'purchases',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('purchase_num', sa.String(255), nullable=False),
        sa.Column('supplier_name', sa.String(255), nullable=False),
        sa.Column('supplier_tin', sa.String(50), nullable=True),
        sa.Column('purchase_date', sa.String(10), nullable=False),
        sa.Column('total_vat', sa.Float(), nullable=False),
        sa.Column('total_levy', sa.Float(), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('items_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('submission_id', name='uq_purchase_submission_id'),
        sa.UniqueConstraint('business_id', 'purchase_num', name='uq_business_purchase_num')
    )
    op.create_index('idx_purchase_business_id', 'purchases', ['business_id'])
    op.create_index('idx_purchase_num', 'purchases', ['purchase_num'])

    # Create purchase_items table
    op.create_table(
        'purchase_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('purchase_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('itmref', sa.String(255), nullable=False),
        sa.Column('itmdes', sa.String(255), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('unityprice', sa.Float(), nullable=False),
        sa.Column('taxcode', sa.String(10), nullable=False),
        sa.Column('taxrate', sa.Float(), nullable=False),
        sa.Column('item_total', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['purchase_id'], ['purchases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_purchase_item_purchase_id', 'purchase_items', ['purchase_id'])

    # Create items table
    op.create_table(
        'items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_ref', sa.String(255), nullable=False),
        sa.Column('item_name', sa.String(255), nullable=False),
        sa.Column('item_category', sa.String(255), nullable=True),
        sa.Column('tax_code', sa.String(10), nullable=False),
        sa.Column('gra_registration_status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('gra_item_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('business_id', 'item_ref', name='uq_business_item_ref')
    )
    op.create_index('idx_item_business_id', 'items', ['business_id'])
    op.create_index('idx_item_ref', 'items', ['item_ref'])

    # Create inventory table
    op.create_table(
        'inventory',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('niki_code', sa.String(255), nullable=False),
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('gra_sync_status', sa.String(50), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('business_id', 'niki_code', name='uq_business_niki_code')
    )
    op.create_index('idx_inventory_business_id', 'inventory', ['business_id'])
    op.create_index('idx_inventory_niki_code', 'inventory', ['niki_code'])

    # Create tin_validations table
    op.create_table(
        'tin_validations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tin', sa.String(50), nullable=False),
        sa.Column('validation_status', sa.String(50), nullable=False),
        sa.Column('taxpayer_name', sa.String(255), nullable=True),
        sa.Column('gra_response_code', sa.String(50), nullable=True),
        sa.Column('cached_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('business_id', 'tin', name='uq_business_tin')
    )
    op.create_index('idx_tin_validation_business_id', 'tin_validations', ['business_id'])
    op.create_index('idx_tin_validation_tin', 'tin_validations', ['tin'])
    op.create_index('idx_tin_validation_expires_at', 'tin_validations', ['expires_at'])

    # Create tag_descriptions table
    op.create_table(
        'tag_descriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tag_code', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('business_id', 'tag_code', name='uq_business_tag_code')
    )
    op.create_index('idx_tag_description_business_id', 'tag_descriptions', ['business_id'])
    op.create_index('idx_tag_description_tag_code', 'tag_descriptions', ['tag_code'])

    # Create z_reports table
    op.create_table(
        'z_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('report_date', sa.String(10), nullable=False),
        sa.Column('inv_close', sa.Integer(), nullable=True),
        sa.Column('inv_count', sa.Integer(), nullable=True),
        sa.Column('inv_open', sa.Integer(), nullable=True),
        sa.Column('inv_vat', sa.Float(), nullable=True),
        sa.Column('inv_total', sa.Float(), nullable=True),
        sa.Column('inv_levy', sa.Float(), nullable=True),
        sa.Column('gra_response_code', sa.String(50), nullable=True),
        sa.Column('raw_response', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('business_id', 'report_date', name='uq_business_report_date')
    )
    op.create_index('idx_z_report_business_id', 'z_reports', ['business_id'])
    op.create_index('idx_z_report_date', 'z_reports', ['report_date'])

    # Create vsdc_health_checks table
    op.create_table(
        'vsdc_health_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('sdc_id', sa.String(255), nullable=True),
        sa.Column('gra_response_code', sa.String(50), nullable=True),
        sa.Column('checked_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_vsdc_health_check_business_id', 'vsdc_health_checks', ['business_id'])
    op.create_index('idx_vsdc_health_check_expires_at', 'vsdc_health_checks', ['expires_at'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('request_payload', sa.JSON(), nullable=True),
        sa.Column('response_code', sa.Integer(), nullable=False),
        sa.Column('response_status', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_log_business_id', 'audit_logs', ['business_id'])
    op.create_index('idx_audit_log_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_log_action', 'audit_logs', ['action'])

    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('webhook_url', sa.String(500), nullable=False),
        sa.Column('events', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('secret', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_webhook_business_id', 'webhooks', ['business_id'])
    op.create_index('idx_webhook_is_active', 'webhooks', ['is_active'])

    # Create webhook_deliveries table
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('webhook_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(255), nullable=False),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('response_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('delivery_status', sa.String(50), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_attempt_at', sa.DateTime(), nullable=True),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['webhook_id'], ['webhooks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_webhook_delivery_webhook_id', 'webhook_deliveries', ['webhook_id'])
    op.create_index('idx_webhook_delivery_status', 'webhook_deliveries', ['delivery_status'])
    op.create_index('idx_webhook_delivery_next_retry_at', 'webhook_deliveries', ['next_retry_at'])


def downgrade() -> None:
    op.drop_index('idx_webhook_delivery_next_retry_at', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_delivery_status', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_delivery_webhook_id', table_name='webhook_deliveries')
    op.drop_table('webhook_deliveries')
    op.drop_index('idx_webhook_is_active', table_name='webhooks')
    op.drop_index('idx_webhook_business_id', table_name='webhooks')
    op.drop_table('webhooks')
    op.drop_index('idx_audit_log_action', table_name='audit_logs')
    op.drop_index('idx_audit_log_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_log_business_id', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index('idx_vsdc_health_check_expires_at', table_name='vsdc_health_checks')
    op.drop_index('idx_vsdc_health_check_business_id', table_name='vsdc_health_checks')
    op.drop_table('vsdc_health_checks')
    op.drop_index('idx_z_report_date', table_name='z_reports')
    op.drop_index('idx_z_report_business_id', table_name='z_reports')
    op.drop_table('z_reports')
    op.drop_index('idx_tag_description_tag_code', table_name='tag_descriptions')
    op.drop_index('idx_tag_description_business_id', table_name='tag_descriptions')
    op.drop_table('tag_descriptions')
    op.drop_index('idx_tin_validation_expires_at', table_name='tin_validations')
    op.drop_index('idx_tin_validation_tin', table_name='tin_validations')
    op.drop_index('idx_tin_validation_business_id', table_name='tin_validations')
    op.drop_table('tin_validations')
    op.drop_index('idx_inventory_niki_code', table_name='inventory')
    op.drop_index('idx_inventory_business_id', table_name='inventory')
    op.drop_table('inventory')
    op.drop_index('idx_item_ref', table_name='items')
    op.drop_index('idx_item_business_id', table_name='items')
    op.drop_table('items')
    op.drop_index('idx_purchase_item_purchase_id', table_name='purchase_items')
    op.drop_table('purchase_items')
    op.drop_index('idx_purchase_num', table_name='purchases')
    op.drop_index('idx_purchase_business_id', table_name='purchases')
    op.drop_table('purchases')
    op.drop_index('idx_refund_item_refund_id', table_name='refund_items')
    op.drop_table('refund_items')
    op.drop_index('idx_refund_id', table_name='refunds')
    op.drop_index('idx_refund_business_id', table_name='refunds')
    op.drop_table('refunds')
    op.drop_index('idx_invoice_item_itmref', table_name='invoice_items')
    op.drop_index('idx_invoice_item_invoice_id', table_name='invoice_items')
    op.drop_table('invoice_items')
    op.drop_index('idx_invoice_date', table_name='invoices')
    op.drop_index('idx_invoice_num', table_name='invoices')
    op.drop_index('idx_invoice_business_id', table_name='invoices')
    op.drop_table('invoices')
    op.drop_index('idx_submission_created_at', table_name='submissions')
    op.drop_index('idx_submission_type', table_name='submissions')
    op.drop_index('idx_submission_status', table_name='submissions')
    op.drop_index('idx_submission_business_id', table_name='submissions')
    op.drop_table('submissions')
    op.drop_index('idx_business_status', table_name='businesses')
    op.drop_index('idx_business_api_key', table_name='businesses')
    op.drop_table('businesses')

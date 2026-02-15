"""Add signature/stamping fields to submissions table

Revision ID: 002
Revises: 001
Create Date: 2026-02-10 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add signature/stamping fields to submissions table
    op.add_column('submissions', sa.Column('ysdcid', sa.String(255), nullable=True))
    op.add_column('submissions', sa.Column('ysdcrecnum', sa.String(255), nullable=True))
    op.add_column('submissions', sa.Column('ysdcintdata', sa.Text(), nullable=True))
    op.add_column('submissions', sa.Column('ysdcnrc', sa.String(255), nullable=True))


def downgrade() -> None:
    # Remove signature/stamping fields from submissions table
    op.drop_column('submissions', 'ysdcnrc')
    op.drop_column('submissions', 'ysdcintdata')
    op.drop_column('submissions', 'ysdcrecnum')
    op.drop_column('submissions', 'ysdcid')

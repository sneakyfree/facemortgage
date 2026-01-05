"""Add bid_transactions table and fix schema issues

Revision ID: 008
Revises: 007
Create Date: 2026-01-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create bid_transactions table (was missing from initial migration)
    op.create_table(
        'bid_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('wallet_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('bid_wallets.id'), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('transaction_type', sa.String(30), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('stripe_payment_intent_id', sa.String(100), nullable=True),
        sa.Column('related_call_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Add index on wallet_id for faster lookups
    op.create_index('ix_bid_transactions_wallet_id', 'bid_transactions', ['wallet_id'])
    op.create_index('ix_bid_transactions_created_at', 'bid_transactions', ['created_at'])

    # Add is_super_admin column to users (was in model but not migrated)
    op.add_column('users', sa.Column('is_super_admin', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'is_super_admin')
    op.drop_index('ix_bid_transactions_created_at', table_name='bid_transactions')
    op.drop_index('ix_bid_transactions_wallet_id', table_name='bid_transactions')
    op.drop_table('bid_transactions')

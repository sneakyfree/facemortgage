"""Add grid analytics tables

Revision ID: 002
Revises: 001
Create Date: 2024-12-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create grid_impressions table for daily aggregate tracking
    op.create_table(
        'grid_impressions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('professional_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('impressions_count', sa.Integer(), default=0, nullable=False),
        sa.Column('clicks_count', sa.Integer(), default=0, nullable=False),
        sa.Column('calls_initiated', sa.Integer(), default=0, nullable=False),
        sa.Column('avg_position', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        # Unique constraint on professional_id + date for daily aggregation
        sa.UniqueConstraint('professional_id', 'date', name='uq_grid_impressions_professional_date'),
    )

    # Create index for efficient date range queries
    op.create_index('ix_grid_impressions_date', 'grid_impressions', ['date'])
    op.create_index('ix_grid_impressions_professional_id', 'grid_impressions', ['professional_id'])

    # Create grid_clicks table for detailed click tracking
    op.create_table(
        'grid_clicks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('professional_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('borrower_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('click_type', sa.String(30), nullable=False),  # 'profile_view', 'call_initiated', 'video_preview'
        sa.Column('grid_position', sa.Integer(), nullable=True),
        sa.Column('filter_context', postgresql.JSONB(), nullable=True),  # What filters were active
        sa.Column('referrer', sa.String(500), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),  # IPv6 compatible
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # Create indexes for click analytics
    op.create_index('ix_grid_clicks_professional_id', 'grid_clicks', ['professional_id'])
    op.create_index('ix_grid_clicks_created_at', 'grid_clicks', ['created_at'])
    op.create_index('ix_grid_clicks_click_type', 'grid_clicks', ['click_type'])

    # Rename metadata column to extra_data in lead_activities to avoid SQLAlchemy reserved keyword
    op.alter_column('lead_activities', 'metadata', new_column_name='extra_data')

    # Rename metadata column to extra_data in billing_transactions
    op.alter_column('billing_transactions', 'metadata', new_column_name='extra_data')


def downgrade() -> None:
    # Rename columns back
    op.alter_column('billing_transactions', 'extra_data', new_column_name='metadata')
    op.alter_column('lead_activities', 'extra_data', new_column_name='metadata')

    # Drop indexes
    op.drop_index('ix_grid_clicks_click_type', table_name='grid_clicks')
    op.drop_index('ix_grid_clicks_created_at', table_name='grid_clicks')
    op.drop_index('ix_grid_clicks_professional_id', table_name='grid_clicks')

    # Drop grid_clicks table
    op.drop_table('grid_clicks')

    # Drop indexes
    op.drop_index('ix_grid_impressions_professional_id', table_name='grid_impressions')
    op.drop_index('ix_grid_impressions_date', table_name='grid_impressions')

    # Drop grid_impressions table
    op.drop_table('grid_impressions')

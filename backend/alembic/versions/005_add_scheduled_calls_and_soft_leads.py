"""Add scheduled_calls and soft_leads tables

Revision ID: 005
Revises: 004
Create Date: 2024-12-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create scheduled_call_status enum
    scheduled_call_status = postgresql.ENUM(
        'pending', 'confirmed', 'completed', 'cancelled', 'no_show',
        name='scheduledcallstatus',
        create_type=False
    )
    op.execute("DO $$ BEGIN CREATE TYPE scheduledcallstatus AS ENUM ('pending','confirmed','completed','cancelled','no_show'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    # Create scheduled_calls table
    op.create_table(
        'scheduled_calls',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('borrower_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('contact_name', sa.String(100), nullable=False),
        sa.Column('contact_email', sa.String(255), nullable=False),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('professional_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id'), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(), nullable=False, index=True),
        sa.Column('timezone', sa.String(50), default='America/New_York'),
        sa.Column('status', scheduled_call_status, default='pending'),
        sa.Column('loan_purpose', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('reminder_sent_at', sa.DateTime(), nullable=True),
        sa.Column('completed_call_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('video_calls.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_scheduled_calls_professional_id', 'scheduled_calls', ['professional_id'])

    # Create soft_lead_status enum
    soft_lead_status = postgresql.ENUM(
        'new', 'matched', 'contacted', 'converted', 'expired',
        name='softleadstatus',
        create_type=False
    )
    op.execute("DO $$ BEGIN CREATE TYPE softleadstatus AS ENUM ('new','matched','contacted','converted','expired'); EXCEPTION WHEN duplicate_object THEN NULL; END $$")

    # Create soft_leads table
    op.create_table(
        'soft_leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('loan_purpose', sa.String(50), nullable=True),
        sa.Column('estimated_amount', sa.Integer(), nullable=True),
        sa.Column('property_state', sa.String(2), nullable=True),
        sa.Column('property_county', sa.String(100), nullable=True),
        sa.Column('preferred_language', sa.String(10), nullable=True),
        sa.Column('timeframe', sa.String(50), nullable=True),
        sa.Column('preferred_professional_type', sa.String(50), nullable=True),
        sa.Column('preferred_specialty', sa.String(100), nullable=True),
        sa.Column('status', soft_lead_status, default='new'),
        sa.Column('matched_professional_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id'), nullable=True),
        sa.Column('matched_at', sa.DateTime(), nullable=True),
        sa.Column('converted_lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leads.id'), nullable=True),
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('referrer_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_soft_leads_status', 'soft_leads', ['status'])


def downgrade() -> None:
    op.drop_index('ix_soft_leads_status')
    op.drop_index('ix_soft_leads_created_at')
    op.drop_index('ix_soft_leads_email')
    op.drop_table('soft_leads')

    op.drop_index('ix_scheduled_calls_professional_id')
    op.drop_index('ix_scheduled_calls_scheduled_for')
    op.drop_table('scheduled_calls')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS softleadstatus')
    op.execute('DROP TYPE IF EXISTS scheduledcallstatus')

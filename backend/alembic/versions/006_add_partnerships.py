"""Add partnerships and partnership_referrals tables

Revision ID: 006
Revises: 005
Create Date: 2024-12-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create partnership_status enum
    partnership_status = postgresql.ENUM(
        'pending', 'active', 'paused', 'terminated',
        name='partnershipstatus',
        create_type=False
    )
    partnership_status.create(op.get_bind(), checkfirst=True)

    # Create partnership_tier enum
    partnership_tier = postgresql.ENUM(
        'basic', 'silver', 'gold', 'platinum',
        name='partnershiptier',
        create_type=False
    )
    partnership_tier.create(op.get_bind(), checkfirst=True)

    # Create partnerships table
    op.create_table(
        'partnerships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('loan_officer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id'), nullable=False, index=True),
        sa.Column('realtor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id'), nullable=True),
        sa.Column('external_realtor_name', sa.String(100), nullable=True),
        sa.Column('external_realtor_email', sa.String(255), nullable=True),
        sa.Column('external_realtor_phone', sa.String(20), nullable=True),
        sa.Column('external_realtor_company', sa.String(200), nullable=True),
        sa.Column('status', sa.Enum('pending', 'active', 'paused', 'terminated', name='partnershipstatus'), default='pending'),
        sa.Column('tier', sa.Enum('basic', 'silver', 'gold', 'platinum', name='partnershiptier'), default='basic'),
        sa.Column('revenue_share_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('invitation_token', sa.String(64), nullable=True, unique=True),
        sa.Column('invited_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('widget_enabled', sa.Boolean(), default=False),
        sa.Column('widget_token', sa.String(64), nullable=True, unique=True),
        sa.Column('widget_config', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('terminated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_partnerships_loan_officer_id', 'partnerships', ['loan_officer_id'])
    op.create_index('ix_partnerships_realtor_id', 'partnerships', ['realtor_id'])
    op.create_index('ix_partnerships_status', 'partnerships', ['status'])

    # Create partnership_referrals table
    op.create_table(
        'partnership_referrals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('partnership_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('partnerships.id'), nullable=False, index=True),
        sa.Column('borrower_name', sa.String(100), nullable=False),
        sa.Column('borrower_email', sa.String(255), nullable=False),
        sa.Column('borrower_phone', sa.String(20), nullable=True),
        sa.Column('property_address', sa.String(500), nullable=True),
        sa.Column('loan_purpose', sa.String(50), nullable=True),
        sa.Column('estimated_amount', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), default='new'),
        sa.Column('converted_to_lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leads.id'), nullable=True),
        sa.Column('converted_to_call_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('video_calls.id'), nullable=True),
        sa.Column('source', sa.String(50), default='manual'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_partnership_referrals_partnership_id', 'partnership_referrals', ['partnership_id'])
    op.create_index('ix_partnership_referrals_status', 'partnership_referrals', ['status'])


def downgrade() -> None:
    op.drop_index('ix_partnership_referrals_status')
    op.drop_index('ix_partnership_referrals_partnership_id')
    op.drop_table('partnership_referrals')

    op.drop_index('ix_partnerships_status')
    op.drop_index('ix_partnerships_realtor_id')
    op.drop_index('ix_partnerships_loan_officer_id')
    op.drop_table('partnerships')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS partnershiptier')
    op.execute('DROP TYPE IF EXISTS partnershipstatus')

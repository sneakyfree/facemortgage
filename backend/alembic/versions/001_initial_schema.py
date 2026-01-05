"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-12-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    op.execute("CREATE TYPE usertype AS ENUM ('borrower', 'loan_officer', 'realtor', 'title_rep', 'attorney')")
    op.execute("CREATE TYPE professionalstatus AS ENUM ('offline', 'online_available', 'online_busy', 'in_call', 'away')")
    op.execute("CREATE TYPE subscriptiontier AS ENUM ('free', 'basic', 'professional', 'premium')")
    op.execute("CREATE TYPE callstatus AS ENUM ('initiated', 'ringing', 'connected', 'completed', 'missed', 'declined', 'failed')")

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('user_type', postgresql.ENUM('borrower', 'loan_officer', 'realtor', 'title_rep', 'attorney', name='usertype', create_type=False), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('email_verified', sa.Boolean(), default=False),
        sa.Column('phone_verified', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
    )

    # Specialties table
    op.create_table(
        'specialties',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
    )

    # Languages table
    op.create_table(
        'languages',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('code', sa.String(5), unique=True, nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
    )

    # Counties table
    op.create_table(
        'counties',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('state_code', sa.String(2), nullable=False),
        sa.Column('county_name', sa.String(100), nullable=False),
        sa.Column('fips_code', sa.String(5), nullable=True),
    )

    # Professional profiles table
    op.create_table(
        'professional_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('job_title', sa.String(100), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('years_experience', sa.Integer(), nullable=True),
        sa.Column('nmls_id', sa.String(20), nullable=True, index=True),
        sa.Column('nmls_verified', sa.Boolean(), default=False),
        sa.Column('nmls_verified_at', sa.DateTime(), nullable=True),
        sa.Column('office_address', postgresql.JSONB(), nullable=True),
        sa.Column('timezone', sa.String(50), default='America/New_York'),
        sa.Column('prerecorded_video_url', sa.String(500), nullable=True),
        sa.Column('webcam_enabled', sa.Boolean(), default=True),
        sa.Column('status', postgresql.ENUM('offline', 'online_available', 'online_busy', 'in_call', 'away', name='professionalstatus', create_type=False), default='offline'),
        sa.Column('status_updated_at', sa.DateTime(), nullable=True),
        sa.Column('current_bid_amount', sa.Numeric(10, 2), default=0),
        sa.Column('subscription_tier', postgresql.ENUM('free', 'basic', 'professional', 'premium', name='subscriptiontier', create_type=False), default='free'),
        sa.Column('time_online_today_seconds', sa.Integer(), default=0),
        sa.Column('total_calls_completed', sa.Integer(), default=0),
        sa.Column('avg_pickup_time_seconds', sa.Numeric(8, 2), nullable=True),
        sa.Column('total_reviews', sa.Integer(), default=0),
        sa.Column('avg_rating', sa.Numeric(3, 2), default=0.00),
        sa.Column('is_featured', sa.Boolean(), default=False),
        sa.Column('profile_complete', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Borrower profiles table
    op.create_table(
        'borrower_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('preferred_languages', postgresql.JSONB(), nullable=True),
        sa.Column('preferred_counties', postgresql.JSONB(), nullable=True),
        sa.Column('loan_purpose', sa.String(50), nullable=True),
        sa.Column('property_type', sa.String(50), nullable=True),
        sa.Column('estimated_credit_score', sa.String(20), nullable=True),
        sa.Column('contact_preference', sa.String(20), default='any'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Professional specialties junction table
    op.create_table(
        'professional_specialties',
        sa.Column('professional_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('specialty_id', sa.Integer(), sa.ForeignKey('specialties.id', ondelete='CASCADE'), primary_key=True),
    )

    # Professional languages junction table
    op.create_table(
        'professional_languages',
        sa.Column('professional_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('language_id', sa.Integer(), sa.ForeignKey('languages.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('proficiency', sa.String(20), default='fluent'),
    )

    # Professional service areas junction table
    op.create_table(
        'professional_service_areas',
        sa.Column('professional_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('county_id', sa.Integer(), sa.ForeignKey('counties.id', ondelete='CASCADE'), primary_key=True),
    )

    # Video calls table
    op.create_table(
        'video_calls',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('room_id', sa.String(100), unique=True, nullable=False),
        sa.Column('borrower_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('professional_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id'), nullable=False),
        sa.Column('initiated_at', sa.DateTime(), nullable=False),
        sa.Column('ring_started_at', sa.DateTime(), nullable=True),
        sa.Column('answered_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('pickup_time_seconds', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('status', postgresql.ENUM('initiated', 'ringing', 'connected', 'completed', 'missed', 'declined', 'failed', name='callstatus', create_type=False), default='initiated'),
        sa.Column('end_reason', sa.String(50), nullable=True),
        sa.Column('borrower_camera_on', sa.Boolean(), default=False),
        sa.Column('professional_camera_on', sa.Boolean(), default=True),
        sa.Column('recording_url', sa.String(500), nullable=True),
        sa.Column('ice_servers_used', postgresql.JSONB(), nullable=True),
        sa.Column('quality_metrics', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # Reviews table
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('video_call_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('video_calls.id'), nullable=True),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('reviewed_professional_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id'), nullable=False),
        sa.Column('overall_rating', sa.SmallInteger(), nullable=False),
        sa.Column('knowledge_rating', sa.SmallInteger(), nullable=True),
        sa.Column('communication_rating', sa.SmallInteger(), nullable=True),
        sa.Column('responsiveness_rating', sa.SmallInteger(), nullable=True),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('is_verified_call', sa.Boolean(), default=False),
        sa.Column('is_published', sa.Boolean(), default=True),
        sa.Column('is_flagged', sa.Boolean(), default=False),
        sa.Column('moderation_status', sa.String(20), default='approved'),
        sa.Column('professional_response', sa.Text(), nullable=True),
        sa.Column('professional_responded_at', sa.DateTime(), nullable=True),
        sa.Column('helpful_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Leads table
    op.create_table(
        'leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('borrower_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('professional_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id'), nullable=False),
        sa.Column('source_call_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('video_calls.id'), nullable=True),
        sa.Column('lead_status', sa.String(20), default='new'),
        sa.Column('contact_name', sa.String(200), nullable=True),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('loan_purpose', sa.String(50), nullable=True),
        sa.Column('property_address', sa.Text(), nullable=True),
        sa.Column('estimated_property_value', sa.Numeric(12, 2), nullable=True),
        sa.Column('estimated_loan_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('last_contact_at', sa.DateTime(), nullable=True),
        sa.Column('next_followup_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('estimated_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('actual_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Lead activities table
    op.create_table(
        'lead_activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # Subscription plans table
    op.create_table(
        'subscription_plans',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('tier', sa.String(20), nullable=False),
        sa.Column('monthly_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('annual_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('max_daily_leads', sa.Integer(), nullable=True),
        sa.Column('grid_priority_boost', sa.Integer(), default=0),
        sa.Column('analytics_access_level', sa.String(20), nullable=True),
        sa.Column('video_recording_enabled', sa.Boolean(), default=False),
        sa.Column('custom_branding_enabled', sa.Boolean(), default=False),
        sa.Column('features', postgresql.JSONB(), nullable=True),
        sa.Column('stripe_price_id_monthly', sa.String(100), nullable=True),
        sa.Column('stripe_price_id_annual', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('professional_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id'), nullable=False),
        sa.Column('plan_id', sa.Integer(), sa.ForeignKey('subscription_plans.id'), nullable=True),
        sa.Column('stripe_customer_id', sa.String(100), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(100), nullable=True),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('trial_end', sa.DateTime(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('card_brand', sa.String(20), nullable=True),
        sa.Column('card_last4', sa.String(4), nullable=True),
        sa.Column('card_expiry_month', sa.Integer(), nullable=True),
        sa.Column('card_expiry_year', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Bid wallets table
    op.create_table(
        'bid_wallets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('professional_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id'), unique=True, nullable=False),
        sa.Column('available_credits', sa.Numeric(10, 2), default=0),
        sa.Column('reserved_credits', sa.Numeric(10, 2), default=0),
        sa.Column('lifetime_deposits', sa.Numeric(10, 2), default=0),
        sa.Column('lifetime_spent', sa.Numeric(10, 2), default=0),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Placement bids table
    op.create_table(
        'placement_bids',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('professional_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id'), nullable=False),
        sa.Column('daily_budget', sa.Numeric(10, 2), nullable=False),
        sa.Column('bid_per_impression', sa.Numeric(6, 4), nullable=True),
        sa.Column('bid_per_click', sa.Numeric(8, 2), nullable=True),
        sa.Column('target_counties', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('target_languages', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('target_specialties', postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column('target_hours', postgresql.JSONB(), nullable=True),
        sa.Column('daily_spent', sa.Numeric(10, 2), default=0),
        sa.Column('total_spent', sa.Numeric(12, 2), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Billing transactions table
    op.create_table(
        'billing_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('professional_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('professional_profiles.id'), nullable=False),
        sa.Column('transaction_type', sa.String(30), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('stripe_payment_intent_id', sa.String(100), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('billing_transactions')
    op.drop_table('placement_bids')
    op.drop_table('bid_wallets')
    op.drop_table('subscriptions')
    op.drop_table('subscription_plans')
    op.drop_table('lead_activities')
    op.drop_table('leads')
    op.drop_table('reviews')
    op.drop_table('video_calls')
    op.drop_table('professional_service_areas')
    op.drop_table('professional_languages')
    op.drop_table('professional_specialties')
    op.drop_table('borrower_profiles')
    op.drop_table('professional_profiles')
    op.drop_table('counties')
    op.drop_table('languages')
    op.drop_table('specialties')
    op.drop_table('users')
    op.execute('DROP TYPE callstatus')
    op.execute('DROP TYPE subscriptiontier')
    op.execute('DROP TYPE professionalstatus')
    op.execute('DROP TYPE usertype')

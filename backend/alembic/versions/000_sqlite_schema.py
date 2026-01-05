"""SQLite-compatible unified schema

Revision ID: 000_sqlite
Revises: None
Create Date: 2026-01-05

This migration creates the full schema using SQLite-compatible types.
For PostgreSQL deployments, use migrations 001-009 instead.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '000_sqlite'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('user_type', sa.String(20), nullable=False),  # borrower, loan_officer, realtor, title_rep, attorney
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('email_verified', sa.Boolean(), default=False),
        sa.Column('phone_verified', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('device_tokens', sa.JSON(), nullable=True),
        sa.Column('push_enabled', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('last_platform', sa.String(20), nullable=True),
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
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('company_name', sa.String(255), nullable=True),
        sa.Column('job_title', sa.String(100), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('years_experience', sa.Integer(), nullable=True),
        sa.Column('nmls_id', sa.String(20), nullable=True, index=True),
        sa.Column('nmls_verified', sa.Boolean(), default=False),
        sa.Column('nmls_verified_at', sa.DateTime(), nullable=True),
        sa.Column('office_address', sa.JSON(), nullable=True),
        sa.Column('timezone', sa.String(50), default='America/New_York'),
        sa.Column('prerecorded_video_url', sa.String(500), nullable=True),
        sa.Column('webcam_enabled', sa.Boolean(), default=True),
        sa.Column('status', sa.String(20), default='offline'),  # offline, online_available, online_busy, in_call, away
        sa.Column('status_updated_at', sa.DateTime(), nullable=True),
        sa.Column('current_bid_amount', sa.Numeric(10, 2), default=0),
        sa.Column('subscription_tier', sa.String(20), default='free'),  # free, basic, professional, premium
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
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('preferred_languages', sa.JSON(), nullable=True),
        sa.Column('preferred_counties', sa.JSON(), nullable=True),
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
        sa.Column('professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('specialty_id', sa.Integer(), sa.ForeignKey('specialties.id', ondelete='CASCADE'), primary_key=True),
    )

    # Professional languages junction table
    op.create_table(
        'professional_languages',
        sa.Column('professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('language_id', sa.Integer(), sa.ForeignKey('languages.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('proficiency', sa.String(20), default='fluent'),
    )

    # Professional service areas junction table
    op.create_table(
        'professional_service_areas',
        sa.Column('professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('county_id', sa.Integer(), sa.ForeignKey('counties.id', ondelete='CASCADE'), primary_key=True),
    )

    # Video calls table
    op.create_table(
        'video_calls',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('room_id', sa.String(100), unique=True, nullable=False),
        sa.Column('borrower_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id'), nullable=False),
        sa.Column('initiated_at', sa.DateTime(), nullable=False),
        sa.Column('ring_started_at', sa.DateTime(), nullable=True),
        sa.Column('answered_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('pickup_time_seconds', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), default='initiated'),  # initiated, ringing, connected, completed, missed, declined, failed
        sa.Column('end_reason', sa.String(50), nullable=True),
        sa.Column('borrower_camera_on', sa.Boolean(), default=False),
        sa.Column('professional_camera_on', sa.Boolean(), default=True),
        sa.Column('recording_url', sa.String(500), nullable=True),
        sa.Column('ice_servers_used', sa.JSON(), nullable=True),
        sa.Column('quality_metrics', sa.JSON(), nullable=True),
        sa.Column('anonymous_session_id', sa.String(64), nullable=True),
        sa.Column('anonymous_device_fingerprint', sa.String(256), nullable=True),
        sa.Column('captured_name', sa.String(100), nullable=True),
        sa.Column('captured_email', sa.String(255), nullable=True),
        sa.Column('captured_phone', sa.String(20), nullable=True),
        sa.Column('lead_captured_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_video_calls_anonymous_session_id', 'video_calls', ['anonymous_session_id'])
    op.create_index('ix_video_calls_borrower_id', 'video_calls', ['borrower_id'])
    op.create_index('ix_video_calls_professional_id', 'video_calls', ['professional_id'])
    op.create_index('ix_video_calls_professional_status', 'video_calls', ['professional_id', 'status'])

    # Reviews table
    op.create_table(
        'reviews',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('video_call_id', sa.String(36), sa.ForeignKey('video_calls.id'), nullable=True),
        sa.Column('reviewer_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('reviewed_professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id'), nullable=False),
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
    op.create_index('ix_reviews_reviewer_id', 'reviews', ['reviewer_id'])
    op.create_index('ix_reviews_reviewed_professional_id', 'reviews', ['reviewed_professional_id'])

    # Leads table
    op.create_table(
        'leads',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('borrower_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id'), nullable=False),
        sa.Column('source_call_id', sa.String(36), sa.ForeignKey('video_calls.id'), nullable=True),
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
    op.create_index('ix_leads_professional_id', 'leads', ['professional_id'])
    op.create_index('ix_leads_professional_status', 'leads', ['professional_id', 'lead_status'])

    # Lead activities table
    op.create_table(
        'lead_activities',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('lead_id', sa.String(36), sa.ForeignKey('leads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('performed_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_lead_activities_lead_id', 'lead_activities', ['lead_id'])

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
        sa.Column('features', sa.JSON(), nullable=True),
        sa.Column('stripe_price_id_monthly', sa.String(100), nullable=True),
        sa.Column('stripe_price_id_annual', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )

    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id'), nullable=False),
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
    op.create_index('ix_subscriptions_professional_id', 'subscriptions', ['professional_id'])

    # Bid wallets table
    op.create_table(
        'bid_wallets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id'), unique=True, nullable=False),
        sa.Column('available_credits', sa.Numeric(10, 2), default=0),
        sa.Column('reserved_credits', sa.Numeric(10, 2), default=0),
        sa.Column('lifetime_deposits', sa.Numeric(10, 2), default=0),
        sa.Column('lifetime_spent', sa.Numeric(10, 2), default=0),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    # Bid transactions table
    op.create_table(
        'bid_transactions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('wallet_id', sa.String(36), sa.ForeignKey('bid_wallets.id'), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('transaction_type', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reference_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_bid_transactions_wallet_id', 'bid_transactions', ['wallet_id'])

    # Placement bids table
    op.create_table(
        'placement_bids',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id'), nullable=False),
        sa.Column('daily_budget', sa.Numeric(10, 2), nullable=False),
        sa.Column('bid_per_impression', sa.Numeric(6, 4), nullable=True),
        sa.Column('bid_per_click', sa.Numeric(8, 2), nullable=True),
        sa.Column('target_counties', sa.JSON(), nullable=True),
        sa.Column('target_languages', sa.JSON(), nullable=True),
        sa.Column('target_specialties', sa.JSON(), nullable=True),
        sa.Column('target_hours', sa.JSON(), nullable=True),
        sa.Column('daily_spent', sa.Numeric(10, 2), default=0),
        sa.Column('total_spent', sa.Numeric(12, 2), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_placement_bids_professional_id', 'placement_bids', ['professional_id'])

    # Billing transactions table
    op.create_table(
        'billing_transactions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id'), nullable=False),
        sa.Column('transaction_type', sa.String(30), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('stripe_payment_intent_id', sa.String(100), nullable=True),
        sa.Column('stripe_invoice_id', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_billing_transactions_professional_id', 'billing_transactions', ['professional_id'])

    # Grid impressions table
    op.create_table(
        'grid_impressions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('impressions_count', sa.Integer(), default=0, nullable=False),
        sa.Column('clicks_count', sa.Integer(), default=0, nullable=False),
        sa.Column('calls_initiated', sa.Integer(), default=0, nullable=False),
        sa.Column('calls_connected', sa.Integer(), default=0, nullable=False),
        sa.Column('avg_position', sa.Numeric(5, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_grid_impressions_professional_date', 'grid_impressions', ['professional_id', 'date'], unique=True)

    # Grid click events table
    op.create_table(
        'grid_click_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', sa.String(64), nullable=True),
        sa.Column('event_type', sa.String(30), nullable=False),
        sa.Column('grid_position', sa.Integer(), nullable=True),
        sa.Column('filters_applied', sa.JSON(), nullable=True),
        sa.Column('device_type', sa.String(20), nullable=True),
        sa.Column('referrer', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_grid_click_events_professional_id', 'grid_click_events', ['professional_id'])
    op.create_index('ix_grid_click_events_session_id', 'grid_click_events', ['session_id'])

    # Scheduled calls table
    op.create_table(
        'scheduled_calls',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('borrower_id', sa.String(36), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('contact_name', sa.String(200), nullable=False),
        sa.Column('contact_email', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(20), nullable=True),
        sa.Column('scheduled_start', sa.DateTime(), nullable=False),
        sa.Column('scheduled_end', sa.DateTime(), nullable=False),
        sa.Column('timezone', sa.String(50), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),  # pending, confirmed, completed, cancelled, no_show
        sa.Column('reminder_sent', sa.Boolean(), default=False),
        sa.Column('confirmation_token', sa.String(64), nullable=True),
        sa.Column('video_call_id', sa.String(36), sa.ForeignKey('video_calls.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_scheduled_calls_professional_id', 'scheduled_calls', ['professional_id'])
    op.create_index('ix_scheduled_calls_scheduled_start', 'scheduled_calls', ['scheduled_start'])
    op.create_index('ix_scheduled_calls_confirmation_token', 'scheduled_calls', ['confirmation_token'], unique=True)

    # Soft leads table
    op.create_table(
        'soft_leads',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_id', sa.String(64), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('name', sa.String(200), nullable=True),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('page_url', sa.String(500), nullable=True),
        sa.Column('utm_source', sa.String(100), nullable=True),
        sa.Column('utm_medium', sa.String(100), nullable=True),
        sa.Column('utm_campaign', sa.String(100), nullable=True),
        sa.Column('device_type', sa.String(20), nullable=True),
        sa.Column('converted_to_lead_id', sa.String(36), sa.ForeignKey('leads.id', ondelete='SET NULL'), nullable=True),
        sa.Column('converted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_soft_leads_professional_id', 'soft_leads', ['professional_id'])
    op.create_index('ix_soft_leads_email', 'soft_leads', ['email'])
    op.create_index('ix_soft_leads_session_id', 'soft_leads', ['session_id'])

    # Partnerships table
    op.create_table(
        'partnerships',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('initiator_id', sa.String(36), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('partner_id', sa.String(36), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),  # pending, active, paused, terminated
        sa.Column('tier', sa.String(20), default='basic'),  # basic, preferred, exclusive
        sa.Column('referral_fee_percent', sa.Numeric(5, 2), nullable=True),
        sa.Column('referral_fee_flat', sa.Numeric(10, 2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_partnerships_initiator_id', 'partnerships', ['initiator_id'])
    op.create_index('ix_partnerships_partner_id', 'partnerships', ['partner_id'])
    op.create_index('ix_partnerships_unique', 'partnerships', ['initiator_id', 'partner_id'], unique=True)

    # Partnership referrals table
    op.create_table(
        'partnership_referrals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('partnership_id', sa.String(36), sa.ForeignKey('partnerships.id', ondelete='CASCADE'), nullable=False),
        sa.Column('referring_professional_id', sa.String(36), sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lead_id', sa.String(36), sa.ForeignKey('leads.id', ondelete='SET NULL'), nullable=True),
        sa.Column('video_call_id', sa.String(36), sa.ForeignKey('video_calls.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),  # pending, accepted, completed, rejected
        sa.Column('referral_fee_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('fee_paid', sa.Boolean(), default=False),
        sa.Column('fee_paid_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_partnership_referrals_partnership_id', 'partnership_referrals', ['partnership_id'])
    op.create_index('ix_partnership_referrals_referring_professional_id', 'partnership_referrals', ['referring_professional_id'])


def downgrade() -> None:
    op.drop_table('partnership_referrals')
    op.drop_table('partnerships')
    op.drop_table('soft_leads')
    op.drop_table('scheduled_calls')
    op.drop_table('grid_click_events')
    op.drop_table('grid_impressions')
    op.drop_table('billing_transactions')
    op.drop_table('placement_bids')
    op.drop_table('bid_transactions')
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

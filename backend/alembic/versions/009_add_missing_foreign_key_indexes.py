"""Add missing foreign key indexes for performance

Revision ID: 009
Revises: 008
Create Date: 2026-01-05

This migration adds indexes to foreign key columns that were missing indexes.
Foreign keys are not automatically indexed in PostgreSQL, and without indexes,
lookups on these columns require full table scans.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # VideoCall indexes
    op.create_index('ix_video_calls_borrower_id', 'video_calls', ['borrower_id'])
    op.create_index('ix_video_calls_professional_id', 'video_calls', ['professional_id'])
    op.create_index('ix_video_calls_professional_status', 'video_calls', ['professional_id', 'status'])

    # Lead indexes
    op.create_index('ix_leads_borrower_id', 'leads', ['borrower_id'])
    op.create_index('ix_leads_professional_id', 'leads', ['professional_id'])
    op.create_index('ix_leads_source_call_id', 'leads', ['source_call_id'])
    op.create_index('ix_leads_professional_status', 'leads', ['professional_id', 'lead_status'])

    # LeadActivity indexes
    op.create_index('ix_lead_activities_lead_id', 'lead_activities', ['lead_id'])
    op.create_index('ix_lead_activities_performed_by', 'lead_activities', ['performed_by'])

    # Review indexes
    op.create_index('ix_reviews_video_call_id', 'reviews', ['video_call_id'])
    op.create_index('ix_reviews_reviewer_id', 'reviews', ['reviewer_id'])
    op.create_index('ix_reviews_reviewed_professional_id', 'reviews', ['reviewed_professional_id'])

    # Subscription indexes
    op.create_index('ix_subscriptions_professional_id', 'subscriptions', ['professional_id'])
    op.create_index('ix_subscriptions_plan_id', 'subscriptions', ['plan_id'])

    # PlacementBid indexes
    op.create_index('ix_placement_bids_professional_id', 'placement_bids', ['professional_id'])

    # BillingTransaction indexes
    op.create_index('ix_billing_transactions_professional_id', 'billing_transactions', ['professional_id'])

    # GridClick indexes
    op.create_index('ix_grid_clicks_borrower_id', 'grid_clicks', ['borrower_id'])

    # ScheduledCall indexes
    op.create_index('ix_scheduled_calls_borrower_id', 'scheduled_calls', ['borrower_id'])
    op.create_index('ix_scheduled_calls_professional_id', 'scheduled_calls', ['professional_id'])
    op.create_index('ix_scheduled_calls_professional_scheduled', 'scheduled_calls', ['professional_id', 'scheduled_for'])

    # SoftLead indexes
    op.create_index('ix_soft_leads_matched_professional_id', 'soft_leads', ['matched_professional_id'])
    op.create_index('ix_soft_leads_converted_lead_id', 'soft_leads', ['converted_lead_id'])

    # Partnership indexes
    op.create_index('ix_partnerships_realtor_id', 'partnerships', ['realtor_id'])

    # PartnershipReferral indexes
    op.create_index('ix_partnership_referrals_converted_to_lead_id', 'partnership_referrals', ['converted_to_lead_id'])
    op.create_index('ix_partnership_referrals_converted_to_call_id', 'partnership_referrals', ['converted_to_call_id'])


def downgrade() -> None:
    # PartnershipReferral indexes
    op.drop_index('ix_partnership_referrals_converted_to_call_id', table_name='partnership_referrals')
    op.drop_index('ix_partnership_referrals_converted_to_lead_id', table_name='partnership_referrals')

    # Partnership indexes
    op.drop_index('ix_partnerships_realtor_id', table_name='partnerships')

    # SoftLead indexes
    op.drop_index('ix_soft_leads_converted_lead_id', table_name='soft_leads')
    op.drop_index('ix_soft_leads_matched_professional_id', table_name='soft_leads')

    # ScheduledCall indexes
    op.drop_index('ix_scheduled_calls_professional_scheduled', table_name='scheduled_calls')
    op.drop_index('ix_scheduled_calls_professional_id', table_name='scheduled_calls')
    op.drop_index('ix_scheduled_calls_borrower_id', table_name='scheduled_calls')

    # GridClick indexes
    op.drop_index('ix_grid_clicks_borrower_id', table_name='grid_clicks')

    # BillingTransaction indexes
    op.drop_index('ix_billing_transactions_professional_id', table_name='billing_transactions')

    # PlacementBid indexes
    op.drop_index('ix_placement_bids_professional_id', table_name='placement_bids')

    # Subscription indexes
    op.drop_index('ix_subscriptions_plan_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_professional_id', table_name='subscriptions')

    # Review indexes
    op.drop_index('ix_reviews_reviewed_professional_id', table_name='reviews')
    op.drop_index('ix_reviews_reviewer_id', table_name='reviews')
    op.drop_index('ix_reviews_video_call_id', table_name='reviews')

    # LeadActivity indexes
    op.drop_index('ix_lead_activities_performed_by', table_name='lead_activities')
    op.drop_index('ix_lead_activities_lead_id', table_name='lead_activities')

    # Lead indexes
    op.drop_index('ix_leads_professional_status', table_name='leads')
    op.drop_index('ix_leads_source_call_id', table_name='leads')
    op.drop_index('ix_leads_professional_id', table_name='leads')
    op.drop_index('ix_leads_borrower_id', table_name='leads')

    # VideoCall indexes
    op.drop_index('ix_video_calls_professional_status', table_name='video_calls')
    op.drop_index('ix_video_calls_professional_id', table_name='video_calls')
    op.drop_index('ix_video_calls_borrower_id', table_name='video_calls')

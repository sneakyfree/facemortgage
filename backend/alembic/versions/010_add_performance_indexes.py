"""Add performance indexes for common query patterns

Revision ID: 010
Revises: 009
Create Date: 2026-01-07

Adds indexes optimized for:
- Professional grid queries (status filtering)
- Soft lead matching
- Time-based queries
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Professional grid indexes - most common queries filter by status
    # Partial index for available professionals (most common query)
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_professionals_available
        ON professional_profiles(status, subscription_tier, current_bid_amount DESC)
        WHERE status = 'online_available'
    """)

    # Index for professionals by status with rating (for grid sorting)
    op.create_index(
        'ix_professionals_status_rating',
        'professional_profiles',
        ['status', 'avg_rating'],
    )

    # Index for subscription tier filtering (common in billing queries)
    op.create_index(
        'ix_professionals_tier',
        'professional_profiles',
        ['subscription_tier'],
    )

    # User type index for filtering by professional type
    op.create_index(
        'ix_users_type_active',
        'users',
        ['user_type', 'is_active'],
    )

    # Soft lead indexes for matching queries
    op.execute("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_soft_leads_status_created
        ON soft_leads(status, created_at DESC)
        WHERE status IN ('new', 'matched', 'contacted')
    """)

    # Video calls time-based index for analytics
    op.create_index(
        'ix_video_calls_initiated_at',
        'video_calls',
        ['initiated_at'],
    )

    # Video calls by status for dashboard queries
    op.create_index(
        'ix_video_calls_status',
        'video_calls',
        ['status'],
    )

    # Reviews created_at for time-based queries
    op.create_index(
        'ix_reviews_created_at',
        'reviews',
        ['created_at'],
    )

    # Billing transactions for monthly statements
    op.create_index(
        'ix_billing_transactions_created_at',
        'billing_transactions',
        ['created_at'],
    )

    # Professional service areas - for geographic filtering
    op.create_index(
        'ix_professional_service_areas_county',
        'professional_service_areas',
        ['county_id'],
    )

    # Professional languages - for language filtering
    op.create_index(
        'ix_professional_languages_language',
        'professional_languages',
        ['language_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_professional_languages_language', table_name='professional_languages')
    op.drop_index('ix_professional_service_areas_county', table_name='professional_service_areas')
    op.drop_index('ix_billing_transactions_created_at', table_name='billing_transactions')
    op.drop_index('ix_reviews_created_at', table_name='reviews')
    op.drop_index('ix_video_calls_status', table_name='video_calls')
    op.drop_index('ix_video_calls_initiated_at', table_name='video_calls')

    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_soft_leads_status_created")

    op.drop_index('ix_users_type_active', table_name='users')
    op.drop_index('ix_professionals_tier', table_name='professional_profiles')
    op.drop_index('ix_professionals_status_rating', table_name='professional_profiles')

    op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_professionals_available")

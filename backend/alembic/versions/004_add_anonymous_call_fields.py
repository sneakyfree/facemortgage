"""Add anonymous call support fields to video_calls table.

Revision ID: 004
Revises: 003_add_user_is_admin
Create Date: 2024-12-31

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_anonymous_call_fields'
down_revision = '003_add_user_is_admin'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add anonymous session tracking fields
    op.add_column('video_calls', sa.Column('anonymous_session_id', sa.String(64), nullable=True))
    op.add_column('video_calls', sa.Column('anonymous_device_fingerprint', sa.String(256), nullable=True))

    # Add post-call lead capture fields
    op.add_column('video_calls', sa.Column('captured_name', sa.String(100), nullable=True))
    op.add_column('video_calls', sa.Column('captured_email', sa.String(255), nullable=True))
    op.add_column('video_calls', sa.Column('captured_phone', sa.String(20), nullable=True))
    op.add_column('video_calls', sa.Column('lead_captured_at', sa.DateTime(), nullable=True))

    # Create index for anonymous session lookups
    op.create_index('ix_video_calls_anonymous_session_id', 'video_calls', ['anonymous_session_id'])


def downgrade() -> None:
    op.drop_index('ix_video_calls_anonymous_session_id', table_name='video_calls')
    op.drop_column('video_calls', 'lead_captured_at')
    op.drop_column('video_calls', 'captured_phone')
    op.drop_column('video_calls', 'captured_email')
    op.drop_column('video_calls', 'captured_name')
    op.drop_column('video_calls', 'anonymous_device_fingerprint')
    op.drop_column('video_calls', 'anonymous_session_id')

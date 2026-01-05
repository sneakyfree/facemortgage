"""Add anonymous call support fields to video_calls table.

Revision ID: 004
Revises: 003
Create Date: 2024-12-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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

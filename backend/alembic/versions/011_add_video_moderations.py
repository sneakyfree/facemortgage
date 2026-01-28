"""Add video_moderations table

Revision ID: 011
Revises: 010
Create Date: 2025-01-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create moderation_status enum
    moderation_status = postgresql.ENUM(
        'pending', 'approved', 'rejected',
        name='moderationstatus',
        create_type=False
    )
    moderation_status.create(op.get_bind(), checkfirst=True)

    # Create video_moderations table
    op.create_table(
        'video_moderations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('professional_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('professional_profiles.id', ondelete='CASCADE'), 
                  nullable=False),
        sa.Column('video_url', sa.String(500), nullable=False),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', name='moderationstatus'), 
                  nullable=False, server_default='pending'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('users.id'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('rejection_reason', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Create indexes for efficient queries
    op.create_index('ix_video_moderations_status', 'video_moderations', ['status'])
    op.create_index('ix_video_moderations_professional_id', 'video_moderations', ['professional_id'])
    op.create_index('ix_video_moderations_reviewed_at', 'video_moderations', ['reviewed_at'])


def downgrade() -> None:
    op.drop_index('ix_video_moderations_reviewed_at')
    op.drop_index('ix_video_moderations_professional_id')
    op.drop_index('ix_video_moderations_status')
    op.drop_table('video_moderations')
    
    # Drop enum
    op.execute('DROP TYPE IF EXISTS moderationstatus')

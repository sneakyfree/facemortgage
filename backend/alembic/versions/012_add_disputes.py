"""Add disputes and dispute_messages tables

Revision ID: 012
Revises: 011
Create Date: 2025-01-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '012'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create dispute_type enum
    dispute_type = postgresql.ENUM(
        'billing', 'service', 'technical', 'other',
        name='disputetype',
        create_type=False
    )
    dispute_type.create(op.get_bind(), checkfirst=True)

    # Create dispute_status enum
    dispute_status = postgresql.ENUM(
        'open', 'in_progress', 'resolved', 'closed',
        name='disputestatus',
        create_type=False
    )
    dispute_status.create(op.get_bind(), checkfirst=True)

    # Create dispute_priority enum
    dispute_priority = postgresql.ENUM(
        'low', 'medium', 'high', 'urgent',
        name='disputepriority',
        create_type=False
    )
    dispute_priority.create(op.get_bind(), checkfirst=True)

    # Create disputes table
    op.create_table(
        'disputes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dispute_type', sa.Enum('billing', 'service', 'technical', 'other', name='disputetype'),
                  nullable=False),
        sa.Column('subject', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('open', 'in_progress', 'resolved', 'closed', name='disputestatus'),
                  nullable=False, server_default='open'),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'urgent', name='disputepriority'),
                  nullable=False, server_default='medium'),
        sa.Column('related_transaction_id', sa.String(100), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_disputes_user_id', 'disputes', ['user_id'])
    op.create_index('ix_disputes_status', 'disputes', ['status'])
    op.create_index('ix_disputes_assigned_to', 'disputes', ['assigned_to'])

    # Create dispute_messages table
    op.create_table(
        'dispute_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('dispute_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('disputes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id'), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_internal', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_dispute_messages_dispute_id', 'dispute_messages', ['dispute_id'])


def downgrade() -> None:
    op.drop_index('ix_dispute_messages_dispute_id')
    op.drop_table('dispute_messages')

    op.drop_index('ix_disputes_assigned_to')
    op.drop_index('ix_disputes_status')
    op.drop_index('ix_disputes_user_id')
    op.drop_table('disputes')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS disputepriority')
    op.execute('DROP TYPE IF EXISTS disputestatus')
    op.execute('DROP TYPE IF EXISTS disputetype')

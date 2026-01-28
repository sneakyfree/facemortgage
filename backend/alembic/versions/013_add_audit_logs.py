"""Add audit_logs table

Revision ID: 013
Revises: 012
Create Date: 2025-01-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '013'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create audit event type enum
    audit_event_type = postgresql.ENUM(
        'login', 'login_failed', 'logout', 'password_change',
        'account_created', 'account_disabled', 'account_enabled', 'profile_updated',
        'admin_user_status_change', 'admin_video_approved', 'admin_video_rejected', 'admin_dispute_resolved',
        'subscription_created', 'subscription_cancelled',
        'api_key_created', 'data_export',
        name='auditeventtype',
        create_type=False
    )
    audit_event_type.create(op.get_bind(), checkfirst=True)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_type', sa.Enum(
            'login', 'login_failed', 'logout', 'password_change',
            'account_created', 'account_disabled', 'account_enabled', 'profile_updated',
            'admin_user_status_change', 'admin_video_approved', 'admin_video_rejected', 'admin_dispute_resolved',
            'subscription_created', 'subscription_cancelled',
            'api_key_created', 'data_export',
            name='auditeventtype'),
            nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('extra_data', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_event_type', 'audit_logs', ['event_type'])
    op.create_index('ix_audit_logs_resource_id', 'audit_logs', ['resource_id'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_audit_logs_created_at')
    op.drop_index('ix_audit_logs_resource_id')
    op.drop_index('ix_audit_logs_event_type')
    op.drop_index('ix_audit_logs_user_id')
    op.drop_table('audit_logs')
    op.execute('DROP TYPE IF EXISTS auditeventtype')

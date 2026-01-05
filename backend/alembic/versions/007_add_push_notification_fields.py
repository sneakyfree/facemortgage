"""Add push notification fields to users table

Revision ID: 007
Revises: 006
Create Date: 2024-12-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add push notification fields to users table
    op.add_column('users', sa.Column('device_tokens', postgresql.JSONB(), nullable=True))
    op.add_column('users', sa.Column('push_enabled', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('users', sa.Column('last_platform', sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_platform')
    op.drop_column('users', 'push_enabled')
    op.drop_column('users', 'device_tokens')

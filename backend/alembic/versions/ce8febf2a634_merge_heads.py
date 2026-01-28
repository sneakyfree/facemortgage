"""merge_heads

Revision ID: ce8febf2a634
Revises: 000_sqlite, 015
Create Date: 2026-01-12 08:34:06.113406

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce8febf2a634'
down_revision: Union[str, None] = ('000_sqlite', '015')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

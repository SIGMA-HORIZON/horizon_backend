"""Add AccountRequest model

Revision ID: 8f6fd2130a92
Revises: e2292f460e52
Create Date: 2026-03-29 13:03:46.619962

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f6fd2130a92'
down_revision: Union[str, Sequence[str], None] = 'e2292f460e52'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: account_requests table is now included in the initial migration."""
    pass


def downgrade() -> None:
    """No-op."""
    pass

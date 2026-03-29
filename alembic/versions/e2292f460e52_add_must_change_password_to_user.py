"""Add must_change_password to User

Revision ID: e2292f460e52
Revises: efedde8c87b2
Create Date: 2026-03-29 12:24:53.716897

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2292f460e52'
down_revision: Union[str, Sequence[str], None] = 'efedde8c87b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op: must_change_password is now included in the initial migration."""
    pass


def downgrade() -> None:
    """No-op."""
    pass

"""merge heads

Revision ID: 780646f748fd
Revises: 5660b73c0da4, remove_prize_money_column
Create Date: 2025-11-06 01:08:58.679059

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '780646f748fd'
down_revision: Union[str, Sequence[str], None] = ('5660b73c0da4', 'remove_prize_money_column')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

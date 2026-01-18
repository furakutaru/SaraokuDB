"""merge prize flag heads

Revision ID: 5ab57ad54119
Revises: 3a6884b4747e, add_prize_management_fields
Create Date: 2026-01-14 13:21:19.206355

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ab57ad54119'
down_revision: Union[str, Sequence[str], None] = ('3a6884b4747e', 'add_prize_management_fields')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

"""merge prize fields heads

Revision ID: 87c6d26e4bf2
Revises: 2c9d01287823, remove_owner_id_and_primary_image
Create Date: 2026-01-10 09:10:34.621225

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87c6d26e4bf2'
down_revision: Union[str, Sequence[str], None] = ('2c9d01287823', 'remove_owner_id_and_primary_image')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

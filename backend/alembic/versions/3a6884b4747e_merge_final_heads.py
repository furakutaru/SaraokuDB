"""merge final heads

Revision ID: 3a6884b4747e
Revises: 2e090c6f3495, 87c6d26e4bf2
Create Date: 2026-01-10 16:34:42.940492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a6884b4747e'
down_revision: Union[str, Sequence[str], None] = ('2e090c6f3495', '87c6d26e4bf2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

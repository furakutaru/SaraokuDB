"""Add rakuten_url column to horses table

Revision ID: 4a5b3daef67a
Revises: 24058f3025d8
Create Date: 2025-10-10 21:19:31.198608

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a5b3daef67a'
down_revision: Union[str, Sequence[str], None] = '24058f3025d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('horses', sa.Column('rakuten_url', sa.String(length=500), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('horses', 'rakuten_url')

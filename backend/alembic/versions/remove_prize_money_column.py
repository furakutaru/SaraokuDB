"""remove_prize_money_column

Revision ID: remove_prize_money_column
Revises: 1daa8369af8b
Create Date: 2025-11-05 23:11:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'remove_prize_money_column'
down_revision: Union[str, Sequence[str], None] = '1daa8369af8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Drop the prize_money column from horses table
    op.drop_column('horses', 'prize_money')


def downgrade() -> None:
    """Downgrade database schema."""
    # Re-add the prize_money column
    op.add_column(
        'horses',
        sa.Column('prize_money', sa.Float(), nullable=True)
    )

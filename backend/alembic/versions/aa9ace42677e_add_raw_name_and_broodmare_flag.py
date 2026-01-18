"""add raw name and broodmare flag

Revision ID: aa9ace42677e
Revises: 5ab57ad54119
Create Date: 2026-01-14 14:22:23.450900

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa9ace42677e'
down_revision: Union[str, Sequence[str], None] = '5ab57ad54119'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add raw_name and is_broodmare columns to horses table."""
    with op.batch_alter_table('horses', schema='public') as batch_op:
        batch_op.add_column(sa.Column('raw_name', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('is_broodmare', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    # remove temporary default to align with SQLAlchemy model behaviour
    with op.batch_alter_table('horses', schema='public') as batch_op:
        batch_op.alter_column('is_broodmare', server_default=None)


def downgrade() -> None:
    """Remove raw_name and is_broodmare columns."""
    with op.batch_alter_table('horses', schema='public') as batch_op:
        batch_op.drop_column('is_broodmare')
        batch_op.drop_column('raw_name')

"""remove_rakuten_url_column

Revision ID: ebe1f80d52d5
Revises: 4a5b3daef67a
Create Date: 2025-10-14 18:24:53.445729

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ebe1f80d52d5'
down_revision: Union[str, Sequence[str], None] = '4a5b3daef67a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # rakuten_url カラムを削除
    op.drop_column('horses', 'rakuten_url')


def downgrade() -> None:
    """Downgrade schema."""
    # ダウングレード時に rakuten_url カラムを再作成
    op.add_column('horses',
        sa.Column('rakuten_url', sa.String(length=500), nullable=True)
    )

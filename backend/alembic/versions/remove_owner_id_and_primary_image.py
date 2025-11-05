"""Remove owner_id and primary_image columns

Revision ID: remove_owner_id_and_primary_image
Revises: convert_unified_race_records
Create Date: 2025-11-06 01:31:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'remove_owner_id_and_primary_image'
down_revision: Union[str, Sequence[str], None] = 'convert_unified_race_records'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 外部キー制約を削除
    op.drop_constraint('fk_horses_owner_id_users', 'horses', type_='foreignkey')
    
    # カラムを削除
    op.drop_column('horses', 'primary_image')
    op.drop_column('horses', 'owner_id')


def downgrade() -> None:
    """Downgrade schema."""
    # カラムを再作成
    op.add_column('horses', 
                 sa.Column('owner_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('horses', 
                 sa.Column('primary_image', sa.VARCHAR(length=500), autoincrement=False, nullable=True))
    
    # 外部キー制約を再作成
    op.create_foreign_key(
        'fk_horses_owner_id_users', 
        'horses', 'users', 
        ['owner_id'], ['id']
    )

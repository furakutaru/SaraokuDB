"""update_unified_race_records_type

Revision ID: 5660b73c0da4
Revises: 9b11adadae81
Create Date: 2025-11-04 23:28:47.032903

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5660b73c0da4'
down_revision: Union[str, Sequence[str], None] = '9b11adadae81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 既存のunified_race_recordsカラムを削除
    op.drop_column('horses', 'unified_race_records')
    
    # 新しいboolean型のunified_race_recordsカラムを追加
    op.add_column('horses', 
        sa.Column('unified_race_records', 
                 sa.Boolean(), 
                 server_default='false', 
                 nullable=True)
    )
    
    # race_recordに基づいてunified_race_recordsを更新
    conn = op.get_bind()
    conn.execute("""
        UPDATE horses 
        SET unified_race_records = (
            CASE 
                WHEN race_record IS NULL THEN true
                WHEN race_record::json->>'total_races' IS NULL THEN true
                WHEN (race_record::json->>'total_races')::int = 0 THEN true
                ELSE false 
            END
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # ダウングレード時は元のjson型に戻す
    op.drop_column('horses', 'unified_race_records')
    op.add_column('horses', 
        sa.Column('unified_race_records', 
                 sa.JSON(), 
                 nullable=True)
    )

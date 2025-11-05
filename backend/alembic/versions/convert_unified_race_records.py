"""Convert unified_race_records from boolean to JSON

Revision ID: convert_unified_race_records
Revises: 780646f748fd
Create Date: 2025-11-06 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'convert_unified_race_records'
down_revision: Union[str, Sequence[str], None] = '780646f748fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. まず、新しい一時カラムを作成
    op.add_column('horses', 
                 sa.Column('unified_race_records_temp', 
                          postgresql.JSON(astext_type=sa.Text()),
                          comment='統合されたレース記録（JSON形式）',
                          server_default='[]'))
    
    # 2. 既存のboolean値を新しいJSON形式に変換してコピー
    op.execute("""
    UPDATE horses 
    SET unified_race_records_temp = 
        CASE 
            WHEN unified_race_records = true THEN '{}'::jsonb
            ELSE '[]'::jsonb
        END
    """)
    
    # 3. 元のカラムを削除
    op.drop_column('horses', 'unified_race_records')
    
    # 4. 一時カラムを元の名前にリネーム
    op.alter_column('horses', 'unified_race_records_temp', 
                   new_column_name='unified_race_records')


def downgrade() -> None:
    """Downgrade schema."""
    # 1. 新しい一時カラムを作成（boolean型）
    op.add_column('horses',
                 sa.Column('unified_race_records_temp', 
                          sa.BOOLEAN(),
                          server_default=sa.text('false')))
    
    # 2. JSONデータをbooleanに変換してコピー
    op.execute("""
    UPDATE horses 
    SET unified_race_records_temp = 
        CASE 
            WHEN unified_race_records::text = '{}' THEN true
            ELSE false
        END
    """)
    
    # 3. 元のカラムを削除
    op.drop_column('horses', 'unified_race_records')
    
    # 4. 一時カラムを元の名前にリネーム
    op.alter_column('horses', 'unified_race_records_temp', 
                   new_column_name='unified_race_records')

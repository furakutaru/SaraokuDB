"""add_indexes_to_auction_histories

Revision ID: xxxxxxxxxxxx
Revises: b200c4436242
Create Date: 2025-10-25 20:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251025_add_indexes_to_auction_histories'
down_revision = 'c5ab31fc062d'
branch_labels = None
depends_on = None

def upgrade():
    # インデックスが存在するか確認してから作成
    connection = op.get_bind()
    # idx_auction_histories_horse_id が存在しない場合のみ作成
    result = connection.execute(
        sa.text("""
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'auction_histories' 
        AND indexname = 'idx_auction_histories_horse_id'
        """)
    ).scalar()
    if not result:
        op.create_index('idx_auction_histories_horse_id', 'auction_histories', ['horse_id'])
    
    # idx_auction_histories_auction_date が存在しない場合のみ作成
    result = connection.execute(sa.text("""
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'auction_histories' 
        AND indexname = 'idx_auction_histories_auction_date'
        """)
    ).scalar()
    if not result:
        op.create_index('idx_auction_histories_auction_date', 'auction_histories', [sa.text('auction_date DESC')])
    
    # idx_auction_histories_horse_id_auction_date が存在しない場合のみ作成
    result = connection.execute(
        sa.text("""
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'auction_histories' 
        AND indexname = 'idx_auction_histories_horse_id_auction_date'
        """)
    ).scalar()
    if not result:
        op.create_index('idx_auction_histories_horse_id_auction_date', 'auction_histories', 
                      ['horse_id', sa.text('auction_date DESC')])

def downgrade():
    # インデックスを削除
    op.drop_index('idx_auction_histories_horse_id_auction_date', 'auction_histories')
    op.drop_index('idx_auction_histories_auction_date', 'auction_histories')
    op.drop_index('idx_auction_histories_horse_id', 'auction_histories')

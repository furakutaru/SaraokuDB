"""add_latest_auction_id

Revision ID: 20251026_add_latest_auction_id
Revises: ae19117b1ba7
Create Date: 2025-10-26 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251026_add_latest_auction_id'
down_revision = 'ae19117b1ba7'
branch_labels = None
depends_on = None

def upgrade():
    # horsesテーブルにlatest_auction_idカラムを追加
    op.add_column('horses', sa.Column('latest_auction_id', sa.Integer(), nullable=True))
    
    # 外部キー制約を追加
    op.create_foreign_key(
        'fk_horses_latest_auction_id',
        'horses', 'auction_histories',
        ['latest_auction_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # 既存データのlatest_auction_idを更新するためのSQLを実行
    op.execute("""
        UPDATE horses h
        SET latest_auction_id = latest_ah.id
        FROM (
            SELECT DISTINCT ON (horse_id) id, horse_id
            FROM auction_histories
            ORDER BY horse_id, auction_date DESC
        ) latest_ah
        WHERE h.id = latest_ah.horse_id
    """)

def downgrade():
    # 外部キー制約を削除
    op.drop_constraint('fk_horses_latest_auction_id', 'horses', type_='foreignkey')
    
    # latest_auction_idカラムを削除
    op.drop_column('horses', 'latest_auction_id')

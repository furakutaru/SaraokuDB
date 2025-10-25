"""add_indexes_to_auction_histories

Revision ID: xxxxxxxxxxxx
Revises: b200c4436242
Create Date: 2025-10-25 20:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'xxxxxxxxxxxx'
down_revision = 'b200c4436242'
branch_labels = None
depends_on = None

def upgrade():
    # インデックスを追加
    op.create_index('idx_auction_histories_horse_id', 'auction_histories', ['horse_id'])
    op.create_index('idx_auction_histories_auction_date', 'auction_histories', [sa.text('auction_date DESC')])
    op.create_index('idx_auction_histories_horse_id_auction_date', 'auction_histories', 
                   ['horse_id', sa.text('auction_date DESC')])

def downgrade():
    # インデックスを削除
    op.drop_index('idx_auction_histories_horse_id_auction_date', 'auction_histories')
    op.drop_index('idx_auction_histories_auction_date', 'auction_histories')
    op.drop_index('idx_auction_histories_horse_id', 'auction_histories')

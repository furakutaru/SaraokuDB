"""migrate_damsire_to_dam_sire

Revision ID: xxxxx
Revises: yyyyy
Create Date: 2025-11-03 19:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '64136c311485442292a215a1a8f15839'
down_revision = '4ce4de32b4c3'
branch_labels = None
depends_on = None

def upgrade():
    # damsire のデータを dam_sire にコピー（dam_sire が空の場合のみ）
    op.execute("""
        UPDATE horses 
        SET dam_sire = damsire 
        WHERE (dam_sire IS NULL OR dam_sire = '') 
        AND damsire IS NOT NULL
    """)

def downgrade():
    # ロールバック用に dam_sire のデータを damsire にコピー
    op.execute("""
        UPDATE horses 
        SET damsire = dam_sire 
        WHERE (damsire IS NULL OR damsire = '') 
        AND dam_sire IS NOT NULL
    """)

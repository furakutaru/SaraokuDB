"""Remove rakuten_url column from horses table"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_rakuten_url'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Remove the rakuten_url column
    with op.batch_alter_table('horses', schema=None) as batch_op:
        batch_op.drop_column('rakuten_url')

def downgrade():
    # Add the rakuten_url column back (if needed for rollback)
    with op.batch_alter_table('horses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('rakuten_url', sa.String(length=500), nullable=True))

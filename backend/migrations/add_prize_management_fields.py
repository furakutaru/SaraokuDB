"""Add prize management fields to horses table"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_prize_management_fields'
down_revision = 'remove_rakuten_url'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('horses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('current_prize', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('last_prize_update', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('next_update_due_date', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('update_interval_months', sa.Integer(), nullable=False, server_default=sa.text('3')))
        batch_op.add_column(sa.Column('is_retired', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    # Remove server defaults to match SQLAlchemy model behaviour
    with op.batch_alter_table('horses', schema=None) as batch_op:
        batch_op.alter_column('update_interval_months', server_default=None)
        batch_op.alter_column('is_retired', server_default=None)


def downgrade():
    with op.batch_alter_table('horses', schema=None) as batch_op:
        batch_op.drop_column('is_retired')
        batch_op.drop_column('update_interval_months')
        batch_op.drop_column('next_update_due_date')
        batch_op.drop_column('last_prize_update')
        batch_op.drop_column('current_prize')

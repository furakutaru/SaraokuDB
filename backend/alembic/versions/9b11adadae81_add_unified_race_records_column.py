"""add_unified_race_records_column

Revision ID: 9b11adadae81
Revises: a4f748710c6c
Create Date: 2025-11-04 23:28:12.268414

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b11adadae81'
down_revision: Union[str, Sequence[str], None] = 'a4f748710c6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add unified_race_records column as BOOLEAN with default False
    op.add_column('horses', sa.Column('unified_race_records', sa.Boolean(), server_default='false', nullable=True))
    
    # If there's a race_record column, update unified_race_records based on its value
    conn = op.get_bind()
    conn.execute("""
        UPDATE horses 
        SET unified_race_records = (
            CASE 
                WHEN race_record->>'total_races' IS NULL THEN true
                WHEN (race_record->>'total_races')::int = 0 THEN true
                ELSE false 
            END
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('horses', 'unified_race_records')

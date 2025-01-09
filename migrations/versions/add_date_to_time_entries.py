"""add date to time entries

Revision ID: add_date_to_time_entries
Revises: add_timestamps_to_time_entries
Create Date: 2025-01-09 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_date_to_time_entries'
down_revision: Union[str, None] = 'add_timestamps_to_time_entries'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add date column
    op.add_column('time_entries',
        sa.Column('date', sa.Date(), nullable=True)
    )
    
    # Update existing records to use the first day of their month
    # This is a temporary solution for existing records
    op.execute("""
        UPDATE time_entries 
        SET date = DATE_TRUNC('month', CAST(month || ' 1, 2025' as DATE))
        WHERE date IS NULL
    """)
    
    # Make the column not nullable after setting default values
    op.alter_column('time_entries', 'date',
        existing_type=sa.Date(),
        nullable=False
    )

def downgrade() -> None:
    op.drop_column('time_entries', 'date')

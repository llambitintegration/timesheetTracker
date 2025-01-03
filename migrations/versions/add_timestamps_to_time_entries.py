"""add timestamps to time entries

Revision ID: add_timestamps_to_time_entries
Revises: 9eac8145ca59
Create Date: 2025-01-03 20:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_timestamps_to_time_entries'
down_revision: Union[str, None] = '9eac8145ca59'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add created_at column with server default
    op.add_column('time_entries',
        sa.Column('created_at', sa.DateTime(timezone=True),
                 server_default=sa.text('now()'),
                 nullable=True)
    )
    
    # Add updated_at column
    op.add_column('time_entries',
        sa.Column('updated_at', sa.DateTime(timezone=True),
                 onupdate=sa.text('now()'),
                 nullable=True)
    )

def downgrade() -> None:
    op.drop_column('time_entries', 'updated_at')
    op.drop_column('time_entries', 'created_at')

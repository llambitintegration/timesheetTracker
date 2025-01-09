"""add date to time entries

Revision ID: add_date_to_time_entries
Revises: add_timestamps_to_time_entries
Create Date: 2025-01-09 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from utils.logger import Logger

logger = Logger().get_logger()

# revision identifiers, used by Alembic.
revision: str = 'add_date_to_time_entries'
down_revision: Union[str, None] = 'add_timestamps_to_time_entries'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add date column to time_entries table"""
    logger.info("Starting migration to add date column to time_entries")
    try:
        # Add date column if it doesn't exist
        logger.info("Adding date column to time_entries table")
        op.add_column('time_entries',
            sa.Column('date', sa.Date(), nullable=True)
        )

        # Update existing records to use the first day of their month
        # This is a temporary solution for existing records
        logger.info("Updating existing records with date values")
        op.execute("""
            UPDATE time_entries 
            SET date = DATE_TRUNC('month', CAST(month || ' 1, 2025' as DATE))
            WHERE date IS NULL
        """)

        # Make the column not nullable after setting default values
        logger.info("Making date column not nullable")
        op.alter_column('time_entries', 'date',
            existing_type=sa.Date(),
            nullable=False
        )

        logger.info("Successfully completed date column migration")
    except Exception as e:
        logger.error(f"Error during date column migration: {str(e)}")
        logger.exception("Migration error details:")
        raise

def downgrade() -> None:
    """Remove date column from time_entries table"""
    logger.info("Starting migration rollback for date column")
    try:
        logger.info("Dropping date column from time_entries table")
        op.drop_column('time_entries', 'date')
        logger.info("Successfully completed date column rollback")
    except Exception as e:
        logger.error(f"Error during date column rollback: {str(e)}")
        logger.exception("Rollback error details:")
        raise
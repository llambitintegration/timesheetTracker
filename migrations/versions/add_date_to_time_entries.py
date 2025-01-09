"""add date to time entries - Deprecated, merged into base migration

This migration is deprecated as the date column is now part of the initial table creation.
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
    """This migration is deprecated as date column is now part of initial table creation"""
    pass

def downgrade() -> None:
    """No downgrade needed as this migration is deprecated"""
    pass
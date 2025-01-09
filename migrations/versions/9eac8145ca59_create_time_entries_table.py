"""create_time_entries_table

Revision ID: 9eac8145ca59
Revises: 
Create Date: 2025-01-03 16:57:56.627458
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from utils.logger import Logger

logger = Logger().get_logger()

# revision identifiers, used by Alembic.
revision: str = '9eac8145ca59'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    try:
        # Create customers table first
        logger.info("Starting to create customers table")
        op.create_table('customers',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('contact_email', sa.String(), nullable=False),
            sa.Column('industry', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=False),
            sa.Column('address', sa.String(), nullable=True),
            sa.Column('phone', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
        logger.info("Successfully created customers table")

        # Create project_managers table
        logger.info("Starting to create project_managers table")
        op.create_table('project_managers',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name'),
            sa.UniqueConstraint('email')
        )
        logger.info("Successfully created project_managers table")

        # Create projects table
        logger.info("Starting to create projects table")
        op.create_table('projects',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('project_id', sa.String(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('location', sa.String(), nullable=False),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('customer', sa.String(), nullable=False),
            sa.Column('project_manager', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('project_id'),
            sa.ForeignKeyConstraint(['customer'], ['customers.name'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['project_manager'], ['project_managers.name'], ondelete='CASCADE')
        )
        logger.info("Successfully created projects table")

        # Create time_entries table
        logger.info("Starting to create time_entries table")
        op.create_table('time_entries',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('date', sa.Date(), nullable=False),  # Explicit date field for timesheet entries
            sa.Column('week_number', sa.Integer(), nullable=False),
            sa.Column('month', sa.String(), nullable=False),
            sa.Column('category', sa.String(), nullable=False),
            sa.Column('subcategory', sa.String(), nullable=False),
            sa.Column('customer', sa.String(), nullable=True),
            sa.Column('project', sa.String(), nullable=True),
            sa.Column('task_description', sa.String(), nullable=True),
            sa.Column('hours', sa.Float(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['customer'], ['customers.name'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['project'], ['projects.project_id'], ondelete='SET NULL')
        )
        logger.info("Successfully created time_entries table")

    except Exception as e:
        logger.error(f"Error during upgrade: {str(e)}")
        logger.exception("Upgrade error details:")
        raise

def downgrade() -> None:
    logger.info("Starting database downgrade")
    try:
        # Drop tables in reverse order of creation
        logger.info("Dropping time_entries table")
        op.drop_table('time_entries')
        logger.info("Dropping projects table")
        op.drop_table('projects')
        logger.info("Dropping project_managers table")
        op.drop_table('project_managers')
        logger.info("Dropping customers table")
        op.drop_table('customers')
        logger.info("Successfully completed database downgrade")
    except Exception as e:
        logger.error(f"Error during downgrade: {str(e)}")
        logger.exception("Downgrade error details:")
        raise
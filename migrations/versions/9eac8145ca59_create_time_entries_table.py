"""create_time_entries_table

Revision ID: 9eac8145ca59
Revises: 
Create Date: 2025-01-03 16:57:56.627458

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9eac8145ca59'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from utils.logger import Logger
    logger = Logger().get_logger()
    
    # Create customers table first
    logger.debug("Creating customers table")
    op.create_table('customers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('contact_email', sa.String(), nullable=False),
        sa.Column('industry', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    logger.debug("Creating project_managers table")
    op.create_table('project_managers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('email')
    )

    logger.debug("Creating projects table")
    op.create_table('projects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('location', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('customer', sa.String(), nullable=False),
        sa.Column('project_manager', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id'),
        sa.ForeignKeyConstraint(['customer'], ['customers.name'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_manager'], ['project_managers.name'], ondelete='CASCADE')
    )

    logger.debug("Creating time_entries table")
    op.create_table('time_entries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('now()'), nullable=True),
        sa.Column('week_number', sa.Integer(), nullable=False),
        sa.Column('month', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('subcategory', sa.String(), nullable=False),
        sa.Column('customer', sa.String(), nullable=True),
        sa.Column('project', sa.String(), nullable=True),
        sa.Column('task_description', sa.String(), nullable=True),
        sa.Column('hours', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer'], ['customers.name'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project'], ['projects.project_id'], ondelete='SET NULL')
    )


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('time_entries')
    op.drop_table('projects')
    op.drop_table('project_managers')
    op.drop_table('customers')
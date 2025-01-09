"""base migration

Revision ID: base_migration_001
Revises: 
Create Date: 2025-01-09 20:15:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from utils.logger import Logger

logger = Logger().get_logger()

# revision identifiers, used by Alembic.
revision: str = 'base_migration_001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Create all tables in a single migration"""
    try:
        connection = op.get_bind()

        # Create customers table first
        logger.info("Creating customers table")
        op.create_table('customers',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('contact_email', sa.String(), nullable=True),
            sa.Column('industry', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=True),
            sa.Column('address', sa.String(), nullable=True),
            sa.Column('phone', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
        connection.execute(sa.text('COMMIT'))

        # Insert default and common customers first
        logger.info("Creating default and common customers")
        connection.execute(sa.text("""
            INSERT INTO customers (name, contact_email, status) VALUES
            ('Unassigned', 'unassigned@company.com', 'active'),
            ('ECOLAB', 'contact@ecolab.com', 'active'),
            ('Hiland Dairy', 'contact@hilanddairy.com', 'active'),
            ('Dr Pepper Snapple', 'contact@drpepper.com', 'active'),
            ('Country Pure', 'contact@countrypure.com', 'active')
            ON CONFLICT (name) DO NOTHING
        """))
        connection.execute(sa.text('COMMIT'))

        # Create project_managers table
        logger.info("Creating project_managers table")
        op.create_table('project_managers',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('email', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
        connection.execute(sa.text('COMMIT'))

        # Create projects table with proper foreign keys
        logger.info("Creating projects table")
        op.create_table('projects',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('project_id', sa.String(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('customer', sa.String(), nullable=True),
            sa.Column('project_manager', sa.String(), nullable=True),
            sa.Column('status', sa.String(), server_default='active'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('project_id'),
            sa.ForeignKeyConstraint(['customer'], ['customers.name'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['project_manager'], ['project_managers.name'], ondelete='SET NULL'),
            sa.CheckConstraint("status IN ('active', 'inactive', 'pending', 'completed')", name='valid_status'),
            sa.CheckConstraint("project_id != '-'", name='valid_project_id')
        )

        # Insert default and common projects
        connection.execute(sa.text("""
            INSERT INTO projects (project_id, name, description, customer, status)
            VALUES 
            ('Unassigned', 'Unassigned', 'Default project for unassigned entries', 'Unassigned', 'active'),
            ('Project_Magic_Bullet', 'Project Magic Bullet', 'ECOLAB Project', 'ECOLAB', 'active'),
            ('iTrends', 'iTrends', 'ECOLAB iTrends Project', 'ECOLAB', 'active'),
            ('Wichita_KS', 'Wichita KS', 'Hiland Dairy Wichita Project', 'Hiland Dairy', 'active'),
            ('Aspers_PA', 'Aspers PA', 'Dr Pepper Snapple Project', 'Dr Pepper Snapple', 'active'),
            ('Ellington_CT', 'Ellington CT', 'Country Pure Project', 'Country Pure', 'active')
            ON CONFLICT (project_id) DO NOTHING
        """))
        connection.execute(sa.text('COMMIT'))

        # Create time_entries table with updated foreign keys
        logger.info("Creating time_entries table")
        op.create_table('time_entries',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('date', sa.Date(), nullable=False),
            sa.Column('week_number', sa.Integer(), nullable=False),
            sa.Column('month', sa.String(), nullable=False),
            sa.Column('category', sa.String(), nullable=False),
            sa.Column('subcategory', sa.String(), nullable=False),
            sa.Column('customer', sa.String(), nullable=True),
            sa.Column('project', sa.String(), nullable=True),
            sa.Column('task_description', sa.String(), nullable=True),
            sa.Column('hours', sa.Float(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['customer'], ['customers.name'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['project'], ['projects.project_id'], ondelete='SET NULL'),
            sa.CheckConstraint('hours > 0 AND hours <= 24', name='check_valid_hours')
        )
        connection.execute(sa.text('COMMIT'))

        

        logger.info("All tables created successfully")

    except Exception as e:
        logger.error(f"Error during upgrade: {str(e)}")
        logger.exception("Upgrade error details:")
        raise

def downgrade() -> None:
    """Drop all tables in reverse order"""
    try:
        logger.info("Starting database downgrade")
        connection = op.get_bind()

        logger.info("Dropping time_entries table")
        op.drop_table('time_entries')
        connection.execute(sa.text('COMMIT'))

        logger.info("Dropping projects table")
        op.drop_table('projects')
        connection.execute(sa.text('COMMIT'))

        logger.info("Dropping project_managers table")
        op.drop_table('project_managers')
        connection.execute(sa.text('COMMIT'))

        logger.info("Dropping customers table")
        op.drop_table('customers')
        connection.execute(sa.text('COMMIT'))

        logger.info("Database downgrade completed successfully")
    except Exception as e:
        logger.error(f"Error during downgrade: {str(e)}")
        logger.exception("Downgrade error details:")
        raise
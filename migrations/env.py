from logging.config import fileConfig
import os
from os import environ
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from dotenv import load_dotenv
import logging
from sqlalchemy import text

# Import all models to ensure they are part of the metadata
from models.baseModel import Base
from models.timeEntry import TimeEntry
from models.customerModel import Customer
from models.projectModel import Project
from models.projectManagerModel import ProjectManager

# Setup environment import
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# override sqlalchemy.url with DATABASE_URL environment variable
    # Fetch the DATABASE_URL directly from environment variables
database_url = os.environ.get('DATABASE_URL')
if database_url is None:
        raise ValueError("DATABASE_URL environment variable is not set")
config.set_main_option('sqlalchemy.url', database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Setup custom logger
from utils.logger import Logger
logger = Logger().get_logger()
logger.setLevel(logging.DEBUG)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    try:
        logger.info("Starting database migration process")
        logger.info(f"Using database URL: {database_url.split('@')[1]}")  # Log only host/db part

        # Verify metadata
        logger.info("Checking target metadata")
        if not target_metadata:
            logger.error("No target metadata found")
            raise Exception("No target metadata available for migrations")

        # Log table information
        logger.info(f"Found {len(target_metadata.tables)} tables in metadata")
        for table in target_metadata.tables.values():
            logger.info(f"Table in metadata: {table.name}")
            logger.debug(f"Columns in {table.name}:")
            for column in table.columns:
                logger.debug(f"  - {column.name} ({column.type})")

        # Setup database connection
        logger.info("Setting up database connection for migrations")
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            logger.info("Testing database connection")
            connection.execute(text("SELECT 1"))
            logger.info("Database connection successful")

            logger.info("Configuring Alembic context")
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                version_table='alembic_version',
                include_schemas=True,
                compare_type=True,
                compare_server_default=True
            )

            try:
                with context.begin_transaction():
                    logger.info("Beginning migration transaction")
                    logger.info("Running migrations with target metadata tables: " + 
                              ", ".join([t.name for t in target_metadata.tables.values()]))
                    context.run_migrations()
                    logger.info("Migrations completed successfully")
            except Exception as e:
                logger.error(f"Migration failed: {str(e)}")
                logger.error("Migration error details:", exc_info=True)
                raise
    except Exception as e:
        logger.error(f"Migration setup failed: {str(e)}")
        logger.error("Setup error details:", exc_info=True)
        raise

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
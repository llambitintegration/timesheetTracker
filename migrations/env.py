from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config
from sqlalchemy import pool, text
from alembic import context
from dotenv import load_dotenv
import logging

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

# Get database credentials from environment
PGHOST = os.environ.get('PGHOST')
PGDATABASE = os.environ.get('PGDATABASE')
PGUSER = os.environ.get('PGUSER')
PGPASSWORD = os.environ.get('PGPASSWORD')

# Validate all required environment variables are present
missing_vars = []
for var in ['PGHOST', 'PGDATABASE', 'PGUSER', 'PGPASSWORD']:
    if not os.environ.get(var):
        missing_vars.append(var)

if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Construct database URL
database_url = f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{PGHOST}/{PGDATABASE}"

# Override sqlalchemy.url with constructed database URL
config.set_main_option('sqlalchemy.url', database_url)

# Setup custom logger
from utils.logger import Logger
logger = Logger().get_logger()
logger.setLevel(logging.DEBUG)

# Add your model's MetaData object here for 'autogenerate' support
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
        # Configure SQLAlchemy for migrations
        configuration = config.get_section(config.config_ini_section)
        if not isinstance(configuration, dict):
            configuration = {}

        # Add SSL mode for Neon.tech
        if 'sqlalchemy.url' not in configuration:
            configuration['sqlalchemy.url'] = database_url
        configuration['sqlalchemy.connect_args'] = {'sslmode': 'require'}

        # Create our connectable
        connectable = engine_from_config(
            configuration,
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
                compare_server_default=True,
                transaction_per_migration=True,
                render_as_batch=True
            )

            try:
                with context.begin_transaction():
                    logger.info("Beginning migration transaction")
                    context.run_migrations()
                    logger.info("Migrations completed successfully")
            except Exception as e:
                logger.error(f"Migration failed: {str(e)}")
                logger.exception("Migration error details:")
                raise

    except Exception as e:
        logger.error(f"Migration setup failed: {str(e)}")
        logger.exception("Setup error details:")
        raise

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
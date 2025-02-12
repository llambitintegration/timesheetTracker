from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from utils.logger import Logger
from models.baseModel import Base
from sqlalchemy import inspect

# Load environment variables
load_dotenv()

logger = Logger().get_logger()

# Get database credentials from environment variables
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
    error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
    logger.error(error_msg)
    raise ValueError(error_msg)

# Construct DATABASE_URL from individual credentials
DATABASE_URL = f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{PGHOST}/{PGDATABASE}"

try:
    # Create engine with proper configuration and connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
            "sslmode": 'require'  # Required for Neon.tech
        }
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verify_database():
    """Verify database connection and schema"""
    logger.info("Verifying database connection and schema")
    try:
        with engine.connect() as conn:
            # Test basic connection
            conn.execute(text("SELECT 1"))
            logger.info(f"Database driver: {engine.driver}")
            logger.info(f"Database dialect: {engine.dialect.name}")
            logger.info("Successfully connected to database")

            # Use SQLAlchemy inspector for schema verification
            inspector = inspect(engine)
            all_tables = inspector.get_table_names()
            logger.info(f"Found {len(all_tables)} tables in database")

            # Get all expected tables from metadata
            expected_tables = {table.name for table in Base.metadata.sorted_tables}
            logger.info(f"Expected tables: {', '.join(expected_tables)}")

            # Check for missing tables
            missing_tables = expected_tables - set(all_tables)
            if missing_tables:
                logger.warning(f"Missing tables: {', '.join(missing_tables)}")
                return False

            # Log found tables and their structure
            for table_name in all_tables:
                if table_name in expected_tables:
                    columns = inspector.get_columns(table_name)
                    logger.debug(f"Table {table_name} exists with {len(columns)} columns")

            logger.info("Database verification completed successfully")
            return True
    except Exception as e:
        logger.error(f"Database verification failed: {str(e)}")
        logger.exception("Stack trace:")
        return False

def init_database():
    """Initialize database schema"""
    try:
        logger.info("Initializing database tables")
        # Import all models to ensure they're registered with metadata
        from models import Customer, ProjectManager, Project, TimeEntry

        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        if not existing_tables:
            # Create all tables only if none exist
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        else:
            logger.info("Tables already exist, skipping creation")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        logger.exception("Stack trace:")
        return False

def get_db():
    """Get database session"""
    db = SessionLocal()
    logger.debug("Database session created")
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        logger.exception("Database session error details:")
        raise
    finally:
        db.close()
        logger.debug("Database session closed")
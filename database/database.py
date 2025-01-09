from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from utils.logger import Logger
from models.baseModel import Base

# Load environment variables
load_dotenv()

logger = Logger().get_logger()

# Get database URL from Replit Secrets with proper error handling
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    logger.error("DATABASE_URL not found in environment")
    raise ValueError("DATABASE_URL environment variable is not set. Please add it to Replit Secrets.")

# Ensure proper PostgreSQL driver and log the connection attempt
logger.info(f"Attempting to connect to database at: {DATABASE_URL.split('@')[1]}")  # Log only host/db part
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://')

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verify_database():
    """Verify database connection and schema"""
    logger.info(f"Verifying database connection and schema: {DATABASE_URL}")
    try:
        with engine.connect() as conn:
            # Test basic connection
            conn.execute(text("SELECT 1"))
            logger.info(f"Database driver: {engine.driver}")
            logger.info(f"Database dialect: {engine.dialect.name}")
            logger.info("Successfully connected to database")

            # Get all tables from metadata
            tables = list(Base.metadata.sorted_tables)
            logger.info(f"Checking {len(tables)} tables in schema")

            existing_tables = []
            missing_tables = []

            for table in tables:
                logger.debug(f"Verifying table: {table.name}")
                if not engine.dialect.has_table(conn, table.name):
                    missing_tables.append(table.name)
                    logger.warning(f"Table {table.name} does not exist")
                else:
                    existing_tables.append(table.name)
                    logger.debug(f"Table {table.name} exists with columns: {[c.name for c in table.columns]}")

            if existing_tables:
                logger.info(f"Found tables: {', '.join(existing_tables)}")
            if missing_tables:
                logger.warning(f"Missing tables: {', '.join(missing_tables)}")
                return False

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

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
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
    finally:
        db.close()
        logger.debug("Database session closed")
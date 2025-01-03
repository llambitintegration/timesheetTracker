from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from utils.logger import Logger
from models.baseModel import Base

# Load environment variables
load_dotenv()

logger = Logger().get_logger()

# Get database URL from environment with proper error handling
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Use Neon connection pooler
DATABASE_URL = DATABASE_URL.replace('.azure.neon.tech', '-pooler.azure.neon.tech')

# Ensure proper PostgreSQL driver
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://')

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verify_database():
    """Verify database connection and schema"""
    logger.info(f"Verifying database connection and schema: {DATABASE_URL}")
    try:
        with engine.connect() as conn:
            logger.info("Successfully connected to database")
            for table in Base.metadata.sorted_tables:
                if not engine.dialect.has_table(conn, table.name):
                    logger.warning(f"Table {table.name} does not exist")
                    return False
            return True
    except Exception as e:
        logger.error(f"Database verification failed: {str(e)}")
        return False

def init_database():
    """Initialize database schema"""
    try:
        logger.info("Initializing database tables")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
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
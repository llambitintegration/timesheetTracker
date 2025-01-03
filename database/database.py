from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from utils.logger import Logger

logger = Logger().get_logger()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./timesheet.db')
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://')

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verify_database():
    try:
        # Try connecting to the database
        with engine.connect() as conn:
            # Check if tables exist
            for table in models.Base.metadata.tables:
                if not engine.dialect.has_table(conn, table):
                    logger.warning(f"Table {table} does not exist")
                    return False
        return True
    except Exception as e:
        logger.error(f"Database verification failed: {str(e)}")
        return False

# Initialize database connection
verify_database()

def get_db():
    db = SessionLocal()
    logger.debug("Database session created")
    try:
        yield db
    finally:
        db.close()
        logger.debug("Database session closed")
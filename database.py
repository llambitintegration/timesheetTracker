from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from logger import Logger

logger = Logger().get_logger()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./timesheet.db')
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://')

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    logger.debug("Database session created")
    try:
        yield db
    finally:
        db.close()
        logger.debug("Database session closed")
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
PGHOST = os.environ.get('NEON_HOST', os.environ.get('PGHOST'))
PGDATABASE = os.environ.get('NEON_DATABASE', os.environ.get('PGDATABASE'))
PGUSER = os.environ.get('NEON_USER', os.environ.get('PGUSER'))
PGPASSWORD = os.environ.get('NEON_PASSWORD', os.environ.get('PGPASSWORD'))

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
logger.debug(f"Connecting to database host: {PGHOST}")
logger.debug(f"Database name: {PGDATABASE}")
logger.debug(f"Database user: {PGUSER}")

try:
    logger.info("Creating database engine with connection settings")
    logger.debug(f"Connection parameters: pool_size=5, max_overflow=10, pool_timeout=30")
    
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
    
    # Test connection and log database details
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar()
        current_db = conn.execute(text("SELECT current_database()")).scalar()
        logger.info(f"Connected to database: {current_db}")
        logger.info(f"PostgreSQL version: {version}")
        
        # Log database permissions
        logger.debug("Checking database permissions")
        conn.execute(text("SELECT has_database_privilege(current_user, current_database(), 'CREATE')")).scalar()
        logger.info("Database engine created and tested successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    logger.exception("Database initialization error details:")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verify_database():
    """Verify database connection and schema"""
    logger.info("Verifying database connection and schema")
    try:
        with engine.connect() as conn:
            # Test basic connection and log connection details
            result = conn.execute(text("SELECT current_database(), current_user, inet_server_addr()::text, version()"))
            db_info = result.fetchone()
            logger.info(f"Connected to database: {db_info[0]}")
            logger.info(f"Database user: {db_info[1]}")
            logger.info(f"Server address: {db_info[2]}")
            logger.info(f"Database version: {db_info[3]}")
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
                    logger.info(f"Table {table_name} exists with {len(columns)} columns")
                    for column in columns:
                        logger.debug(f"Column in {table_name}: {column['name']} ({column['type']})")

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
        from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT
        from database.customer_repository import CustomerRepository
        from database.project_repository import ProjectRepository
        from database import schemas

        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        logger.info(f"Current tables in database: {', '.join(existing_tables)}")

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        # Create default customer and project if they don't exist
        with SessionLocal() as db:
            customer_repo = CustomerRepository()
            project_repo = ProjectRepository()

            # Create default customer
            if not customer_repo.get_by_name(db, DEFAULT_CUSTOMER):
                default_customer = schemas.CustomerCreate(
                    name=DEFAULT_CUSTOMER,
                    contact_email="unassigned@example.com",
                    status="active"
                )
                customer_repo.create(db, default_customer)
                logger.info(f"Created default customer: {DEFAULT_CUSTOMER}")

            # Create default project
            if not project_repo.get_by_project_id(db, DEFAULT_PROJECT):
                default_project = schemas.ProjectCreate(
                    project_id=DEFAULT_PROJECT,
                    name=DEFAULT_PROJECT,
                    customer=DEFAULT_CUSTOMER,
                    project_manager="-",
                    status="active"
                )
                project_repo.create(db, default_project)
                logger.info(f"Created default project: {DEFAULT_PROJECT}")

        # Verify tables were created
        new_tables = inspector.get_table_names()
        logger.info(f"Tables after initialization: {', '.join(new_tables)}")

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
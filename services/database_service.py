import os
from alembic import command
from alembic.config import Config
from sqlalchemy import text, inspect
from fastapi import HTTPException
from utils.logger import Logger
from database import engine

logger = Logger().get_logger()

class DatabaseService:
    def __init__(self, db_session):
        self.db = db_session

    async def initialize_database(self, force: bool = False):
        """Initialize database and run migrations"""
        logger.info("Starting database initialization process")
        try:
            await self._test_connection()

            if force:
                await self._drop_tables()

            await self._run_migrations()
            await self._verify_database()

            return {
                "status": "success",
                "message": "Database initialized and verified",
                "details": {
                    "tables_created": ['customers', 'project_managers', 'projects', 'time_entries']
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"Database initialization failed: {str(e)}"
            logger.error(error_msg)
            logger.exception("Initialization error stack trace:")
            raise HTTPException(status_code=500, detail=error_msg)

    async def _test_connection(self):
        """Test database connection"""
        logger.info("Testing database connection")
        try:
            # Execute a test query and fetch connection details
            result = self.db.execute(text("""
                SELECT current_database(), current_user, inet_server_addr()::text, 
                       inet_server_port()::text, version();
            """)).fetchone()

            logger.info("Database connection details:")
            logger.info(f"Database: {result[0]}")
            logger.info(f"User: {result[1]}")
            logger.info(f"Server: {result[2]}:{result[3]}")
            logger.info(f"Version: {result[4]}")

            logger.info("Database connection successful")
            return result
        except Exception as conn_error:
            logger.error(f"Database connection failed: {str(conn_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Database connection failed: {str(conn_error)}"
            )

    async def _drop_tables(self):
        """Drop existing tables"""
        logger.info("Force flag is true, dropping existing tables")
        try:
            with engine.connect() as connection:
                connection.execute(text("DROP TABLE IF EXISTS time_entries CASCADE"))
                connection.execute(text("DROP TABLE IF EXISTS projects CASCADE"))
                connection.execute(text("DROP TABLE IF EXISTS project_managers CASCADE"))
                connection.execute(text("DROP TABLE IF EXISTS customers CASCADE"))
                connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
                connection.commit()
            logger.info("Existing tables dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping tables: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error dropping tables: {str(e)}")

    async def _run_migrations(self):
        """Run database migrations"""
        logger.info("Loading Alembic configuration")
        alembic_cfg = Config("alembic.ini")

        # Construct database URL from PG environment variables
        PGHOST = os.environ.get('PGHOST')
        PGDATABASE = os.environ.get('PGDATABASE')
        PGUSER = os.environ.get('PGUSER')
        PGPASSWORD = os.environ.get('PGPASSWORD')

        database_url = f"postgresql+psycopg2://{PGUSER}:{PGPASSWORD}@{PGHOST}/{PGDATABASE}"
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)

        try:
            logger.info("Starting migration process")
            command.upgrade(alembic_cfg, "head")
            logger.info("Migration completed successfully")
        except Exception as migration_error:
            logger.error(f"Migration failed: {str(migration_error)}")
            logger.exception("Migration stack trace:")
            raise HTTPException(
                status_code=500,
                detail=f"Migration failed: {str(migration_error)}"
            )

    async def _verify_database(self):
        """Verify database state after migration"""
        logger.info("Verifying database state after migration")
        with engine.connect() as connection:
            inspector = inspect(engine)
            tables = ['customers', 'project_managers', 'projects', 'time_entries']
            missing_tables = []

            for table in tables:
                if not inspector.has_table(table):
                    missing_tables.append(table)
                    logger.warning(f"Table {table} not found")
                else:
                    logger.info(f"Table {table} exists")
                    if table == 'time_entries':
                        columns = [col['name'] for col in inspector.get_columns(table)]
                        logger.info(f"Columns in time_entries: {columns}")
                        if 'date' not in columns:
                            missing_tables.append('time_entries (missing date column)')

            if missing_tables:
                error_msg = f"Tables missing after migration: {', '.join(missing_tables)}"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
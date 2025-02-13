import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import os
from pathlib import Path
from models.baseModel import Base
from database.database import get_db
from main import app

# Import all models to ensure they're registered with SQLAlchemy
from models.timeEntry import TimeEntry
from models.customerModel import Customer
from models.projectModel import Project
from models.projectManagerModel import ProjectManager

# Use environment variables for test database
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    PGHOST = os.environ.get('PGHOST')
    PGDATABASE = os.environ.get('PGDATABASE')
    PGUSER = os.environ.get('PGUSER')
    PGPASSWORD = os.environ.get('PGPASSWORD')
    DATABASE_URL = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}/{PGDATABASE}"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "sslmode": "require",
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Clear tables before each test in correct order
    try:
        session.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        session.execute(text("TRUNCATE TABLE time_entries RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE TABLE projects RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE TABLE customers RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE TABLE project_managers RESTART IDENTITY CASCADE"))
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

    try:
        yield session
    finally:
        session.close()
        # Clean up tables after test
        session = Session()
        session.execute(text("SET CONSTRAINTS ALL DEFERRED"))
        session.execute(text("TRUNCATE TABLE time_entries RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE TABLE projects RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE TABLE customers RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE TABLE project_managers RESTART IDENTITY CASCADE"))
        session.commit()
        session.close()

@pytest.fixture(scope="function")
def test_client(test_db):
    """Create a test client using the test database"""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Session cleanup is handled by test_db fixture

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def db_session(test_db):
    """Alias for test_db for backward compatibility"""
    return test_db

@pytest.fixture(scope="function")
def setup_test_data(test_db):
    """Set up test data in the database with nullable relationships"""
    try:
        # Create test project managers
        project_manager = ProjectManager(
            name="Test Manager",
            email="test.manager@example.com"
        )
        test_db.add(project_manager)
        test_db.commit()

        # Create test customers
        customer = Customer(
            name="ECOLAB",
            contact_email="ecolab@example.com",
            status="active"
        )
        test_db.add(customer)
        test_db.commit()

        # Create test project with nullable relationships
        project = Project(
            project_id="Project_Magic_Bullet",
            name="Project Magic Bullet",
            customer="ECOLAB",  # Link to existing customer
            project_manager="Test Manager",  # Link to existing manager
            status="active"
        )
        test_db.add(project)
        test_db.commit()

        # Query and return the created data
        return {
            "customers": test_db.query(Customer).all(),
            "project_managers": test_db.query(ProjectManager).all(),
            "projects": test_db.query(Project).all()
        }
    except Exception as e:
        test_db.rollback()
        raise e
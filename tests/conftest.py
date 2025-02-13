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
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
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
def setup_test_data(test_db):
    """Set up test data in the database"""
    try:
        # Create test project managers first
        project_managers = [
            ProjectManager(name="Unassigned", email="unassigned@example.com"),
            ProjectManager(name="Test Manager", email="test.manager@example.com")
        ]
        for manager in project_managers:
            test_db.add(manager)
        test_db.commit()  # Commit project managers first

        # Create test customers
        customers = [
            Customer(name="Unassigned", contact_email="unassigned@example.com", status="active"),
            Customer(name="ECOLAB", contact_email="ecolab@example.com", status="active")
        ]
        for customer in customers:
            test_db.add(customer)
        test_db.commit()  # Commit customers before projects

        # Create test projects
        projects = [
            Project(
                project_id="Unassigned",
                name="Unassigned",
                customer="Unassigned",
                project_manager="Unassigned",
                status="active"
            ),
            Project(
                project_id="Project_Magic_Bullet",
                name="Project Magic Bullet",
                customer="ECOLAB",
                project_manager="Test Manager",
                status="active"
            )
        ]
        for project in projects:
            test_db.add(project)
        test_db.commit()

        return {
            "customers": customers,
            "project_managers": project_managers,
            "projects": projects
        }
    except Exception as e:
        test_db.rollback()
        raise e
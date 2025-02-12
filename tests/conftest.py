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
PGHOST = os.environ.get('PGHOST')
PGDATABASE = os.environ.get('PGDATABASE')
PGUSER = os.environ.get('PGUSER')
PGPASSWORD = os.environ.get('PGPASSWORD')

# Construct test database URL
TEST_DATABASE_URL = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}/{PGDATABASE}"

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
        connect_args={
            "sslmode": "require",
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5
        }
    )

    # Drop all tables first (if they exist)
    Base.metadata.drop_all(bind=engine)

    # Create all tables in correct order
    Base.metadata.create_all(bind=engine)

    yield engine

    # Clean up - drop all tables at the end of session
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a fresh database session for each test"""
    connection = test_engine.connect()
    transaction = connection.begin()

    Session = sessionmaker(bind=connection)
    session = Session()

    # Clear all tables in correct order
    session.execute(text("SET CONSTRAINTS ALL DEFERRED"))
    session.execute(text("TRUNCATE TABLE time_entries RESTART IDENTITY CASCADE"))
    session.execute(text("TRUNCATE TABLE projects RESTART IDENTITY CASCADE"))
    session.execute(text("TRUNCATE TABLE customers RESTART IDENTITY CASCADE"))
    session.execute(text("TRUNCATE TABLE project_managers RESTART IDENTITY CASCADE"))
    session.commit()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client using the test database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup is handled by db_session fixture

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def setup_test_data(db_session):
    """Set up test data in the database"""
    try:
        # Create test project managers first
        project_managers = [
            ProjectManager(name="Unassigned", email="unassigned@example.com"),
            ProjectManager(name="Test Manager", email="test.manager@example.com")
        ]
        for manager in project_managers:
            db_session.add(manager)
        db_session.commit()  # Commit project managers first

        # Create test customers
        customers = [
            Customer(name="Unassigned", contact_email="unassigned@example.com", status="active"),
            Customer(name="ECOLAB", contact_email="ecolab@example.com", status="active")
        ]
        for customer in customers:
            db_session.add(customer)
        db_session.commit()  # Commit customers before projects

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
            db_session.add(project)
        db_session.commit()

        yield {
            "customers": customers,
            "project_managers": project_managers,
            "projects": projects
        }
    except Exception as e:
        db_session.rollback()
        raise e
    finally:
        # Clear test data after the test
        for table in reversed(Base.metadata.sorted_tables):
            db_session.execute(table.delete())
        db_session.commit()
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import os
from pathlib import Path
from models.baseModel import Base
from database.database import get_db
from main import app

# Test database URL - using SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a fresh database session for each test"""
    Session = sessionmaker(bind=test_engine)
    session = Session()

    # Clear tables before each test
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client using the test database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Don't close here, as it's handled by the db_session fixture

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_csv_file():
    """Create a test CSV file with sample data"""
    csv_content = """Week Number,Month,Category,Subcategory,Customer,Project,Task Description,Hours,Date
41,October,Other,Other Training,Unassigned,Unassigned,New hire orientation,6.0,2024-10-07
41,October,Other,Other Training,ECOLAB,Project Magic Bullet,Training session,2.0,2024-10-07
"""
    csv_path = Path("tests/data/test_timesheet.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text(csv_content)
    return csv_path

@pytest.fixture(scope="function")
def setup_test_data(db_session):
    """Set up test data in the database"""
    from models.customerModel import Customer
    from models.projectModel import Project
    from models.projectManagerModel import ProjectManager

    # Create test customers
    customers = [
        Customer(name="Unassigned", contact_email="unassigned_test@example.com", status="active"),
        Customer(name="ECOLAB", contact_email="ecolab_test@example.com", status="active")
    ]
    for customer in customers:
        try:
            db_session.add(customer)
            db_session.flush()
        except:
            db_session.rollback()
            # Skip if customer already exists
            continue

    # Create test projects
    projects = [
        Project(
            project_id="Unassigned",
            name="Unassigned",
            customer="Unassigned",
            status="active"
        ),
        Project(
            project_id="Project_Magic_Bullet",
            name="Project Magic Bullet",
            customer="ECOLAB",
            status="active"
        )
    ]
    for project in projects:
        try:
            db_session.add(project)
            db_session.flush()
        except:
            db_session.rollback()
            # Skip if project already exists
            continue

    db_session.commit()

    yield {"customers": customers, "projects": projects}

    # Cleanup handled by db_session fixture
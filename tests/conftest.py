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
    connection = test_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
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
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="session")
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
    
    # Create test customers
    customers = [
        Customer(name="Unassigned", contact_email="unassigned@company.com"),
        Customer(name="ECOLAB", contact_email="contact@ecolab.com")
    ]
    
    # Create test projects
    projects = [
        Project(
            project_id="Unassigned",
            name="Unassigned",
            customer="Unassigned"
        ),
        Project(
            project_id="Project_Magic_Bullet",
            name="Project Magic Bullet",
            customer="ECOLAB"
        )
    ]
    
    db_session.add_all(customers)
    db_session.add_all(projects)
    db_session.commit()
    
    return {"customers": customers, "projects": projects}

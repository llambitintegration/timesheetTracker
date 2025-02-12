import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.database import Base, get_db
from main import app

# Use the actual database URL from environment variables
DATABASE_URL = f"postgresql://{os.getenv('PGUSER')}:{os.getenv('PGPASSWORD')}@{os.getenv('PGHOST')}/{os.getenv('PGDATABASE')}"

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def test_client():
    return TestClient(app)

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database session for each test"""
    Session = sessionmaker(bind=engine)
    session = Session()

    # Clear tables before each test
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

    try:
        yield session
    finally:
        session.close()
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

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

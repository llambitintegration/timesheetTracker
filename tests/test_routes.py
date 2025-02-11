import pytest
from fastapi.testclient import TestClient
from main import app
from datetime import date
import io
import csv
from pathlib import Path

# Test root endpoint
def test_root_endpoint(client):
    """Test the root endpoint returns correct welcome message"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

# Time entries tests
def test_get_time_entries_empty(client):
    """Test getting time entries when database is empty"""
    response = client.get("/time-entries/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0

def test_create_time_entry(client, setup_test_data):
    """Test creating a single time entry"""
    entry_data = {
        "week_number": 41,
        "month": "October",
        "category": "Other",
        "subcategory": "Other Training",
        "customer": "ECOLAB",
        "project": "Project_Magic_Bullet",
        "task_description": "Test task",
        "hours": 8.0,
        "date": "2024-10-07"
    }
    response = client.post("/time-entries/", json=entry_data)
    assert response.status_code == 201
    data = response.json()
    assert data["customer"] == "ECOLAB"
    assert data["project"] == "Project_Magic_Bullet"
    assert data["hours"] == 8.0

def test_get_time_entries_with_database_query(client, setup_test_data):
    """Test getting time entries with database query verification"""
    # Create multiple test entries first
    entries = [
        {
            "week_number": 41,
            "month": "October",
            "category": "Development",
            "subcategory": "Coding",
            "customer": "ECOLAB",
            "project": "Project_Magic_Bullet",
            "task_description": "Task 1",
            "hours": 8.0,
            "date": "2024-10-07"
        },
        {
            "week_number": 41,
            "month": "October",
            "category": "Development",
            "subcategory": "Testing",
            "customer": "ECOLAB",
            "project": "Project_Magic_Bullet",
            "task_description": "Task 2",
            "hours": 4.0,
            "date": "2024-10-07"
        }
    ]

    # Add entries to database
    for entry in entries:
        response = client.post("/time-entries/", json=entry)
        assert response.status_code == 201

    # Test database query
    response = client.get("/time-entries/")
    assert response.status_code == 200
    data = response.json()

    # Verify query results
    assert len(data) >= 2  # Should have at least our 2 entries
    assert any(entry["customer"] == "ECOLAB" for entry in data)
    assert any(entry["project"] == "Project_Magic_Bullet" for entry in data)
    assert any(entry["category"] == "Development" for entry in data)

def test_get_time_entries_complex_filtering(client, setup_test_data):
    """Test time entries with multiple filter combinations"""
    # Create test entries with different combinations
    entries = [
        {
            "week_number": 41,
            "month": "October",
            "category": "Development",
            "subcategory": "Coding",
            "customer": "ECOLAB",
            "project": "Project_Magic_Bullet",
            "task_description": "Dev Task",
            "hours": 8.0,
            "date": "2024-10-07"
        },
        {
            "week_number": 41,
            "month": "October",
            "category": "QA",
            "subcategory": "Testing",
            "customer": "ECOLAB",
            "project": "Project_Magic_Bullet",
            "task_description": "QA Task",
            "hours": 4.0,
            "date": "2024-10-07"
        }
    ]

    for entry in entries:
        response = client.post("/time-entries/", json=entry)
        assert response.status_code == 201

    # Test filtering by multiple parameters
    response = client.get("/time-entries/", params={
        "customer_name": "ECOLAB",
        "project_id": "Project_Magic_Bullet",
        "skip": 0,
        "limit": 10
    })

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

    # Verify all entries match filter criteria
    for entry in data:
        assert entry["customer"] == "ECOLAB"
        assert entry["project"] == "Project_Magic_Bullet"

def test_get_time_entries_empty_database(client):
    """Test time entries endpoint with empty database"""
    response = client.get("/time-entries/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_get_time_entries_invalid_filters(client):
    """Test time entries endpoint with invalid filter parameters"""
    response = client.get("/time-entries/", params={
        "customer_name": "NonExistentCustomer",
        "project_id": "NonExistentProject"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0

def test_create_time_entry_invalid_data(client):
    """Test creating a time entry with invalid data"""
    invalid_entry = {
        "week_number": 60,  # Invalid week number
        "month": "Invalid",  # Invalid month
        "category": "Other",
        "subcategory": "Training",
        "customer": "NonExistent",
        "project": "NonExistent",
        "hours": 25.0,  # Invalid hours
        "date": "2024-10-07"
    }
    response = client.post("/time-entries/", json=invalid_entry)
    assert response.status_code == 422

def test_upload_excel_valid(client, setup_test_data, tmp_path):
    """Test uploading a valid Excel file"""
    import pandas as pd

    # Create test Excel file
    excel_data = {
        'Week Number': [41, 41],
        'Month': ['October', 'October'],
        'Category': ['Other', 'Other'],
        'Subcategory': ['Other Training', 'Other Training'],
        'Customer': ['ECOLAB', 'ECOLAB'],
        'Project': ['Project_Magic_Bullet', 'Project_Magic_Bullet'],
        'Task Description': ['Test task', 'Another task'],
        'Hours': [8.0, 4.0],
        'Date': ['2024-10-07', '2024-10-07']
    }
    df = pd.DataFrame(excel_data)
    excel_file = tmp_path / "test.xlsx"
    df.to_excel(excel_file, index=False)

    with open(excel_file, "rb") as f:
        response = client.post(
            "/time-entries/upload/",
            files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

    assert response.status_code == 201
    data = response.json()
    assert len(data["entries"]) == 2
    assert data["validation_errors"] == []

# Removed CSV-related tests as we're only supporting XLS format

def test_get_time_entries_with_filters(client, setup_test_data):
    """Test getting time entries with filters"""
    # First create a test entry
    entry_data = {
        "week_number": 41,
        "month": "October",
        "category": "Other",
        "subcategory": "Other Training",
        "customer": "ECOLAB",
        "project": "Project_Magic_Bullet",
        "task_description": "Test task",
        "hours": 8.0,
        "date": "2024-10-07"
    }
    client.post("/time-entries/", json=entry_data)

    # Test filtering by customer
    response = client.get("/time-entries/", params={"customer_name": "ECOLAB"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(entry["customer"] == "ECOLAB" for entry in data)

    # Test filtering by project
    response = client.get("/time-entries/", params={"project_id": "Project_Magic_Bullet"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(entry["project"] == "Project_Magic_Bullet" for entry in data)

def test_get_time_entries_pagination(client, setup_test_data):
    """Test time entries pagination"""
    # Create multiple test entries
    entry_data = {
        "week_number": 41,
        "month": "October",
        "category": "Other",
        "subcategory": "Other Training",
        "customer": "ECOLAB",
        "project": "Project_Magic_Bullet",
        "task_description": "Test task",
        "hours": 8.0,
        "date": "2024-10-07"
    }

    for i in range(5):
        entry_data["task_description"] = f"Task {i}"
        client.post("/time-entries/", json=entry_data)

    # Test first page
    response = client.get("/time-entries/", params={"skip": 0, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Test second page
    response = client.get("/time-entries/", params={"skip": 2, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

if __name__ == "__main__":
    pytest.main(["-v"])
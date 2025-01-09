import pytest
from fastapi.testclient import TestClient
from main import app
from datetime import date
import io
import csv
from pathlib import Path

# Using the existing test client fixture from conftest.py
def test_root_endpoint(client):
    """Test the root endpoint returns correct welcome message"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome" in response.json()["message"]

def test_get_time_entries_empty(client):
    """Test getting time entries when database is empty"""
    response = client.get("/time-entries/")
    assert response.status_code == 200
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

def test_upload_csv_valid(client, setup_test_data, tmp_path):
    """Test uploading a valid CSV file"""
    csv_content = """Week Number,Month,Category,Subcategory,Customer,Project,Task Description,Hours,Date
41,October,Other,Other Training,ECOLAB,Project_Magic_Bullet,Test task,8.0,2024-10-07
41,October,Other,Other Training,ECOLAB,Project_Magic_Bullet,Another task,4.0,2024-10-07"""
    
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content)
    
    with open(csv_file, "rb") as f:
        response = client.post(
            "/time-entries/upload/",
            files={"file": ("test.csv", f, "text/csv")}
        )
    
    assert response.status_code == 201
    data = response.json()
    assert len(data["entries"]) == 2
    assert data["validation_errors"] == []

def test_upload_csv_invalid_format(client):
    """Test uploading CSV with invalid format"""
    # Create CSV with missing required columns
    csv_content = "Category,Hours\nOther,8.0"
    csv_file = io.StringIO(csv_content)
    
    response = client.post(
        "/time-entries/upload/",
        files={"file": ("test.csv", csv_file, "text/csv")}
    )
    
    assert response.status_code == 400
    assert "Missing required columns" in response.json()["detail"]

def test_upload_csv_with_validation_errors(client, setup_test_data, tmp_path):
    """Test uploading CSV with entries that will produce validation warnings"""
    csv_content = """Week Number,Month,Category,Subcategory,Customer,Project,Task Description,Hours,Date
41,October,Other,Other Training,NonExistent,NonExistent,Test task,8.0,2024-10-07"""
    
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content)
    
    with open(csv_file, "rb") as f:
        response = client.post(
            "/time-entries/upload/",
            files={"file": ("test.csv", f, "text/csv")}
        )
    
    assert response.status_code == 201
    data = response.json()
    assert len(data["entries"]) == 1  # Entry should be created with defaults
    assert len(data["validation_errors"]) > 0  # Should have validation errors

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

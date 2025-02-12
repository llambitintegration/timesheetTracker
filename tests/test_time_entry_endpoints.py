import pytest
from fastapi.testclient import TestClient
from tests.test_config import test_client, test_db
from database import schemas
from datetime import date

def test_create_time_entry(test_client: TestClient, test_db, setup_test_data):
    """Test creating a new time entry"""
    entry_data = {
        "week_number": 41,
        "month": "October",
        "category": "Development",
        "subcategory": "Backend",
        "customer": "ECOLAB",
        "project": "Project_Magic_Bullet",
        "task_description": "Test task",
        "hours": 8.0,
        "date": "2024-10-07"
    }
    response = test_client.post("/time-entries", json=entry_data)
    assert response.status_code == 201  # Changed to 201 for resource creation
    data = response.json()
    assert data["week_number"] == entry_data["week_number"]
    assert data["month"] == entry_data["month"]
    assert data["customer"] == entry_data["customer"]
    assert data["project"] == entry_data["project"]
    assert data["hours"] == entry_data["hours"]
    assert data["date"] == entry_data["date"]

def test_get_time_entry(test_client: TestClient, test_db, setup_test_data):
    """Test retrieving a time entry"""
    entry_data = {
        "week_number": 41,
        "month": "October",
        "category": "Development",
        "subcategory": "Backend",
        "customer": "ECOLAB",
        "project": "Project_Magic_Bullet",
        "task_description": "Test task",
        "hours": 8.0,
        "date": "2024-10-07"
    }
    create_response = test_client.post("/time-entries", json=entry_data)
    assert create_response.status_code == 201  # Changed to 201 for resource creation
    created_entry = create_response.json()

    response = test_client.get(f"/time-entries/{created_entry['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["week_number"] == entry_data["week_number"]
    assert data["customer"] == entry_data["customer"]
    assert data["project"] == entry_data["project"]
    assert data["hours"] == entry_data["hours"]

def test_get_nonexistent_time_entry(test_client: TestClient, test_db):
    """Test retrieving a non-existent time entry"""
    response = test_client.get("/time-entries/99999")
    assert response.status_code == 404
    assert "Time entry not found" in response.json()["detail"]

def test_update_time_entry(test_client: TestClient, test_db, setup_test_data):
    """Test updating a time entry"""
    entry_data = {
        "week_number": 41,
        "month": "October",
        "category": "Development",
        "subcategory": "Backend",
        "customer": "ECOLAB",
        "project": "Project_Magic_Bullet",
        "task_description": "Test task",
        "hours": 8.0,
        "date": "2024-10-07"
    }
    create_response = test_client.post("/time-entries", json=entry_data)
    assert create_response.status_code == 201  # Changed to 201 for resource creation
    created_entry = create_response.json()

    update_data = {
        "hours": 6.0,
        "task_description": "Updated task description"
    }
    response = test_client.put(f"/time-entries/{created_entry['id']}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["hours"] == update_data["hours"]
    assert data["task_description"] == update_data["task_description"]
    assert data["customer"] == entry_data["customer"]

def test_delete_time_entry(test_client: TestClient, test_db, setup_test_data):
    """Test deleting a time entry"""
    entry_data = {
        "week_number": 41,
        "month": "October",
        "category": "Development",
        "subcategory": "Backend",
        "customer": "ECOLAB",
        "project": "Project_Magic_Bullet",
        "task_description": "Test task",
        "hours": 8.0,
        "date": "2024-10-07"
    }
    create_response = test_client.post("/time-entries", json=entry_data)
    assert create_response.status_code == 201  # Changed to 201 for resource creation
    created_entry = create_response.json()

    response = test_client.delete(f"/time-entries/{created_entry['id']}")
    assert response.status_code == 204  # Changed to 204 for successful deletion

    # Verify time entry is deleted
    get_response = test_client.get(f"/time-entries/{created_entry['id']}")
    assert get_response.status_code == 404

def test_get_time_entries_by_project(test_client: TestClient, test_db, setup_test_data):
    """Test retrieving time entries filtered by project"""
    project_id = "Project_Magic_Bullet"

    # Create time entries for the project
    entries = [
        {
            "week_number": 41,
            "month": "October",
            "category": "Development",
            "subcategory": "Backend",
            "customer": "ECOLAB",
            "project": project_id,
            "task_description": f"Test task {i}",
            "hours": 8.0,
            "date": "2024-10-07"
        }
        for i in range(2)
    ]

    for entry in entries:
        response = test_client.post("/time-entries", json=entry)
        assert response.status_code == 201  # Changed to 201 for resource creation

    response = test_client.get(f"/time-entries?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= len(entries)
    for entry in data:
        assert entry["project"] == project_id

def test_get_all_time_entries(test_client: TestClient, test_db, setup_test_data):
    """Test retrieving all time entries"""
    entries = [
        {
            "week_number": 41,
            "month": "October",
            "category": "Development",
            "subcategory": "Backend",
            "customer": "ECOLAB",
            "project": "Project_Magic_Bullet",
            "task_description": f"Test task {i}",
            "hours": 8.0,
            "date": "2024-10-07"
        }
        for i in range(3)
    ]

    for entry in entries:
        response = test_client.post("/time-entries", json=entry)
        assert response.status_code == 201  # Changed to 201 for resource creation

    response = test_client.get("/time-entries")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= len(entries)
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
    assert response.status_code == 200
    data = response.json()
    assert data["week_number"] == entry_data["week_number"]
    assert data["month"] == entry_data["month"]
    assert data["customer"] == entry_data["customer"]
    assert data["project"] == entry_data["project"]
    assert data["hours"] == entry_data["hours"]
    assert data["date"] == entry_data["date"]

def test_get_time_entry(test_client: TestClient, test_db, setup_test_data):
    """Test retrieving a time entry"""
    # First create a time entry
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
    assert create_response.status_code == 200
    created_entry = create_response.json()

    # Then get the time entry
    response = test_client.get(f"/time-entries/{created_entry['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["week_number"] == entry_data["week_number"]
    assert data["customer"] == entry_data["customer"]
    assert data["project"] == entry_data["project"]
    assert data["hours"] == entry_data["hours"]

def test_update_time_entry(test_client: TestClient, test_db, setup_test_data):
    """Test updating a time entry"""
    # First create a time entry
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
    assert create_response.status_code == 200
    created_entry = create_response.json()

    # Update the time entry
    update_data = {
        "hours": 6.0,
        "task_description": "Updated task description"
    }
    response = test_client.put(f"/time-entries/{created_entry['id']}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["hours"] == update_data["hours"]
    assert data["task_description"] == update_data["task_description"]
    assert data["customer"] == entry_data["customer"]  # Original data should remain unchanged

def test_delete_time_entry(test_client: TestClient, test_db, setup_test_data):
    """Test deleting a time entry"""
    # First create a time entry
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
    assert create_response.status_code == 200
    created_entry = create_response.json()

    # Delete the time entry
    response = test_client.delete(f"/time-entries/{created_entry['id']}")
    assert response.status_code == 200

    # Verify time entry is deleted
    get_response = test_client.get(f"/time-entries/{created_entry['id']}")
    assert get_response.status_code == 404

def test_get_all_time_entries(test_client: TestClient, test_db, setup_test_data):
    """Test retrieving all time entries"""
    # Create some test time entries
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

    created_entries = []
    for entry in entries:
        response = test_client.post("/time-entries", json=entry)
        assert response.status_code == 200
        created_entries.append(response.json())

    # Get all time entries
    response = test_client.get("/time-entries")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= len(entries)  # Should at least contain our test entries

def test_get_time_entries_by_project(test_client: TestClient, test_db, setup_test_data):
    """Test retrieving time entries filtered by project"""
    # Create time entries for different projects
    project_id = "Project_Magic_Bullet"
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
        assert response.status_code == 200

    # Add an entry for a different project
    different_project_entry = {
        "week_number": 41,
        "month": "October",
        "category": "Development",
        "subcategory": "Backend",
        "customer": "Unassigned",
        "project": "Unassigned",
        "task_description": "Different project task",
        "hours": 8.0,
        "date": "2024-10-07"
    }
    response = test_client.post("/time-entries", json=different_project_entry)
    assert response.status_code == 200

    # Get time entries for specific project
    response = test_client.get(f"/time-entries?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(entries)  # Should only contain entries for the specified project
    for entry in data:
        assert entry["project"] == project_id
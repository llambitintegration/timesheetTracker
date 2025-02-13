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
    assert response.status_code == 201  # Created
    data = response.json()
    assert data["week_number"] == entry_data["week_number"]
    assert data["month"] == entry_data["month"]
    assert data["customer"] == entry_data["customer"]
    assert data["project"] == entry_data["project"]
    assert data["hours"] == entry_data["hours"]
    assert data["date"] == entry_data["date"]

def test_create_time_entry_invalid_data(test_client: TestClient, test_db):
    """Test creating a time entry with invalid data"""
    invalid_entry = {
        "week_number": 60,  # Invalid week number
        "month": "Invalid",  # Invalid month
        "category": "",  # Empty category
        "subcategory": "Backend",
        "customer": "ECOLAB",
        "project": "Project_Magic_Bullet",
        "task_description": "Test task",
        "hours": -1.0,  # Invalid hours
        "date": "invalid-date"  # Invalid date format
    }
    response = test_client.post("/time-entries", json=invalid_entry)
    assert response.status_code == 422  # Unprocessable Entity
    errors = response.json()
    assert "detail" in errors

def test_get_time_entry_by_id(test_client: TestClient, test_db, setup_test_data):
    """Test retrieving a specific time entry by ID"""
    # First create an entry
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
    assert create_response.status_code == 201
    created_entry = create_response.json()

    # Then retrieve it
    response = test_client.get(f"/time-entries/{created_entry['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created_entry["id"]
    assert data["week_number"] == entry_data["week_number"]
    assert data["customer"] == entry_data["customer"]
    assert data["project"] == entry_data["project"]

def test_get_nonexistent_time_entry(test_client: TestClient, test_db):
    """Test retrieving a non-existent time entry"""
    response = test_client.get("/time-entries/99999")
    assert response.status_code == 404
    assert "Time entry not found" in response.json()["detail"]

def test_update_time_entry(test_client: TestClient, test_db, setup_test_data):
    """Test updating a time entry"""
    # First create an entry
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
    assert create_response.status_code == 201
    created_entry = create_response.json()

    # Update the entry
    update_data = {
        "hours": 6.0,
        "task_description": "Updated task description"
    }
    response = test_client.put(f"/time-entries/{created_entry['id']}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["hours"] == update_data["hours"]
    assert data["task_description"] == update_data["task_description"]
    assert data["customer"] == entry_data["customer"]  # Unchanged field

def test_update_time_entry_invalid_data(test_client: TestClient, test_db, setup_test_data):
    """Test updating a time entry with invalid data"""
    # First create an entry
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
    created_entry = create_response.json()

    # Try to update with invalid data
    invalid_update = {
        "hours": -1.0,  # Invalid hours
        "week_number": 60  # Invalid week number
    }
    response = test_client.put(f"/time-entries/{created_entry['id']}", json=invalid_update)
    assert response.status_code == 422
    assert "detail" in response.json()

def test_update_nonexistent_time_entry(test_client: TestClient, test_db):
    """Test updating a non-existent time entry"""
    update_data = {"hours": 6.0}
    response = test_client.put("/time-entries/99999", json=update_data)
    assert response.status_code == 404
    assert "Time entry not found" in response.json()["detail"]

def test_delete_time_entry(test_client: TestClient, test_db, setup_test_data):
    """Test deleting a time entry"""
    # First create an entry
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
    assert create_response.status_code == 201
    created_entry = create_response.json()

    # Delete the entry
    response = test_client.delete(f"/time-entries/{created_entry['id']}")
    assert response.status_code == 204  # No Content

    # Verify it's deleted
    get_response = test_client.get(f"/time-entries/{created_entry['id']}")
    assert get_response.status_code == 404

def test_delete_nonexistent_time_entry(test_client: TestClient, test_db):
    """Test deleting a non-existent time entry"""
    response = test_client.delete("/time-entries/99999")
    assert response.status_code == 404
    assert "Time entry not found" in response.json()["detail"]

def test_get_time_entries_list_empty(test_client: TestClient, test_db):
    """Test getting time entries list when empty"""
    response = test_client.get("/time-entries")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_get_time_entries_list_with_filters(test_client: TestClient, test_db, setup_test_data):
    """Test getting time entries list with filters"""
    # Create test entries
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
    test_client.post("/time-entries", json=entry_data)

    # Test different filters
    filters = [
        {"customer_name": "ECOLAB"},
        {"project_id": "Project_Magic_Bullet"},
        {"date": "2024-10-07"},
        {"customer_name": "ECOLAB", "project_id": "Project_Magic_Bullet"}
    ]

    for filter_params in filters:
        response = test_client.get("/time-entries", params=filter_params)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Verify filters are applied correctly
        for entry in data:
            if "customer_name" in filter_params:
                assert entry["customer"] == filter_params["customer_name"]
            if "project_id" in filter_params:
                assert entry["project"] == filter_params["project_id"]
            if "date" in filter_params:
                assert entry["date"] == filter_params["date"]

def test_get_time_entries_pagination(test_client: TestClient, test_db, setup_test_data):
    """Test time entries pagination"""
    # Create multiple entries
    base_entry = {
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

    # Create 5 entries
    for i in range(5):
        entry = base_entry.copy()
        entry["task_description"] = f"Task {i}"
        test_client.post("/time-entries", json=entry)

    # Test first page
    response = test_client.get("/time-entries", params={"skip": 0, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Test second page
    response = test_client.get("/time-entries", params={"skip": 2, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Test last page
    response = test_client.get("/time-entries", params={"skip": 4, "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 2  # Should be 1 or 2 depending on total entries
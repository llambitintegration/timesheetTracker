import pytest
from fastapi.testclient import TestClient
from tests.test_config import test_client, test_db
from database import schemas

def test_create_project_manager(test_client: TestClient, test_db):
    """Test creating a new project manager"""
    pm_data = {
        "name": "Test Manager",
        "email": "test.manager@example.com"
    }
    response = test_client.post("/project-managers", json=pm_data)
    assert response.status_code == 201  # Changed to 201 for resource creation
    data = response.json()
    assert data["name"] == pm_data["name"]
    assert data["email"] == pm_data["email"]

def test_get_project_manager(test_client: TestClient, test_db):
    """Test retrieving a project manager"""
    pm_data = {
        "name": "Get Test Manager",
        "email": "get_test.manager@example.com"
    }
    create_response = test_client.post("/project-managers", json=pm_data)
    assert create_response.status_code == 201  # Changed to 201 for resource creation

    response = test_client.get(f"/project-managers/{pm_data['email']}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == pm_data["name"]
    assert data["email"] == pm_data["email"]

def test_get_nonexistent_project_manager(test_client: TestClient, test_db):
    """Test retrieving a non-existent project manager"""
    response = test_client.get("/project-managers/nonexistent@example.com")
    assert response.status_code == 404
    assert "Project manager not found" in response.json()["detail"]

def test_update_project_manager(test_client: TestClient, test_db):
    """Test updating a project manager"""
    pm_data = {
        "name": "Update Test Manager",
        "email": "update_test.manager@example.com"
    }
    create_response = test_client.post("/project-managers", json=pm_data)
    assert create_response.status_code == 201

    update_data = {
        "name": "Updated Manager Name"
    }
    response = test_client.put(f"/project-managers/{pm_data['email']}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["email"] == pm_data["email"]

def test_update_nonexistent_project_manager(test_client: TestClient, test_db):
    """Test updating a non-existent project manager"""
    update_data = {
        "name": "Updated Name"
    }
    response = test_client.put("/project-managers/nonexistent@example.com", json=update_data)
    assert response.status_code == 404
    assert "Project manager not found" in response.json()["detail"]

def test_delete_project_manager(test_client: TestClient, test_db):
    """Test deleting a project manager"""
    pm_data = {
        "name": "Delete Test Manager",
        "email": "delete_test.manager@example.com"
    }
    create_response = test_client.post("/project-managers", json=pm_data)
    assert create_response.status_code == 201

    response = test_client.delete(f"/project-managers/{pm_data['email']}")
    assert response.status_code == 204

    # Verify project manager is deleted
    get_response = test_client.get(f"/project-managers/{pm_data['email']}")
    assert get_response.status_code == 404

def test_delete_nonexistent_project_manager(test_client: TestClient, test_db):
    """Test deleting a non-existent project manager"""
    response = test_client.delete("/project-managers/nonexistent@example.com")
    assert response.status_code == 404
    assert "Project manager not found" in response.json()["detail"]

def test_get_all_project_managers(test_client: TestClient, test_db):
    """Test retrieving all project managers"""
    project_managers = [
        {
            "name": f"Test Manager {i}",
            "email": f"test.manager{i}@example.com"
        }
        for i in range(3)
    ]

    for pm in project_managers:
        response = test_client.post("/project-managers", json=pm)
        assert response.status_code == 201  # Changed to 201 for resource creation

    response = test_client.get("/project-managers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= len(project_managers)

def test_create_duplicate_project_manager(test_client: TestClient, test_db):
    """Test creating a project manager with duplicate name"""
    pm_data = {
        "name": "Duplicate Test Manager",
        "email": "duplicate.manager@example.com"
    }

    # Create first project manager
    response = test_client.post("/project-managers", json=pm_data)
    assert response.status_code == 201  # Changed to 201 for resource creation

    # Try to create duplicate
    response = test_client.post("/project-managers", json=pm_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]
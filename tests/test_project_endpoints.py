import pytest
from fastapi.testclient import TestClient
from tests.test_config import test_client, test_db
from database import schemas

def test_create_project(test_client: TestClient, test_db):
    """Test creating a new project"""
    project_data = {
        "project_id": "TEST_001",
        "name": "Test Project",
        "customer": "Test Customer",
        "description": "Test Description",
        "project_manager": "Test Manager",
        "status": "active"
    }
    response = test_client.post("/projects", json=project_data)
    assert response.status_code == 201  # Changed to 201 for resource creation
    data = response.json()
    assert data["project_id"] == project_data["project_id"]
    assert data["name"] == project_data["name"]
    assert data["customer"] == project_data["customer"]
    assert data["description"] == project_data["description"]
    assert data["project_manager"] == project_data["project_manager"]
    assert data["status"] == project_data["status"]

def test_get_project(test_client: TestClient, test_db):
    """Test retrieving a project"""
    project_data = {
        "project_id": "TEST_002",
        "name": "Get Test Project",
        "customer": "Test Customer",
        "description": "Test Description",
        "project_manager": "Test Manager",
        "status": "active"
    }
    create_response = test_client.post("/projects", json=project_data)
    assert create_response.status_code == 201  # Changed to 201 for resource creation

    response = test_client.get(f"/projects/{project_data['project_id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == project_data["project_id"]
    assert data["name"] == project_data["name"]
    assert data["customer"] == project_data["customer"]

def test_update_project(test_client: TestClient, test_db):
    """Test updating a project"""
    project_data = {
        "project_id": "TEST_003",
        "name": "Update Test Project",
        "customer": "Test Customer",
        "description": "Test Description",
        "project_manager": "Test Manager",
        "status": "active"
    }
    create_response = test_client.post("/projects", json=project_data)
    assert create_response.status_code == 201  # Changed to 201 for resource creation

    update_data = {
        "name": "Updated Project Name",
        "description": "Updated Description"
    }
    response = test_client.put(f"/projects/{project_data['project_id']}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["project_id"] == project_data["project_id"]

def test_delete_project(test_client: TestClient, test_db):
    """Test deleting a project"""
    project_data = {
        "project_id": "TEST_004",
        "name": "Delete Test Project",
        "customer": "Test Customer",
        "description": "Test Description",
        "project_manager": "Test Manager",
        "status": "active"
    }
    create_response = test_client.post("/projects", json=project_data)
    assert create_response.status_code == 201  # Changed to 201 for resource creation

    response = test_client.delete(f"/projects/{project_data['project_id']}")
    assert response.status_code == 204  # Changed to 204 for successful deletion

    # Verify project is deleted
    get_response = test_client.get(f"/projects/{project_data['project_id']}")
    assert get_response.status_code == 404

def test_get_all_projects(test_client: TestClient, test_db):
    """Test retrieving all projects"""
    projects = [
        {
            "project_id": f"TEST_{i:03d}",
            "name": f"Test Project {i}",
            "customer": "Test Customer",
            "description": f"Test Description {i}",
            "project_manager": "Test Manager",
            "status": "active"
        }
        for i in range(3)
    ]

    for project in projects:
        response = test_client.post("/projects", json=project)
        assert response.status_code == 201  # Changed to 201 for resource creation

    response = test_client.get("/projects")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= len(projects)

def test_create_duplicate_project(test_client: TestClient, test_db):
    """Test creating a project with duplicate project_id"""
    project_data = {
        "project_id": "TEST_DUP",
        "name": "Duplicate Test Project",
        "customer": "Test Customer",
        "description": "Test Description",
        "project_manager": "Test Manager",
        "status": "active"
    }

    # Create first project
    response = test_client.post("/projects", json=project_data)
    assert response.status_code == 201  # Changed to 201 for resource creation

    # Try to create duplicate
    response = test_client.post("/projects", json=project_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]
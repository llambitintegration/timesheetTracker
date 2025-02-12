import pytest
from fastapi.testclient import TestClient
from tests.test_config import test_client, test_db
from database import schemas

def test_create_customer(test_client: TestClient):
    """Test creating a new customer"""
    customer_data = {
        "name": "Test Customer",
        "contact_email": "test@example.com",
        "industry": "Technology",
        "status": "active"
    }
    response = test_client.post("/customers/", json=customer_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == customer_data["name"]
    assert data["contact_email"] == customer_data["contact_email"]

def test_get_customer(test_client: TestClient):
    """Test retrieving a customer"""
    # First create a customer
    customer_data = {
        "name": "Get Test Customer",
        "contact_email": "get_test@example.com",
        "industry": "Technology",
        "status": "active"
    }
    create_response = test_client.post("/customers/", json=customer_data)
    assert create_response.status_code == 200

    # Then get the customer
    response = test_client.get(f"/customers/{customer_data['name']}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == customer_data["name"]

def test_update_customer(test_client: TestClient):
    """Test updating a customer"""
    # First create a customer
    customer_data = {
        "name": "Update Test Customer",
        "contact_email": "update_test@example.com",
        "industry": "Technology",
        "status": "active"
    }
    create_response = test_client.post("/customers/", json=customer_data)
    assert create_response.status_code == 200

    # Update the customer
    update_data = {
        "contact_email": "updated@example.com",
        "industry": "Healthcare"
    }
    response = test_client.put(f"/customers/{customer_data['name']}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["contact_email"] == update_data["contact_email"]
    assert data["industry"] == update_data["industry"]

def test_delete_customer(test_client: TestClient):
    """Test deleting a customer"""
    # First create a customer
    customer_data = {
        "name": "Delete Test Customer",
        "contact_email": "delete_test@example.com",
        "industry": "Technology",
        "status": "active"
    }
    create_response = test_client.post("/customers/", json=customer_data)
    assert create_response.status_code == 200

    # Delete the customer
    response = test_client.delete(f"/customers/{customer_data['name']}")
    assert response.status_code == 200

    # Verify customer is deleted
    get_response = test_client.get(f"/customers/{customer_data['name']}")
    assert get_response.status_code == 404

def test_get_all_customers(test_client: TestClient):
    """Test retrieving all customers"""
    response = test_client.get("/customers/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

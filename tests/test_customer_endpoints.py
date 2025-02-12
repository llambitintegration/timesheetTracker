import pytest
from fastapi.testclient import TestClient
from tests.test_config import test_client, test_db
from database import schemas

def test_create_customer(test_client: TestClient, test_db):
    """Test creating a new customer"""
    customer_data = {
        "name": "Test Customer",
        "contact_email": "test@example.com",
        "industry": "Technology",
        "status": "active"
    }
    response = test_client.post("/customers", json=customer_data)
    assert response.status_code == 201  # Changed to 201 for resource creation
    data = response.json()
    assert data["name"] == customer_data["name"]
    assert data["contact_email"] == customer_data["contact_email"]
    assert data["industry"] == customer_data["industry"]
    assert data["status"] == customer_data["status"]

def test_get_customer(test_client: TestClient, test_db):
    """Test retrieving a customer"""
    # First create a customer
    customer_data = {
        "name": "Get Test Customer",
        "contact_email": "get_test@example.com",
        "industry": "Technology",
        "status": "active"
    }
    create_response = test_client.post("/customers", json=customer_data)
    assert create_response.status_code == 201  # Changed to 201 for resource creation

    # Then get the customer
    response = test_client.get(f"/customers/{customer_data['name']}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == customer_data["name"]
    assert data["contact_email"] == customer_data["contact_email"]
    assert data["industry"] == customer_data["industry"]

def test_update_customer(test_client: TestClient, test_db):
    """Test updating a customer"""
    # First create a customer
    customer_data = {
        "name": "Update Test Customer",
        "contact_email": "update_test@example.com",
        "industry": "Technology",
        "status": "active"
    }
    create_response = test_client.post("/customers", json=customer_data)
    assert create_response.status_code == 201  # Changed to 201 for resource creation

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
    assert data["name"] == customer_data["name"]  # Name should remain unchanged

def test_delete_customer(test_client: TestClient, test_db):
    """Test deleting a customer"""
    # First create a customer
    customer_data = {
        "name": "Delete Test Customer",
        "contact_email": "delete_test@example.com",
        "industry": "Technology",
        "status": "active"
    }
    create_response = test_client.post("/customers", json=customer_data)
    assert create_response.status_code == 201  # Changed to 201 for resource creation

    # Delete the customer
    response = test_client.delete(f"/customers/{customer_data['name']}")
    assert response.status_code == 204  # Changed to 204 for successful deletion

    # Verify customer is deleted
    get_response = test_client.get(f"/customers/{customer_data['name']}")
    assert get_response.status_code == 404

def test_get_all_customers(test_client: TestClient, test_db):
    """Test retrieving all customers"""
    # Create some test customers first
    customers = [
        {
            "name": f"Test Customer {i}",
            "contact_email": f"test{i}@example.com",
            "industry": "Technology",
            "status": "active"
        }
        for i in range(3)
    ]

    for customer in customers:
        response = test_client.post("/customers", json=customer)
        assert response.status_code == 201  # Changed to 201 for resource creation

    # Get all customers
    response = test_client.get("/customers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= len(customers)  # Should at least contain our test customers

def test_create_duplicate_customer(test_client: TestClient, test_db):
    """Test creating a customer with duplicate name"""
    customer_data = {
        "name": "Duplicate Test Customer",
        "contact_email": "duplicate@example.com",
        "industry": "Technology",
        "status": "active"
    }

    # Create first customer
    response = test_client.post("/customers", json=customer_data)
    assert response.status_code == 201  # Changed to 201 for resource creation

    # Try to create duplicate
    response = test_client.post("/customers", json=customer_data)
    assert response.status_code == 400
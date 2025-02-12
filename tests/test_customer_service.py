import pytest
from fastapi import HTTPException
from services.customer_service import CustomerService
from database.schemas import CustomerCreate, CustomerUpdate
from models.customerModel import Customer

def test_create_customer(db_session):
    """Test creating a customer through service"""
    service = CustomerService(db_session)
    customer_data = CustomerCreate(
        name="Test Customer",
        contact_email="test@example.com",
        industry="Technology",
        status="active"
    )

    result = service.create_customer(customer_data)
    assert result is not None
    assert result.name == "Test Customer"
    assert result.contact_email == "test@example.com"
    assert result.industry == "Technology"
    assert result.status == "active"

def test_create_duplicate_customer(db_session):
    """Test attempting to create a customer with duplicate name"""
    service = CustomerService(db_session)
    customer_data = CustomerCreate(
        name="Duplicate Test",
        contact_email="duplicate@test.com"
    )

    # Create first customer
    service.create_customer(customer_data)

    # Attempt to create duplicate
    with pytest.raises(HTTPException) as exc_info:
        service.create_customer(customer_data)
    assert exc_info.value.status_code == 400
    assert "Customer with name Duplicate Test already exists" in str(exc_info.value.detail)

def test_get_customer(db_session):
    """Test retrieving a customer by name"""
    service = CustomerService(db_session)
    customer_data = CustomerCreate(
        name="Get Test",
        contact_email="get@test.com"
    )

    created = service.create_customer(customer_data)
    retrieved = service.get_customer("Get Test")

    assert retrieved is not None
    assert retrieved.name == "Get Test"
    assert retrieved.contact_email == "get@test.com"

def test_get_nonexistent_customer(db_session):
    """Test retrieving a non-existent customer"""
    service = CustomerService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        service.get_customer("NonexistentCustomer")
    assert exc_info.value.status_code == 404
    assert "Customer not found: NonexistentCustomer" in str(exc_info.value.detail)

def test_get_all_customers(db_session):
    """Test retrieving all customers with pagination"""
    service = CustomerService(db_session)

    # Create multiple customers
    customers = [
        CustomerCreate(name=f"Test Customer {i}", contact_email=f"test{i}@example.com")
        for i in range(3)
    ]
    for customer in customers:
        service.create_customer(customer)

    # Test without pagination
    all_customers = service.get_all_customers()
    assert len(all_customers) >= 3

    # Test with pagination
    page_1 = service.get_all_customers(skip=0, limit=2)
    assert len(page_1) == 2
    page_2 = service.get_all_customers(skip=2, limit=2)
    assert len(page_2) >= 1

def test_update_customer(db_session):
    """Test updating a customer"""
    service = CustomerService(db_session)
    customer_data = CustomerCreate(
        name="Update Test",
        contact_email="update@test.com",
        industry="Old Industry"
    )

    created = service.create_customer(customer_data)
    update_data = CustomerUpdate(industry="New Industry")
    updated = service.update_customer("Update Test", update_data)

    assert updated is not None
    assert updated.industry == "New Industry"
    assert updated.contact_email == "update@test.com"  # Unchanged field

def test_update_nonexistent_customer(db_session):
    """Test attempting to update a non-existent customer"""
    service = CustomerService(db_session)
    update_data = CustomerUpdate(industry="New Industry")
    with pytest.raises(HTTPException) as exc_info:
        service.update_customer("NonexistentCustomer", update_data)
    assert exc_info.value.status_code == 404
    assert "Customer not found: NonexistentCustomer" in str(exc_info.value.detail)

def test_delete_customer(db_session):
    """Test deleting a customer"""
    service = CustomerService(db_session)
    customer_data = CustomerCreate(
        name="Delete Test",
        contact_email="delete@test.com"
    )

    # Create and verify customer exists
    created = service.create_customer(customer_data)
    assert service.get_customer("Delete Test") is not None

    # Delete customer
    result = service.delete_customer("Delete Test")
    assert result is True

    # Verify customer is deleted
    with pytest.raises(HTTPException) as exc_info:
        service.get_customer("Delete Test")
    assert exc_info.value.status_code == 404
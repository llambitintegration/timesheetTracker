import pytest
from sqlalchemy.exc import IntegrityError
from database.customer_repository import CustomerRepository
from models.customerModel import Customer

def test_customer_repository_create(db_session):
    """Test creating a customer through repository"""
    repo = CustomerRepository()
    customer = Customer(
        name="Test Customer",
        contact_email="test@example.com",
        industry="Technology"
    )
    
    result = repo.create(db_session, customer)
    assert result is not None
    assert result.name == "Test Customer"
    assert result.contact_email == "test@example.com"
    assert result.id is not None

def test_customer_repository_get_by_id(db_session):
    """Test retrieving a customer by ID"""
    repo = CustomerRepository()
    customer = Customer(
        name="Get By ID Test",
        contact_email="getbyid@test.com"
    )
    
    created = repo.create(db_session, customer)
    retrieved = repo.get_by_id(db_session, created.id)
    
    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == "Get By ID Test"

def test_customer_repository_get_by_name(db_session):
    """Test retrieving a customer by name"""
    repo = CustomerRepository()
    customer = Customer(
        name="Get By Name Test",
        contact_email="getbyname@test.com"
    )
    
    repo.create(db_session, customer)
    retrieved = repo.get_by_name(db_session, "Get By Name Test")
    
    assert retrieved is not None
    assert retrieved.name == "Get By Name Test"
    assert retrieved.contact_email == "getbyname@test.com"

def test_customer_repository_get_all(db_session):
    """Test retrieving all customers"""
    repo = CustomerRepository()
    customers = [
        Customer(name="All Test 1", contact_email="all1@test.com"),
        Customer(name="All Test 2", contact_email="all2@test.com"),
        Customer(name="All Test 3", contact_email="all3@test.com")
    ]
    
    for customer in customers:
        repo.create(db_session, customer)
    
    all_customers = repo.get_all(db_session)
    assert len(all_customers) >= 3  # May include existing customers from other tests
    assert any(c.name == "All Test 1" for c in all_customers)
    assert any(c.name == "All Test 2" for c in all_customers)
    assert any(c.name == "All Test 3" for c in all_customers)

def test_customer_repository_update(db_session):
    """Test updating a customer"""
    repo = CustomerRepository()
    customer = Customer(
        name="Update Test",
        contact_email="update@test.com",
        industry="Old Industry"
    )
    
    created = repo.create(db_session, customer)
    created.industry = "New Industry"
    updated = repo.update(db_session, created)
    
    assert updated.industry == "New Industry"
    retrieved = repo.get_by_id(db_session, created.id)
    assert retrieved.industry == "New Industry"

def test_customer_repository_delete(db_session):
    """Test deleting a customer"""
    repo = CustomerRepository()
    customer = Customer(
        name="Delete Test",
        contact_email="delete@test.com"
    )
    
    created = repo.create(db_session, customer)
    assert repo.get_by_id(db_session, created.id) is not None
    
    repo.delete(db_session, created.id)
    assert repo.get_by_id(db_session, created.id) is None

def test_customer_repository_unique_name_constraint(db_session):
    """Test that customer names must be unique"""
    repo = CustomerRepository()
    customer1 = Customer(
        name="Unique Test",
        contact_email="unique1@test.com"
    )
    customer2 = Customer(
        name="Unique Test",  # Same name as customer1
        contact_email="unique2@test.com"
    )
    
    repo.create(db_session, customer1)
    with pytest.raises(IntegrityError):
        repo.create(db_session, customer2)

def test_customer_repository_pagination(db_session):
    """Test repository pagination"""
    repo = CustomerRepository()
    # Create 5 customers
    for i in range(5):
        customer = Customer(
            name=f"Page Test {i}",
            contact_email=f"page{i}@test.com"
        )
        repo.create(db_session, customer)
    
    # Test first page (2 items)
    page1 = repo.get_all(db_session, skip=0, limit=2)
    assert len(page1) == 2
    
    # Test second page (2 items)
    page2 = repo.get_all(db_session, skip=2, limit=2)
    assert len(page2) == 2
    
    # Test last page (1 item)
    page3 = repo.get_all(db_session, skip=4, limit=2)
    assert len(page3) == 1

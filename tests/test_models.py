import pytest
from models.timeEntry import TimeEntry
from models.customerModel import Customer
from models.projectModel import Project
from models.projectManagerModel import ProjectManager
from datetime import date
from sqlalchemy.exc import IntegrityError

def test_time_entry_creation():
    """Test TimeEntry model creation"""
    entry = TimeEntry(
        week_number=41,
        month="October",
        category="Other",
        subcategory="Other Training",
        customer="Unassigned",
        project="Unassigned",
        task_description="Test task",
        hours=8.0,
        date=date(2024, 10, 7)
    )
    assert entry.week_number == 41
    assert entry.hours == 8.0
    assert entry.customer == "Unassigned"
    assert entry.date == date(2024, 10, 7)
    assert entry.task_description == "Test task"

def test_customer_creation():
    """Test Customer model creation"""
    customer = Customer(
        name="Test Customer",
        contact_email="test@example.com",
        industry="Technology",
        status="active",
        address="123 Test St",
        phone="123-456-7890"
    )
    assert customer.name == "Test Customer"
    assert customer.contact_email == "test@example.com"
    assert customer.industry == "Technology"
    assert customer.status == "active"
    assert customer.address == "123 Test St"
    assert customer.phone == "123-456-7890"

def test_customer_default_status():
    """Test Customer model default status"""
    customer = Customer(
        name="Test Customer",
        contact_email="test@example.com"
    )
    assert customer.status == "active"

def test_project_creation():
    """Test Project model creation"""
    project = Project(
        project_id="TEST_001",
        name="Test Project",
        customer="Test Customer",
        description="Test Description",
        project_manager="Test Manager",
        status="active"
    )
    assert project.project_id == "TEST_001"
    assert project.name == "Test Project"
    assert project.customer == "Test Customer"
    assert project.description == "Test Description"
    assert project.project_manager == "Test Manager"
    assert project.status == "active"

def test_project_manager_creation():
    """Test ProjectManager model creation"""
    manager = ProjectManager(
        name="Test Manager",
        email="manager@example.com"
    )
    assert manager.name == "Test Manager"
    assert manager.email == "manager@example.com"

def test_project_default_status():
    """Test Project model default status"""
    project = Project(
        project_id="TEST_001",
        name="Test Project",
        customer="Test Customer"
    )
    assert project.status == "active"

def test_time_entry_repr():
    """Test TimeEntry string representation"""
    entry = TimeEntry(
        id=1,
        week_number=41,
        month="October",
        category="Other",
        subcategory="Other Training",
        customer="Test Customer",
        project="TEST_001",
        hours=8.0,
        date=date(2024, 10, 7)
    )
    expected = "<TimeEntry(id=1, date=2024-10-07, hours=8.0, project=TEST_001)>"
    assert str(entry) == expected

def test_project_repr():
    """Test Project string representation"""
    project = Project(
        id=1,
        project_id="TEST_001",
        name="Test Project"
    )
    expected = "<Project(id=1, project_id=TEST_001, name=Test Project)>"
    assert str(project) == expected

def test_model_timestamps(db_session):
    """Test model timestamps are automatically set"""
    customer = Customer(
        name="Timestamp Test",
        contact_email="timestamp@test.com"
    )
    db_session.add(customer)
    db_session.commit()

    assert customer.created_at is not None
    assert customer.updated_at is None  # Should be None until updated

    import time
    time.sleep(0.1)  # Ensure timestamp difference
    customer.industry = "Updated Industry"
    db_session.commit()

    assert customer.updated_at is not None  # Should be set after update
    assert customer.updated_at > customer.created_at
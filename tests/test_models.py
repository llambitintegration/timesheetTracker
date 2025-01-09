import pytest
from models.timeEntry import TimeEntry
from models.customerModel import Customer
from models.projectModel import Project
from datetime import date

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

def test_customer_creation():
    """Test Customer model creation"""
    customer = Customer(
        name="Test Customer",
        contact_email="test@example.com",
        industry="Technology"
    )
    assert customer.name == "Test Customer"
    assert customer.contact_email == "test@example.com"
    assert customer.status == "active"  # Default value

def test_project_creation():
    """Test Project model creation"""
    project = Project(
        project_id="TEST_001",
        name="Test Project",
        customer="Test Customer",
        description="Test Description"
    )
    assert project.project_id == "TEST_001"
    assert project.customer == "Test Customer"
    assert project.status == "active"  # Default value

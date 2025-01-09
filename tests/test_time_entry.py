import pytest
from datetime import datetime, date
from database.schemas import TimeEntryCreate
from services.time_entry_service import TimeEntryService
from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT
from pydantic import ValidationError

def test_create_single_time_entry(db_session):
    """Test creating a single time entry"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        week_number=1,
        month="January",
        category="Development",
        subcategory="Coding",
        customer="TestCustomer",
        project="TestProject",
        task_description="Unit testing",
        hours=8.0,
        date=date(2024, 1, 1)
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.week_number == 1
    assert result.month == "January"
    assert result.category == "Development"
    assert result.hours == 8.0
    assert result.date == date(2024, 1, 1)

def test_create_time_entry_with_defaults(db_session):
    """Test creating a time entry with default values"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        week_number=1,
        month="January",
        category="Development",
        subcategory="Coding",
        customer=None,  # Should default to Unassigned
        project=None,   # Should default to Unassigned
        task_description="Testing defaults",
        hours=4.0,
        date=date(2024, 1, 1)
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.customer == DEFAULT_CUSTOMER
    assert result.project == DEFAULT_PROJECT
    assert result.hours == 4.0

def test_create_time_entry_invalid_hours(db_session):
    """Test creating a time entry with invalid hours"""
    service = TimeEntryService(db_session)

    # Test hours > 24
    with pytest.raises(ValidationError) as exc_info:
        TimeEntryCreate(
            week_number=1,
            month="January",
            category="Development",
            subcategory="Coding",
            customer="TestCustomer",
            project="TestProject",
            task_description="Invalid hours",
            hours=25.0,  # Invalid: more than 24 hours
            date=date(2024, 1, 1)
        )
    assert "Input should be less than or equal to 24" in str(exc_info.value)

    # Test negative hours
    with pytest.raises(ValidationError) as exc_info:
        TimeEntryCreate(
            week_number=1,
            month="January",
            category="Development",
            subcategory="Coding",
            customer="TestCustomer",
            project="TestProject",
            task_description="Invalid hours",
            hours=-1.0,  # Invalid: negative hours
            date=date(2024, 1, 1)
        )
    assert "Input should be greater than or equal to 0" in str(exc_info.value)

def test_get_time_entries(db_session):
    """Test retrieving time entries"""
    service = TimeEntryService(db_session)

    # Create test entries
    entries = [
        TimeEntryCreate(
            week_number=1,
            month="January",
            category="Development",
            subcategory="Coding",
            customer="TestCustomer",
            project="TestProject",
            task_description=f"Entry {i}",
            hours=8.0,
            date=date(2024, 1, 1)
        ) for i in range(3)
    ]

    for entry in entries:
        service.create_time_entry(entry)

    # Test listing all entries
    results = service.get_time_entries()
    assert len(results) == 3

    # Test pagination
    paginated = service.get_time_entries(skip=1, limit=1)
    assert len(paginated) == 1

def test_get_time_entries_with_filters(db_session):
    """Test retrieving time entries with filters"""
    service = TimeEntryService(db_session)

    # Create entries for different customers
    customers = ["Customer1", "Customer2"]
    for customer in customers:
        entry = TimeEntryCreate(
            week_number=1,
            month="January",
            category="Development",
            subcategory="Coding",
            customer=customer,
            project=f"{customer}_Project",
            task_description=f"Work for {customer}",
            hours=8.0,
            date=date(2024, 1, 1)
        )
        service.create_time_entry(entry)

    # Test filtering by customer
    results = service.get_time_entries(customer_name="Customer1")
    assert len(results) == 1
    assert results[0].customer == "Customer1"

    # Test filtering by project
    results = service.get_time_entries(project_id="Customer1_Project")
    assert len(results) == 1
    assert results[0].project == "Customer1_Project"

def test_time_entry_date_validation(db_session):
    """Test time entry date validation"""
    service = TimeEntryService(db_session)

    # Future date should be valid
    future_entry = TimeEntryCreate(
        week_number=1,
        month="January",
        category="Development",
        subcategory="Coding",
        customer="TestCustomer",
        project="TestProject",
        task_description="Future work",
        hours=8.0,
        date=date(2025, 1, 1)
    )

    result = service.create_time_entry(future_entry)
    assert result is not None
    assert result.date == date(2025, 1, 1)
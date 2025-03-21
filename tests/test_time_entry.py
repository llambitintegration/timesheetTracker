import pytest
from datetime import datetime, date
from services.time_entry_service import TimeEntryService
from database.schemas import TimeEntryCreate
from models.customerModel import Customer
from pydantic import ValidationError

def test_create_time_entry_auto_calculations(db_session):
    """Test that week number and month are automatically calculated"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
        task_description="Test auto calculations",
        hours=8.0,
        date=date(2024, 1, 15)  # A date in January, week 3
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.id is not None  # ID should be auto-generated
    assert result.week_number == 3  # Should be week 3
    assert result.month == "January"
    assert result.hours == 8.0
    assert result.customer is None  # Should be null with new schema
    assert result.project is None   # Should be null with new schema

def test_create_time_entry_default_hours(db_session):
    """Test that hours default to 0 when not provided"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
        task_description="Test default hours",
        date=date(2024, 1, 15)
        # Not providing hours
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.hours == 0.0
    assert result.customer is None  # Should be null
    assert result.project is None   # Should be null

def test_create_time_entry_auto_id(db_session):
    """Test that IDs are auto-generated and unique"""
    service = TimeEntryService(db_session)

    # Create two entries
    entry1 = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
        task_description="Entry 1",
        date=date(2024, 1, 15)
    )
    entry2 = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
        task_description="Entry 2",
        date=date(2024, 1, 15)
    )

    result1 = service.create_time_entry(entry1)
    result2 = service.create_time_entry(entry2)

    assert result1.id is not None
    assert result2.id is not None
    assert result1.id != result2.id  # IDs should be unique

def test_create_single_time_entry(db_session, setup_test_data):
    """Test creating a single time entry"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
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
    assert result.customer is None  # Should be null by default
    assert result.project is None   # Should be null by default

def test_get_time_entries_with_filters(db_session, setup_test_data):
    """Test retrieving time entries with filters"""
    service = TimeEntryService(db_session)

    # Create test entries
    entry1 = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
        task_description="Work item",
        hours=8.0,
        date=date(2024, 1, 1)
    )
    service.create_time_entry(entry1)

    # Test filtering
    results = service.get_time_entries()
    assert len(results) >= 1
    for entry in results:
        assert isinstance(entry.customer, (str, type(None)))  # Can be string or None
        assert isinstance(entry.project, (str, type(None)))   # Can be string or None

def test_create_time_entry_with_valid_references(db_session, setup_test_data):
    """Test creating a time entry with valid customer and project references"""
    service = TimeEntryService(db_session)

    # Get existing customer and project from test data
    customer = setup_test_data['customers'][0]
    project = setup_test_data['projects'][0]

    entry = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
        customer=customer.name,
        project=project.project_id,
        task_description="Work with valid references",
        hours=8.0,
        date=date(2024, 1, 1)
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.customer == customer.name
    assert result.project == project.project_id

def test_create_time_entry_with_nonexistent_references(db_session):
    """Test creating a time entry with non-existent customer and project"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
        customer="NonExistentCustomer",
        project="NonExistentProject",
        task_description="Work with invalid references",
        hours=8.0,
        date=date(2024, 1, 1)
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.customer is None  # Should be null when customer doesn't exist
    assert result.project is None   # Should be null when project doesn't exist

def test_create_time_entry_with_defaults(db_session):
    """Test creating a time entry with default values"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
        task_description="Testing defaults",
        date=date(2024, 1, 1)
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.customer is None  # Should be null
    assert result.project is None   # Should be null
    assert result.hours == 0.0      # Should default to 0

def test_create_time_entry_invalid_hours(db_session):
    """Test creating a time entry with invalid hours"""
    service = TimeEntryService(db_session)

    # Test negative hours
    with pytest.raises(ValidationError) as exc_info:
        TimeEntryCreate(
            category="Development",
            subcategory="Coding",
            task_description="Invalid hours",
            hours=-1.0,  # Invalid: negative hours
            date=date(2024, 1, 1)
        )
    assert "Input should be greater than or equal to 0" in str(exc_info.value)

def test_create_time_entry_with_nonexistent_customer(db_session):
    """Test creating a time entry with a non-existent customer"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
        customer="NonExistentCustomer",  # Customer that doesn't exist
        project="NonExistentProject",    # Project that doesn't exist
        task_description="Testing foreign key handling",
        hours=8.0,
        date=date(2024, 1, 1)
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.customer is None  # Should be null
    assert result.project is None   # Should be null
    assert result.hours == 8.0

def test_api_example_default_values(db_session):
    """Test the API example with default values working correctly"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        category="string",
        subcategory="string",
        customer="string",  # Non-existent customer
        project="string",   # Non-existent project
        task_description="string",
        date=date(2025, 1, 9)
        # Not providing hours or week_number/month
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.customer is None  # Should be null
    assert result.project is None   # Should be null
    assert result.hours == 0.0      # Should default to 0
    assert result.week_number == 2  # Should be calculated from date
    assert result.month == "January"  # Should be calculated from date

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

def test_create_time_entry_zero_hours(db_session):
    """Test creating a time entry with zero hours"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
        task_description="Test zero hours",
        hours=0.0,  # Explicitly set to zero
        date=date(2024, 1, 15)
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.hours == 0.0
    assert result.week_number == 3  # Week 3 of January
    assert result.month == "January"

def test_create_time_entry_auto_date_calculations(db_session):
    """Test that date calculations are handled automatically"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
        task_description="Test date calculations",
        hours=8.0,
        date=date(2024, 2, 1)  # February 1st, 2024
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.week_number == 5  # Should be week 5
    assert result.month == "February"
    # Original date should be preserved
    assert result.date == date(2024, 2, 1)

def test_time_entry_with_invalid_project(db_session, setup_test_data):
    """Test that creating a time entry with an invalid project falls back to default"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
        customer="ECOLAB",  # Using existing customer
        project="Wichita, KS",  # Invalid project name that's causing the error
        task_description="Testing invalid project handling",
        hours=8.0,
        date=date(2024, 1, 1)
    )

    # This should not raise an exception, but fall back to default project
    result = service.create_time_entry(entry)
    assert result is not None
    assert result.project is None  # Should fall back to default project
    assert result.hours == 8.0
    assert result.date == date(2024, 1, 1)
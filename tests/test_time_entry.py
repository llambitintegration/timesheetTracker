import pytest
from datetime import datetime, date
from services.time_entry_service import TimeEntryService
from database.schemas import TimeEntryCreate
from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

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

def test_create_time_entry_zero_hours(db_session):
    """Test that zero hours are allowed"""
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
        customer="ECOLAB",  # Using existing customer from setup_test_data
        project="Project_Magic_Bullet",  # Using existing project from setup_test_data
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
    assert result.customer == "ECOLAB"
    assert result.project == "Project_Magic_Bullet"

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
    assert result.customer == DEFAULT_CUSTOMER
    assert result.project == DEFAULT_PROJECT
    assert result.hours == 0.0  # Should default to 0

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
    assert result.customer == DEFAULT_CUSTOMER  # Should fall back to default
    assert result.project == DEFAULT_PROJECT    # Should fall back to default
    assert result.hours == 8.0

def test_create_time_entry_customer_mismatch(db_session, setup_test_data):
    """Test creating a time entry with mismatched customer-project relationship"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
        customer="ECOLAB",  # Existing customer
        project="NonMatchingProject",  # Project not belonging to this customer
        task_description="Testing customer-project mismatch",
        hours=8.0,
        date=date(2024, 1, 1)
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.customer == DEFAULT_CUSTOMER  # Should fall back to default
    assert result.project == DEFAULT_PROJECT    # Should fall back to default

def test_get_time_entries_with_filters(db_session, setup_test_data):
    """Test retrieving time entries with filters"""
    service = TimeEntryService(db_session)

    # Create test entries with existing customer and project
    entry1 = TimeEntryCreate(
        category="Development",
        subcategory="Coding",
        customer="ECOLAB",
        project="Project_Magic_Bullet",
        task_description="Work for ECOLAB",
        hours=8.0,
        date=date(2024, 1, 1)
    )
    service.create_time_entry(entry1)

    # Test filtering by customer
    results = service.get_time_entries(customer_name="ECOLAB")
    assert len(results) == 1
    assert results[0].customer == "ECOLAB"

    # Test filtering by project
    results = service.get_time_entries(project_id="Project_Magic_Bullet")
    assert len(results) == 1
    assert results[0].project == "Project_Magic_Bullet"

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
    assert result.customer == DEFAULT_CUSTOMER
    assert result.project == DEFAULT_PROJECT
    assert result.hours == 0.0  # Should default to 0
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
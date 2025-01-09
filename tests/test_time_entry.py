import pytest
from datetime import datetime, date
from database.schemas import TimeEntryCreate
from services.time_entry_service import TimeEntryService
from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from models.customerModel import Customer

def test_create_single_time_entry(db_session, setup_test_data):
    """Test creating a single time entry"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        week_number=1,
        month="January",
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

def test_create_time_entry_with_nonexistent_customer(db_session):
    """Test creating a time entry with a non-existent customer"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        week_number=1,
        month="January",
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
        week_number=1,
        month="January",
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

def test_create_time_entry_api_example(db_session):
    """Test the specific API example provided - creating entry with non-existent 'string' customer"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        week_number=53,
        month="January",
        category="string",
        subcategory="string",
        customer="string",  # Non-existent customer
        project="string",   # Non-existent project
        task_description="string",
        hours=24.0,
        date=date(2025, 1, 9)
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.customer == DEFAULT_CUSTOMER
    assert result.project == DEFAULT_PROJECT
    assert result.week_number == 53
    assert result.month == "January"
    assert result.hours == 24.0
    assert result.date == date(2025, 1, 9)

def test_get_time_entries_with_filters(db_session, setup_test_data):
    """Test retrieving time entries with filters"""
    service = TimeEntryService(db_session)

    # Create test entries with existing customer and project
    entry1 = TimeEntryCreate(
        week_number=1,
        month="January",
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
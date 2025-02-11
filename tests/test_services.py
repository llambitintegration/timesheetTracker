import pytest
from datetime import datetime, date
from services.time_entry_service import TimeEntryService
from database.schemas import TimeEntryCreate
from models import TimeEntry
from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT

def test_create_time_entry(db_session, setup_test_data):
    """Test creating a single time entry"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        category="Other",
        subcategory="Other Training",
        customer="ECOLAB",
        project="Project_Magic_Bullet",
        task_description="Test entry",
        hours=8.0,
        date=date(2024, 10, 7)
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.customer == "ECOLAB"
    assert result.project == "Project_Magic_Bullet"
    assert result.hours == 8.0
    assert result.week_number == 41
    assert result.month == "October"

def test_create_time_entry_with_defaults(db_session, setup_test_data):
    """Test creating a time entry with default values"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        category="Other",
        subcategory="Other Training",
        customer="NonExistentCustomer",
        project="NonExistentProject",
        task_description="Test entry",
        hours=8.0,
        date=date(2024, 10, 7)
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.customer == DEFAULT_CUSTOMER
    assert result.project == DEFAULT_PROJECT
    assert result.hours == 8.0
    assert result.week_number == 41
    assert result.month == "October"

def test_create_many_entries(db_session, setup_test_data):
    """Test bulk creation of time entries"""
    service = TimeEntryService(db_session)
    entries = [
        TimeEntryCreate(
            category="Other",
            subcategory="Other Training",
            customer="ECOLAB",
            project="Project_Magic_Bullet",
            task_description="Entry 1",
            hours=8.0,
            date=date(2024, 10, 7)
        ),
        TimeEntryCreate(
            category="Other",
            subcategory="Other Training",
            customer="NonExistentCustomer",
            project="NonExistentProject",
            task_description="Entry 2",
            hours=8.0,
            date=date(2024, 10, 7)
        )
    ]

    results = service.create_many_entries(entries)
    assert len(results) == 2
    assert results[0].customer == "ECOLAB"
    assert results[1].customer == DEFAULT_CUSTOMER
    assert results[0].project == "Project_Magic_Bullet"
    assert results[1].project == DEFAULT_PROJECT

def test_get_time_entries(db_session, setup_test_data):
    """Test retrieving time entries with filters"""
    service = TimeEntryService(db_session)

    # Create some test entries first
    entry = TimeEntryCreate(
        category="Other",
        subcategory="Other Training",
        customer="ECOLAB",
        project="Project_Magic_Bullet",
        task_description="Test entry",
        hours=8.0,
        date=date(2024, 10, 7)
    )
    service.create_time_entry(entry)

    # Test filtering by project
    entries = service.get_time_entries(project_id="Project_Magic_Bullet")
    assert len(entries) == 1
    assert entries[0].project == "Project_Magic_Bullet"

    # Test filtering by customer
    entries = service.get_time_entries(customer_name="ECOLAB")
    assert len(entries) == 1
    assert entries[0].customer == "ECOLAB"

    # Test with non-existent filter
    entries = service.get_time_entries(project_id="NonExistentProject")
    assert len(entries) == 0

def test_get_time_entries_pagination(db_session, setup_test_data):
    """Test time entries pagination"""
    service = TimeEntryService(db_session)

    # Create multiple test entries
    entries = []
    for i in range(5):
        entry = TimeEntryCreate(
            category="Other",
            subcategory="Other Training",
            customer="ECOLAB",
            project="Project_Magic_Bullet",
            task_description=f"Entry {i}",
            hours=8.0,
            date=date(2024, 10, 7)
        )
        entries.append(entry)
    service.create_many_entries(entries)

    # Test first page
    page_1 = service.get_time_entries(skip=0, limit=2)
    assert len(page_1) == 2

    # Test second page
    page_2 = service.get_time_entries(skip=2, limit=2)
    assert len(page_2) == 2

    # Test last page
    page_3 = service.get_time_entries(skip=4, limit=2)
    assert len(page_3) == 1
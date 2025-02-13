import pytest
from datetime import datetime, date
from services.time_entry_service import TimeEntryService
from database.schemas import TimeEntryCreate
from models import TimeEntry

def test_create_time_entry(db_session, setup_test_data):
    """Test creating a single time entry"""
    service = TimeEntryService(db_session)
    entry = TimeEntryCreate(
        category="Other",
        subcategory="Other Training",
        task_description="Test entry",
        hours=8.0,
        date=date(2024, 10, 7)
    )

    result = service.create_time_entry(entry)
    assert result is not None
    assert result.customer is None
    assert result.project is None
    assert result.hours == 8.0
    assert result.week_number == 41
    assert result.month == "October"

def test_create_time_entry_with_nonexistent_references(db_session, setup_test_data):
    """Test creating a time entry with non-existent customer and project"""
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
    assert result.customer is None
    assert result.project is None
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

    results = service.bulk_create(db_session, entries)
    assert len(results) == 2
    assert all(entry.customer is None for entry in results)
    assert all(entry.project is None for entry in results)

def test_get_time_entries(db_session, setup_test_data):
    """Test retrieving time entries with filters"""
    service = TimeEntryService(db_session)

    # Create test entry
    entry = TimeEntryCreate(
        category="Other",
        subcategory="Other Training",
        task_description="Test entry",
        hours=8.0,
        date=date(2024, 10, 7)
    )
    service.create_time_entry(entry)

    # Test basic retrieval
    entries = service.get_time_entries()
    assert len(entries) >= 1
    for entry in entries:
        assert isinstance(entry.customer, (str, type(None)))  # Can be string or None
        assert isinstance(entry.project, (str, type(None)))   # Can be string or None

def test_get_time_entries_pagination(db_session, setup_test_data):
    """Test time entries pagination"""
    service = TimeEntryService(db_session)

    # Create multiple test entries
    entries = []
    for i in range(5):
        entry = TimeEntryCreate(
            category="Other",
            subcategory="Other Training",
            task_description=f"Entry {i}",
            hours=8.0,
            date=date(2024, 10, 7)
        )
        entries.append(entry)

    # Use bulk create for better performance
    service.bulk_create(db_session, entries)

    # Test first page
    page_1 = service.get_time_entries(skip=0, limit=2)
    assert len(page_1) == 2

    # Test second page
    page_2 = service.get_time_entries(skip=2, limit=2)
    assert len(page_2) == 2

    # Test last page
    page_3 = service.get_time_entries(skip=4, limit=2)
    assert len(page_3) == 1
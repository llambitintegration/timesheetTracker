import pytest
from utils.utils import parse_csv, clean_string_value, parse_date, validate_week_number, validate_month
from datetime import datetime
from pathlib import Path

def test_parse_csv_with_valid_data(test_csv_file, setup_test_data):
    """Test parsing a valid CSV file"""
    with open(test_csv_file, 'r') as file:
        entries = parse_csv(file)

    assert len(entries) == 2
    assert entries[0].customer == "Unassigned"
    assert entries[0].hours == 6.0
    assert entries[1].customer == "ECOLAB"
    assert entries[1].project == "Project_Magic_Bullet"

def test_clean_string_value():
    """Test string cleaning functionality"""
    assert clean_string_value("  Test  ") == "Test"
    assert clean_string_value("") == ""
    assert clean_string_value(None) == ""
    assert clean_string_value("Project-123", field_type="project") == "Project_123"
    assert clean_string_value("other training", field_type="category") == "Other Training"
    assert clean_string_value("info/file management", field_type="subcategory") == "Info/File Management"

def test_parse_date():
    """Test date parsing functionality"""
    # Test various date formats
    assert parse_date("2024-01-01") == datetime(2024, 1, 1).date()
    assert parse_date("01/01/24") == datetime(2024, 1, 1).date()
    assert parse_date("01-01-2024") == datetime(2024, 1, 1).date()

    # Test invalid date handling
    today = datetime.now().date()
    assert parse_date("invalid_date") == today
    assert parse_date("") == today
    assert parse_date(None) == today

def test_validate_week_number():
    """Test week number validation"""
    assert validate_week_number(1) == 1
    assert validate_week_number(53) == 53
    assert validate_week_number("1") == 1
    assert validate_week_number("53") == 53

    # Test invalid week numbers
    current_week = datetime.now().isocalendar()[1]
    assert validate_week_number(0) == current_week
    assert validate_week_number(54) == current_week
    assert validate_week_number("invalid") == current_week

def test_validate_month():
    """Test month name validation"""
    assert validate_month("January") == "January"
    assert validate_month("january") == "January"
    assert validate_month("JANUARY") == "January"

    # Test invalid month handling
    current_month = datetime.now().strftime("%B")
    assert validate_month("Invalid") == current_month
    assert validate_month("") == current_month
    assert validate_month(None) == current_month

def test_parse_csv_with_missing_required_columns(tmp_path):
    """Test CSV parsing with missing required columns"""
    invalid_csv = tmp_path / "invalid.csv"
    invalid_csv.write_text("Category,Hours\n")

    with pytest.raises(ValueError) as exc_info:
        with open(invalid_csv, 'r') as file:
            parse_csv(file)
    assert "Missing required columns" in str(exc_info.value)

def test_parse_csv_with_invalid_hours(tmp_path):
    """Test CSV parsing with invalid hours"""
    invalid_csv = tmp_path / "invalid_hours.csv"
    csv_content = """Week Number,Month,Category,Subcategory,Customer,Project,Task Description,Hours,Date
41,October,Other,Other Training,Unassigned,Unassigned,Test task,-1.0,2024-10-07"""
    invalid_csv.write_text(csv_content)

    with open(invalid_csv, 'r') as file:
        entries = parse_csv(file)
    assert len(entries) == 0  # Invalid hours should be skipped

def test_parse_csv_with_empty_rows(tmp_path):
    """Test CSV parsing with empty rows"""
    csv_file = tmp_path / "empty_rows.csv"
    csv_content = """Week Number,Month,Category,Subcategory,Customer,Project,Task Description,Hours,Date

41,October,Other,Other Training,Unassigned,Unassigned,Task 1,8.0,2024-10-07

41,October,Other,Other Training,Unassigned,Unassigned,Task 2,8.0,2024-10-07

"""
    csv_file.write_text(csv_content)

    with open(csv_file, 'r') as file:
        entries = parse_csv(file)
    assert len(entries) == 2  # Empty rows should be ignored

def test_parse_csv_with_special_characters(tmp_path):
    """Test CSV parsing with special characters in text fields"""
    csv_file = tmp_path / "special_chars.csv"
    csv_content = """Week Number,Month,Category,Subcategory,Customer,Project,Task Description,Hours,Date
41,October,Other,Other Training,Test & Co.,Project-123,"Task, with comma",8.0,2024-10-07"""
    csv_file.write_text(csv_content)

    with open(csv_file, 'r') as file:
        entries = parse_csv(file)
    assert len(entries) == 1
    assert entries[0].customer == "Test & Co."
    assert entries[0].project == "Project_123"
    assert entries[0].task_description == "Task, with comma"
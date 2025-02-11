import pytest
from fastapi.testclient import TestClient
from main import app
import pandas as pd
from pathlib import Path
import logging
from utils.xls_analyzer import XLSAnalyzer

logger = logging.getLogger(__name__)

def create_test_excel(tmp_path, data):
    """Helper function to create test Excel file"""
    df = pd.DataFrame(data)
    excel_file = tmp_path / "test.xlsx"
    df.to_excel(excel_file, index=False)
    return excel_file

@pytest.fixture
def valid_timesheet_data():
    """Fixture for valid timesheet data"""
    return {
        'Week Number': [41, 41],
        'Month': ['October', 'October'],
        'Category': ['Development', 'Testing'],
        'Subcategory': ['Backend', 'QA'],
        'Customer': ['ECOLAB', 'ECOLAB'],
        'Project': ['Project_Magic_Bullet', 'Project_Magic_Bullet'],
        'Task Description': ['API Development', 'Integration Testing'],
        'Hours': [8.0, 4.0],
        'Date': ['2024-10-07', '2024-10-07']
    }

@pytest.fixture
def invalid_timesheet_data():
    """Fixture for invalid timesheet data"""
    return {
        'Category': ['Development'],
        'Hours': [8.0],
        'Date': ['2024-10-07']
    }

def test_xls_analyzer_valid(tmp_path, valid_timesheet_data):
    """Test XLSAnalyzer with valid data"""
    excel_file = create_test_excel(tmp_path, valid_timesheet_data)

    with open(excel_file, "rb") as f:
        contents = f.read()
        analyzer = XLSAnalyzer()
        records = analyzer.read_excel(contents)

        assert len(records) == 2
        assert records[0]['Customer'] == 'ECOLAB'
        assert records[0]['Project'] == 'Project_Magic_Bullet'
        assert records[0]['Hours'] == 8.0
        assert records[1]['Hours'] == 4.0

def test_xls_analyzer_empty_file(tmp_path):
    """Test XLSAnalyzer with empty file"""
    analyzer = XLSAnalyzer()
    with pytest.raises(ValueError):
        analyzer.read_excel(b'')

def test_xls_analyzer_invalid_data(tmp_path, invalid_timesheet_data):
    """Test XLSAnalyzer with invalid data"""
    excel_file = create_test_excel(tmp_path, invalid_timesheet_data)

    with open(excel_file, "rb") as f:
        contents = f.read()
        analyzer = XLSAnalyzer()
        records = analyzer.read_excel(contents)

        assert len(records) == 1
        assert records[0]['Customer'] == 'Unassigned'
        assert records[0]['Project'] == 'Unassigned'
        assert records[0]['Category'] == 'Development'
        assert records[0]['Hours'] == 8.0

def test_dash_customer_handling(client, setup_test_data, tmp_path):
    """Test handling of dash (-) values in customer field"""
    data = {
        'Week Number': [41],
        'Month': ['October'],
        'Category': ['Development'],
        'Subcategory': ['Backend'],
        'Customer': ['-'],
        'Project': ['-'],
        'Task Description': ['Test task'],
        'Hours': [8.0],
        'Date': ['2024-10-07']
    }
    excel_file = create_test_excel(tmp_path, data)

    with open(excel_file, "rb") as f:
        response = client.post(
            "/time-entries/upload/",
            files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

    assert response.status_code == 201
    entries = response.json()["entries"]
    assert len(entries) == 1
    assert entries[0]["customer"] == "Unassigned"
    assert entries[0]["project"] == "Unassigned"

def test_upload_excel_valid(client, setup_test_data, tmp_path, valid_timesheet_data):
    """Test uploading a valid Excel file"""
    excel_file = create_test_excel(tmp_path, valid_timesheet_data)

    with open(excel_file, "rb") as f:
        response = client.post(
            "/time-entries/upload/",
            files={"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

    assert response.status_code == 201
    data = response.json()
    assert len(data["entries"]) == 2
    assert data["validation_errors"] == []

def test_xls_analyzer_date_conversion(tmp_path):
    """Test date conversion in XLSAnalyzer"""
    data = {
        'Week Number': [41, 41],
        'Month': ['October', 'October'],
        'Category': ['Test', 'Test'],
        'Subcategory': ['Test', 'Test'],
        'Customer': ['ECOLAB', 'ECOLAB'],
        'Project': ['Project_Magic_Bullet', 'Project_Magic_Bullet'],
        'Task Description': ['Test 1', 'Test 2'],
        'Hours': [8.0, 8.0],
        'Date': ['2024-10-07', '2024-10-08']
    }
    excel_file = create_test_excel(tmp_path, data)

    with open(excel_file, "rb") as f:
        contents = f.read()
        analyzer = XLSAnalyzer()
        records = analyzer.read_excel(contents)

        assert len(records) == 2
        assert records[0]['Date'] == '2024-10-07'
        assert records[1]['Date'] == '2024-10-08'

def test_xls_analyzer_missing_columns(tmp_path):
    """Test XLSAnalyzer with missing required columns"""
    data = {
        'Category': ['Test'],
        'Hours': [8.0],
        'Date': ['2024-10-07']
    }
    excel_file = create_test_excel(tmp_path, data)

    with open(excel_file, "rb") as f:
        contents = f.read()
        analyzer = XLSAnalyzer()
        records = analyzer.read_excel(contents)

        assert len(records) == 1
        assert records[0]['Customer'] == 'Unassigned'
        assert records[0]['Project'] == 'Unassigned'
        assert records[0]['Week Number'] == 0
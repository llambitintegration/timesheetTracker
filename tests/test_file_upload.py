<replit_final_file>
import pytest
from fastapi.testclient import TestClient
from main import app
import io
import pandas as pd
from pathlib import Path
import logging
import asyncio
import httpx
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
        assert records[0]['Customer'] == '-'
        assert records[0]['Project'] == '-'

def test_xls_analyzer_date_conversion(tmp_path):
    """Test date conversion in XLSAnalyzer"""
    data = {
        'Date': ['2024-10-07', '2024-10-08'],
        'Week Number': [41, 41],
        'Category': ['Test', 'Test']
    }
    excel_file = create_test_excel(tmp_path, data)

    with open(excel_file, "rb") as f:
        contents = f.read()
        analyzer = XLSAnalyzer()
        records = analyzer.read_excel(contents)

        assert len(records) == 2
        assert isinstance(records[0]['Date'], pd.Timestamp)
        assert str(records[0]['Date'].date()) == '2024-10-07'

def test_xls_analyzer_missing_columns(tmp_path):
    """Test XLSAnalyzer with missing required columns"""
    data = {'Category': ['Test'], 'Hours': [8.0]}
    excel_file = create_test_excel(tmp_path, data)

    with open(excel_file, "rb") as f:
        contents = f.read()
        analyzer = XLSAnalyzer()
        records = analyzer.read_excel(contents)

        assert len(records) == 1
        assert records[0]['Customer'] == '-'
        assert records[0]['Project'] == '-'
        assert records[0]['Week Number'] == 0
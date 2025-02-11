import pytest
from fastapi.testclient import TestClient
from main import app
import io
import pandas as pd
from pathlib import Path
import logging
import asyncio
import httpx

logger = logging.getLogger(__name__)

def create_test_excel(tmp_path, data):
    """Helper function to create test Excel file"""
    df = pd.DataFrame(data)
    excel_file = tmp_path / "test.xlsx"
    df.to_excel(excel_file, index=False)
    return excel_file

def create_test_csv(tmp_path, data):
    """Helper function to create test CSV file"""
    df = pd.DataFrame(data)
    csv_file = tmp_path / "test.csv"
    df.to_csv(csv_file, index=False)
    return csv_file

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

def test_upload_excel_valid(client, tmp_path, valid_timesheet_data, setup_test_data):
    """Test uploading a valid Excel file"""
    excel_file = create_test_excel(tmp_path, valid_timesheet_data)

    with open(excel_file, "rb") as f:
        files = {"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = client.post("/time-entries/upload/", files=files)

    assert response.status_code == 201, f"Response: {response.json()}"
    data = response.json()
    assert "entries" in data
    assert len(data["entries"]) == 2
    assert data["validation_errors"] == []

    # Verify the entries were created correctly
    for entry in data["entries"]:
        assert entry["customer"] == "ECOLAB"
        assert entry["project"] == "Project_Magic_Bullet"
        assert float(entry["hours"]) in [8.0, 4.0]

def test_upload_csv_valid(client, tmp_path, valid_timesheet_data, setup_test_data):
    """Test uploading a valid CSV file"""
    csv_file = create_test_csv(tmp_path, valid_timesheet_data)

    with open(csv_file, "rb") as f:
        files = {"file": ("test.csv", f, "text/csv")}
        response = client.post("/time-entries/upload/", files=files)

    assert response.status_code == 201, f"Response: {response.json()}"
    data = response.json()
    assert len(data["entries"]) == 2
    assert data["validation_errors"] == []

def test_upload_invalid_format(client, tmp_path, invalid_timesheet_data):
    """Test uploading file with invalid format"""
    excel_file = create_test_excel(tmp_path, invalid_timesheet_data)

    with open(excel_file, "rb") as f:
        files = {"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = client.post("/time-entries/upload/", files=files)

    assert response.status_code == 400
    assert "Missing required columns" in response.json()["detail"]

def test_upload_empty_file(client):
    """Test uploading an empty file"""
    empty_file = io.BytesIO()
    files = {"file": ("empty.xlsx", empty_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    response = client.post("/time-entries/upload/", files=files)

    assert response.status_code == 400

def test_upload_bulk_entries(client, tmp_path, setup_test_data):
    """Test bulk upload performance with many entries"""
    # Create large dataset
    num_entries = 100
    large_data = {
        'Week Number': [41] * num_entries,
        'Month': ['October'] * num_entries,
        'Category': ['Development'] * num_entries,
        'Subcategory': ['Backend'] * num_entries,
        'Customer': ['ECOLAB'] * num_entries,
        'Project': ['Project_Magic_Bullet'] * num_entries,
        'Task Description': [f'Task {i}' for i in range(num_entries)],
        'Hours': [8.0] * num_entries,
        'Date': ['2024-10-07'] * num_entries
    }

    excel_file = create_test_excel(tmp_path, large_data)

    with open(excel_file, "rb") as f:
        files = {"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = client.post("/time-entries/upload/", files=files)

    assert response.status_code == 201, f"Response: {response.json()}"
    data = response.json()
    assert len(data["entries"]) == num_entries
    assert data["validation_errors"] == []

@pytest.mark.asyncio
async def test_concurrent_uploads(client, tmp_path, valid_timesheet_data, setup_test_data):
    """Test handling of concurrent uploads"""
    base_url = "http://testserver"

    async def upload_file():
        excel_file = create_test_excel(tmp_path, valid_timesheet_data)
        async with httpx.AsyncClient(base_url=base_url) as ac:
            with open(excel_file, "rb") as f:
                files = {"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                response = await ac.post("/time-entries/upload/", files=files)
                return response.status_code

    # Run concurrent uploads
    tasks = [upload_file() for _ in range(3)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Check if any tasks failed
    errors = [r for r in results if isinstance(r, Exception)]
    if errors:
        pytest.fail(f"Concurrent uploads failed with errors: {errors}")

    # Verify all successful responses
    assert all(status == 201 for status in results if not isinstance(status, Exception))

def test_invalid_data_validation(client, tmp_path):
    """Test validation of invalid data in uploaded file"""
    invalid_data = {
        'Week Number': [41],
        'Month': ['October'],
        'Category': ['Other'],
        'Subcategory': ['Training'],
        'Customer': ['NonExistent'],
        'Project': ['NonExistent'],
        'Task Description': ['Test'],
        'Hours': [8.0],
        'Date': ['2024-10-07']
    }

    excel_file = create_test_excel(tmp_path, invalid_data)

    with open(excel_file, "rb") as f:
        files = {"file": ("test.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = client.post("/time-entries/upload/", files=files)

    assert response.status_code == 201, f"Response: {response.json()}"
    data = response.json()
    assert "entries" in data
    assert "validation_errors" in data
    assert len(data["entries"]) == 1
    assert data["entries"][0]["customer"] == "Unassigned"

if __name__ == "__main__":
    pytest.main(["-v"])
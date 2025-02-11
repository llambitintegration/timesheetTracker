
from fastapi.testclient import TestClient
import pytest
from main import app
from datetime import datetime
import re

client = TestClient(app)

def validate_timestamp(timestamp_str: str) -> bool:
    """Validate ISO timestamp format"""
    try:
        datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

def test_time_entry_interface():
    """Test TimeEntry interface matches API response"""
    response = client.get("/time-entries")
    assert response.status_code == 200
    entries = response.json()
    
    if entries:  # If we have any entries
        entry = entries[0]
        assert isinstance(entry.get('id'), (int, str))
        assert isinstance(entry.get('week_number'), int)
        assert isinstance(entry.get('month'), str)
        assert isinstance(entry.get('category'), str)
        assert isinstance(entry.get('subcategory'), str)
        assert isinstance(entry.get('hours'), (int, float))
        assert isinstance(entry.get('created_at'), str)
        assert validate_timestamp(entry.get('created_at'))
        if entry.get('updated_at'):
            assert validate_timestamp(entry.get('updated_at'))

def test_customer_interface():
    """Test Customer interface matches API response"""
    response = client.get("/customers")
    assert response.status_code == 200
    customers = response.json()
    
    if customers:
        customer = customers[0]
        assert isinstance(customer.get('id'), (int, str))
        assert isinstance(customer.get('name'), str)
        assert isinstance(customer.get('created_at'), str)
        assert validate_timestamp(customer.get('created_at'))
        if customer.get('updated_at'):
            assert validate_timestamp(customer.get('updated_at'))

def test_project_interface():
    """Test Project interface matches API response"""
    response = client.get("/projects")
    assert response.status_code == 200
    projects = response.json()
    
    if projects:
        project = projects[0]
        assert isinstance(project.get('id'), (int, str))
        assert isinstance(project.get('name'), str)
        assert isinstance(project.get('project_id'), str)
        assert isinstance(project.get('customer'), str)
        project_manager = project.get('project_manager')
        assert project_manager is None or isinstance(project_manager, str)
        assert isinstance(project.get('created_at'), str)
        assert validate_timestamp(project.get('created_at'))
        if project.get('updated_at'):
            assert validate_timestamp(project.get('updated_at'))

def test_project_manager_interface():
    """Test ProjectManager interface matches API response"""
    response = client.get("/project-managers")
    assert response.status_code == 200
    managers = response.json()
    
    if managers:
        manager = managers[0]
        assert isinstance(manager.get('id'), (int, str))
        assert isinstance(manager.get('name'), str)
        assert isinstance(manager.get('created_at'), str)
        assert validate_timestamp(manager.get('created_at'))
        if manager.get('updated_at'):
            assert validate_timestamp(manager.get('updated_at'))

def test_database_status_interface():
    """Test DatabaseStatus interface matches API response"""
    response = client.get("/health")
    assert response.status_code == 200
    status = response.json()
    
    assert isinstance(status.get('status'), str)
    assert isinstance(status.get('timestamp'), str)
    assert validate_timestamp(status.get('timestamp'))

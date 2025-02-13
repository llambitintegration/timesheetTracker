import pytest
from utils.validators import normalize_customer_name, normalize_project_id, normalize_project_manager

def test_normalize_customer_name():
    """Test customer name normalization"""
    # Test empty/invalid values
    assert normalize_customer_name('-') is None
    assert normalize_customer_name(None) is None
    assert normalize_customer_name('') is None
    assert normalize_customer_name('None') is None
    assert normalize_customer_name('null') is None
    assert normalize_customer_name('NA') is None

    # Test valid customer names
    assert normalize_customer_name('Test Customer') == 'Test Customer'
    assert normalize_customer_name(' Test Customer ') == 'Test Customer'

def test_normalize_project_id():
    """Test project ID normalization"""
    # Test empty/invalid values
    assert normalize_project_id('-') is None
    assert normalize_project_id(None) is None
    assert normalize_project_id('') is None
    assert normalize_project_id('None') is None
    assert normalize_project_id('null') is None
    assert normalize_project_id('NA') is None

    # Test valid project IDs with spaces and hyphens
    assert normalize_project_id('Test Project') == 'Test_Project'
    assert normalize_project_id('Test-Project') == 'Test_Project'
    assert normalize_project_id(' Test  Project ') == 'Test__Project'

def test_normalize_project_manager():
    """Test project manager name normalization"""
    # Test empty/invalid values
    assert normalize_project_manager('-') is None
    assert normalize_project_manager(None) is None
    assert normalize_project_manager('') is None
    assert normalize_project_manager('None') is None
    assert normalize_project_manager('null') is None
    assert normalize_project_manager('NA') is None

    # Test valid project manager names
    assert normalize_project_manager('John Doe') == 'John Doe'
    assert normalize_project_manager(' John Doe ') == 'John Doe'
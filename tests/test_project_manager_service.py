import pytest
from services.project_manager_service import ProjectManagerService
from database.schemas import ProjectManagerCreate, ProjectManagerUpdate
from models.projectManagerModel import ProjectManager

def test_create_project_manager(db_session):
    """Test creating a project manager through service"""
    service = ProjectManagerService(db_session)
    pm_data = ProjectManagerCreate(
        name="Test Manager",
        email="test@example.com"
    )

    result = service.create_project_manager(pm_data)
    assert result is not None
    assert result.name == "Test Manager"
    assert result.email == "test@example.com"

def test_create_duplicate_project_manager(db_session):
    """Test attempting to create a project manager with duplicate email"""
    service = ProjectManagerService(db_session)
    pm_data = ProjectManagerCreate(
        name="Duplicate Test",
        email="duplicate@test.com"
    )

    # Create first project manager
    service.create_project_manager(pm_data)

    # Attempt to create duplicate
    with pytest.raises(ValueError) as exc_info:
        service.create_project_manager(pm_data)
    assert "Project manager with email duplicate@test.com already exists" in str(exc_info.value)

def test_get_project_manager(db_session):
    """Test retrieving a project manager by email"""
    service = ProjectManagerService(db_session)
    pm_data = ProjectManagerCreate(
        name="Get Test",
        email="get@test.com"
    )

    created = service.create_project_manager(pm_data)
    retrieved = service.get_project_manager("get@test.com")

    assert retrieved is not None
    assert retrieved.name == "Get Test"
    assert retrieved.email == "get@test.com"

def test_get_nonexistent_project_manager(db_session):
    """Test retrieving a non-existent project manager"""
    service = ProjectManagerService(db_session)
    result = service.get_project_manager("nonexistent@test.com")
    assert result is None

def test_get_all_project_managers(db_session):
    """Test retrieving all project managers with pagination"""
    service = ProjectManagerService(db_session)
    
    # Create multiple project managers
    pms = [
        ProjectManagerCreate(name=f"Test Manager {i}", email=f"test{i}@example.com")
        for i in range(3)
    ]
    for pm in pms:
        service.create_project_manager(pm)

    # Test without pagination
    all_pms = service.get_all_project_managers()
    assert len(all_pms) >= 3

    # Test with pagination
    page_1 = service.get_all_project_managers(skip=0, limit=2)
    assert len(page_1) == 2
    page_2 = service.get_all_project_managers(skip=2, limit=2)
    assert len(page_2) >= 1

def test_update_project_manager(db_session):
    """Test updating a project manager"""
    service = ProjectManagerService(db_session)
    pm_data = ProjectManagerCreate(
        name="Update Test",
        email="update@test.com"
    )

    created = service.create_project_manager(pm_data)
    update_data = ProjectManagerUpdate(name="Updated Name")
    updated = service.update_project_manager("update@test.com", update_data)

    assert updated is not None
    assert updated.name == "Updated Name"
    assert updated.email == "update@test.com"  # Unchanged field

def test_update_nonexistent_project_manager(db_session):
    """Test attempting to update a non-existent project manager"""
    service = ProjectManagerService(db_session)
    update_data = ProjectManagerUpdate(name="New Name")
    result = service.update_project_manager("nonexistent@test.com", update_data)
    assert result is None

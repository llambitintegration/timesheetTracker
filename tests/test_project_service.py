import pytest
from services.project_service import ProjectService
from database.schemas import ProjectCreate, ProjectBase
from models.projectModel import Project

def test_create_project(db_session):
    """Test creating a project through service"""
    service = ProjectService(db_session)
    project_data = ProjectCreate(
        project_id="TEST-001",
        name="Test Project",
        description="Test Description",
        customer="Test Customer",
        project_manager="Test Manager",
        status="active"
    )

    result = service.create_project(project_data)
    assert result is not None
    assert result.project_id == "TEST-001"
    assert result.name == "Test Project"
    assert result.status == "active"

def test_create_duplicate_project(db_session):
    """Test attempting to create a project with duplicate project_id"""
    service = ProjectService(db_session)
    project_data = ProjectCreate(
        project_id="DUP-001",
        name="Duplicate Test",
        description="Test Description",
        customer="Test Customer",
        project_manager="Test Manager"
    )

    # Create first project
    service.create_project(project_data)

    # Attempt to create duplicate
    with pytest.raises(ValueError) as exc_info:
        service.create_project(project_data)
    assert "Project with ID DUP-001 already exists" in str(exc_info.value)

def test_get_project(db_session):
    """Test retrieving a project by project_id"""
    service = ProjectService(db_session)
    project_data = ProjectCreate(
        project_id="GET-001",
        name="Get Test",
        description="Test Description",
        customer="Test Customer",
        project_manager="Test Manager"
    )

    created = service.create_project(project_data)
    retrieved = service.get_project("GET-001")

    assert retrieved is not None
    assert retrieved.project_id == "GET-001"
    assert retrieved.name == "Get Test"

def test_get_nonexistent_project(db_session):
    """Test retrieving a non-existent project"""
    service = ProjectService(db_session)
    result = service.get_project("NONEXISTENT-001")
    assert result is None

def test_get_all_projects(db_session):
    """Test retrieving all projects with pagination"""
    service = ProjectService(db_session)
    
    # Create multiple projects
    projects = [
        ProjectCreate(
            project_id=f"ALL-00{i}",
            name=f"Test Project {i}",
            description="Test Description",
            customer="Test Customer",
            project_manager="Test Manager"
        )
        for i in range(3)
    ]
    for project in projects:
        service.create_project(project)

    # Test without pagination
    all_projects = service.get_all_projects()
    assert len(all_projects) >= 3

    # Test with pagination
    page_1 = service.get_all_projects(skip=0, limit=2)
    assert len(page_1) == 2
    page_2 = service.get_all_projects(skip=2, limit=2)
    assert len(page_2) >= 1

def test_get_projects_by_customer(db_session):
    """Test retrieving projects by customer"""
    service = ProjectService(db_session)
    
    # Create project with specific customer
    project_data = ProjectCreate(
        project_id="CUST-001",
        name="Customer Test",
        description="Test Description",
        customer="Special Customer",
        project_manager="Test Manager"
    )
    service.create_project(project_data)

    # Test retrieval
    projects = service.get_projects_by_customer("Special Customer")
    assert len(projects) >= 1
    assert all(p.customer == "Special Customer" for p in projects)

def test_get_projects_by_manager(db_session):
    """Test retrieving projects by project manager"""
    service = ProjectService(db_session)
    
    # Create project with specific manager
    project_data = ProjectCreate(
        project_id="MGR-001",
        name="Manager Test",
        description="Test Description",
        customer="Test Customer",
        project_manager="Special Manager"
    )
    service.create_project(project_data)

    # Test retrieval
    projects = service.get_projects_by_manager("Special Manager")
    assert len(projects) >= 1
    assert all(p.project_manager == "Special Manager" for p in projects)

def test_update_project(db_session):
    """Test updating a project"""
    service = ProjectService(db_session)
    project_data = ProjectCreate(
        project_id="UPDATE-001",
        name="Update Test",
        description="Test Description",
        customer="Test Customer",
        project_manager="Test Manager"
    )

    created = service.create_project(project_data)
    update_data = ProjectBase(
        project_id="UPDATE-001",
        name="Updated Name",
        description="Updated Description",
        customer="Test Customer",
        project_manager="Test Manager"
    )
    updated = service.update_project("UPDATE-001", update_data)

    assert updated is not None
    assert updated.name == "Updated Name"
    assert updated.description == "Updated Description"
    assert updated.project_id == "UPDATE-001"  # Unchanged field

def test_update_nonexistent_project(db_session):
    """Test attempting to update a non-existent project"""
    service = ProjectService(db_session)
    update_data = ProjectBase(
        project_id="NONEXISTENT-001",
        name="New Name",
        description="New Description",
        customer="Test Customer",
        project_manager="Test Manager"
    )
    result = service.update_project("NONEXISTENT-001", update_data)
    assert result is None

def test_delete_project(db_session):
    """Test deleting a project"""
    service = ProjectService(db_session)
    project_data = ProjectCreate(
        project_id="DELETE-001",
        name="Delete Test",
        description="Test Description",
        customer="Test Customer",
        project_manager="Test Manager"
    )

    # Create and then delete
    service.create_project(project_data)
    result = service.delete_project("DELETE-001")
    assert result is True

    # Verify deletion
    deleted_project = service.get_project("DELETE-001")
    assert deleted_project is None

def test_delete_nonexistent_project(db_session):
    """Test attempting to delete a non-existent project"""
    service = ProjectService(db_session)
    result = service.delete_project("NONEXISTENT-001")
    assert result is False

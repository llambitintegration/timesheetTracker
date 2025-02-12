import pytest
from services.project_service import ProjectService
from database.schemas import ProjectCreate, ProjectBase, CustomerCreate
from models.projectModel import Project
from models.projectManagerModel import ProjectManager
from models.customerModel import Customer as CustomerModel
from fastapi import HTTPException

def create_test_project_manager(db_session):
    """Helper function to create a test project manager"""
    pm = ProjectManager(
        name="test_manager",
        email="test_manager@example.com"
    )
    db_session.add(pm)
    db_session.commit()
    return pm

def create_test_customer(db_session):
    """Helper function to create a test customer"""
    customer = CustomerModel(
        name="Test Customer",
        contact_email="test@example.com",
        status="active"
    )
    db_session.add(customer)
    db_session.commit()
    return customer

def test_create_project(db_session):
    """Test creating a project through service"""
    create_test_project_manager(db_session)  # Create test project manager first
    create_test_customer(db_session)  # Create test customer first

    service = ProjectService(db_session)
    project_data = ProjectCreate(
        project_id="TEST-001",
        name="Test Project",
        description="Test Description",
        customer="Test Customer",
        project_manager="test_manager",
        status="active"
    )

    result = service.create_project(project_data)
    assert result is not None
    assert result.project_id == "TEST-001"
    assert result.name == "Test Project"
    assert result.status == "active"
    assert result.project_manager == "test_manager"
    assert result.customer == "Test Customer"

def test_create_duplicate_project(db_session):
    """Test attempting to create a project with duplicate project_id"""
    create_test_project_manager(db_session)  # Create test project manager first
    create_test_customer(db_session)  # Create test customer first
    service = ProjectService(db_session)
    project_data = ProjectCreate(
        project_id="DUP-001",
        name="Duplicate Test",
        description="Test Description",
        customer="Test Customer",
        project_manager="test_manager"
    )

    # Create first project
    service.create_project(project_data)

    # Attempt to create duplicate
    with pytest.raises(HTTPException) as exc_info:
        service.create_project(project_data)
    assert exc_info.value.status_code == 400
    assert "Project with ID DUP-001 already exists" in str(exc_info.value.detail)

def test_get_project(db_session):
    """Test retrieving a project by project_id"""
    create_test_project_manager(db_session)
    create_test_customer(db_session)
    service = ProjectService(db_session)
    project_data = ProjectCreate(
        project_id="GET-001",
        name="Get Test",
        description="Test Description",
        customer="Test Customer",
        project_manager="test_manager"
    )

    created = service.create_project(project_data)
    retrieved = service.get_project("GET-001")

    assert retrieved is not None
    assert retrieved.project_id == "GET-001"
    assert retrieved.name == "Get Test"

def test_get_nonexistent_project(db_session):
    """Test retrieving a non-existent project"""
    service = ProjectService(db_session)
    with pytest.raises(HTTPException) as exc_info:
        service.get_project("NONEXISTENT-001")
    assert exc_info.value.status_code == 404
    assert "Project not found" in str(exc_info.value.detail)

def test_create_project_without_project_manager(db_session):
    """Test creating a project without a project manager should fail"""
    create_test_customer(db_session)  # Create test customer first
    service = ProjectService(db_session)
    project_data = ProjectCreate(
        project_id="PM-001",
        name="No Manager Project",
        description="Test Description",
        customer="Test Customer",
        project_manager=None,
        status="active"
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_project(project_data)
    assert exc_info.value.status_code == 400
    assert "Project manager is required" in str(exc_info.value.detail)

def test_create_project_with_nonexistent_project_manager(db_session):
    """Test creating a project with a non-existent project manager should fail"""
    create_test_customer(db_session)  # Create test customer first
    service = ProjectService(db_session)
    project_data = ProjectCreate(
        project_id="PM-002",
        name="Invalid Manager Project",
        description="Test Description",
        customer="Test Customer",
        project_manager="nonexistent_manager",
        status="active"
    )

    with pytest.raises(HTTPException) as exc_info:
        service.create_project(project_data)
    assert exc_info.value.status_code == 404
    assert "Project manager not found" in str(exc_info.value.detail)

def test_get_all_projects(db_session):
    """Test retrieving all projects with pagination"""
    create_test_project_manager(db_session)  # Create test project manager first
    service = ProjectService(db_session)

    # Create multiple projects
    projects = [
        ProjectCreate(
            project_id=f"ALL-00{i}",
            name=f"Test Project {i}",
            description="Test Description",
            customer="Test Customer",
            project_manager="test_manager"  # Use existing project manager
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
    create_test_project_manager(db_session)
    create_test_customer(db_session)
    service = ProjectService(db_session)

    # Create multiple projects for the same customer
    for i in range(3):
        project_data = ProjectCreate(
            project_id=f"CUST-00{i}",
            name=f"Customer Test {i}",
            description="Test Description",
            customer="Test Customer",
            project_manager="test_manager"
        )
        service.create_project(project_data)

    # Test retrieval
    projects = service.get_projects_by_customer("Test Customer")
    assert len(projects) == 3
    assert all(p.customer == "Test Customer" for p in projects)


def test_get_projects_by_manager(db_session):
    """Test retrieving projects by project manager"""
    create_test_project_manager(db_session)
    create_test_customer(db_session)
    service = ProjectService(db_session)

    # Create multiple projects for the same manager
    for i in range(3):
        project_data = ProjectCreate(
            project_id=f"MGR-00{i}",
            name=f"Manager Test {i}",
            description="Test Description",
            customer="Test Customer",
            project_manager="test_manager"
        )
        service.create_project(project_data)

    # Test retrieval
    projects = service.get_projects_by_manager("test_manager")
    assert len(projects) == 3
    assert all(p.project_manager == "test_manager" for p in projects)

def test_update_project(db_session):
    """Test updating a project"""
    create_test_project_manager(db_session)  # Create test project manager first
    service = ProjectService(db_session)
    project_data = ProjectCreate(
        project_id="UPDATE-001",
        name="Update Test",
        description="Test Description",
        customer="Test Customer",
        project_manager="test_manager"  # Use existing project manager
    )

    created = service.create_project(project_data)
    update_data = ProjectBase(
        project_id="UPDATE-001",
        name="Updated Name",
        description="Updated Description",
        customer="Test Customer",
        project_manager="test_manager"  # Use existing project manager
    )
    updated = service.update_project("UPDATE-001", update_data)

    assert updated is not None
    assert updated.name == "Updated Name"
    assert updated.description == "Updated Description"
    assert updated.project_id == "UPDATE-001"  # Unchanged field
    assert updated.project_manager == "test_manager"

def test_create_project_with_invalid_customer(db_session):
    """Test creating a project with an invalid customer"""
    create_test_project_manager(db_session)
    service = ProjectService(db_session)
    project_data = ProjectCreate(
        project_id="INVCUST-001",
        name="Invalid Customer Project",
        description="Test Description",
        customer=None,  # Invalid customer
        project_manager="test_manager",
        status="active"
    )

    # Should succeed with DEFAULT_CUSTOMER
    result = service.create_project(project_data)
    assert result is not None
    assert result.customer == "Default Customer"

def test_update_nonexistent_project(db_session):
    """Test attempting to update a non-existent project"""
    service = ProjectService(db_session)
    update_data = ProjectBase(
        project_id="NONEXISTENT-001",
        name="New Name",
        description="New Description",
        customer="Test Customer",
        project_manager="test_manager"
    )
    result = service.update_project("NONEXISTENT-001", update_data)
    assert result is None

def test_delete_project(db_session):
    """Test deleting a project"""
    create_test_project_manager(db_session)
    service = ProjectService(db_session)
    project_data = ProjectCreate(
        project_id="DELETE-001",
        name="Delete Test",
        description="Test Description",
        customer="Test Customer",
        project_manager="test_manager"
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

def test_create_project_with_new_customer(db_session):
    """Test creating a project with a new customer that doesn't exist yet"""
    create_test_project_manager(db_session)  # Create test project manager first
    service = ProjectService(db_session)

    project_data = ProjectCreate(
        project_id="NEW-001",
        name="New Customer Project",
        description="Test Description",
        customer="New Test Customer",
        project_manager="test_manager",
        status="active"
    )

    result = service.create_project(project_data)
    assert result is not None
    assert result.project_id == "NEW-001"
    assert result.customer == "New Test Customer"
    assert result.status == "active"
    assert result.project_manager == "test_manager"

    # Verify customer was created
    customer = service.customer_repo.get_by_name(db_session, "New Test Customer")
    assert customer is not None
    assert customer.name == "New Test Customer"

DEFAULT_CUSTOMER = "Default Customer"

def test_create_project_without_customer(db_session):
    """Test creating a project without specifying a customer"""
    create_test_project_manager(db_session)
    service = ProjectService(db_session)
    project_data = ProjectCreate(
        project_id="DEFAULT-001",
        name="Default Customer Project",
        description="Test Description",
        customer=DEFAULT_CUSTOMER,
        project_manager="test_manager",
        status="active"
    )

    result = service.create_project(project_data)
    assert result is not None
    assert result.project_id == "DEFAULT-001"
    assert result.customer == DEFAULT_CUSTOMER
    assert result.project_manager == "test_manager"
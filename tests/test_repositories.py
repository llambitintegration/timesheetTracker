import pytest
from sqlalchemy.exc import IntegrityError
from database.customer_repository import CustomerRepository
from database.timesheet_repository import TimeEntryRepository
from models.customerModel import Customer
from models.timeEntry import TimeEntry
from datetime import date
from database.project_repository import ProjectRepository # Assuming this exists
from models.projectModel import Project # Assuming this exists


def test_customer_repository_create(db_session):
    """Test creating a customer through repository"""
    repo = CustomerRepository()
    customer = Customer(
        name="Test Customer",
        contact_email="test@example.com",
        industry="Technology"
    )

    result = repo.create(db_session, customer)
    assert result is not None
    assert result.name == "Test Customer"
    assert result.contact_email == "test@example.com"
    assert result.id is not None


def test_customer_repository_get_by_id(db_session):
    """Test retrieving a customer by ID"""
    repo = CustomerRepository()
    customer = Customer(
        name="Get By ID Test",
        contact_email="getbyid@test.com"
    )

    created = repo.create(db_session, customer)
    retrieved = repo.get_by_id(db_session, created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.name == "Get By ID Test"


def test_customer_repository_get_by_name(db_session):
    """Test retrieving a customer by name"""
    repo = CustomerRepository()
    customer = Customer(
        name="Get By Name Test",
        contact_email="getbyname@test.com"
    )

    repo.create(db_session, customer)
    retrieved = repo.get_by_name(db_session, "Get By Name Test")

    assert retrieved is not None
    assert retrieved.name == "Get By Name Test"
    assert retrieved.contact_email == "getbyname@test.com"


def test_customer_repository_get_all(db_session):
    """Test retrieving all customers"""
    repo = CustomerRepository()
    customers = [
        Customer(name="All Test 1", contact_email="all1@test.com"),
        Customer(name="All Test 2", contact_email="all2@test.com"),
        Customer(name="All Test 3", contact_email="all3@test.com")
    ]

    for customer in customers:
        repo.create(db_session, customer)

    all_customers = repo.get_all(db_session)
    assert len(all_customers) >= 3  # May include existing customers from other tests
    assert any(c.name == "All Test 1" for c in all_customers)
    assert any(c.name == "All Test 2" for c in all_customers)
    assert any(c.name == "All Test 3" for c in all_customers)


def test_customer_repository_update(db_session):
    """Test updating a customer"""
    repo = CustomerRepository()
    customer = Customer(
        name="Update Test",
        contact_email="update@test.com",
        industry="Old Industry"
    )

    created = repo.create(db_session, customer)
    created.industry = "New Industry"
    updated = repo.update(db_session, created)

    assert updated is not None
    assert updated.industry == "New Industry"
    retrieved = repo.get_by_id(db_session, created.id)
    assert retrieved is not None
    assert retrieved.industry == "New Industry"


def test_customer_repository_delete(db_session):
    """Test deleting a customer"""
    repo = CustomerRepository()
    customer = Customer(
        name="Delete Test",
        contact_email="delete@test.com"
    )

    created = repo.create(db_session, customer)
    assert repo.get_by_id(db_session, created.id) is not None

    repo.delete(db_session, created.id)
    assert repo.get_by_id(db_session, created.id) is None


def test_customer_repository_unique_name_constraint(db_session):
    """Test that customer names must be unique"""
    repo = CustomerRepository()
    customer1 = Customer(
        name="Unique Test",
        contact_email="unique1@test.com"
    )
    customer2 = Customer(
        name="Unique Test",  # Same name as customer1
        contact_email="unique2@test.com"
    )

    repo.create(db_session, customer1)
    with pytest.raises(IntegrityError):
        repo.create(db_session, customer2)


def test_customer_repository_pagination(db_session):
    """Test repository pagination"""
    repo = CustomerRepository()
    # Create 5 customers
    for i in range(5):
        customer = Customer(
            name=f"Page Test {i}",
            contact_email=f"page{i}@test.com"
        )
        repo.create(db_session, customer)

    # Test first page (2 items)
    page1 = repo.get_all(db_session, skip=0, limit=2)
    assert len(page1) == 2

    # Test second page (2 items)
    page2 = repo.get_all(db_session, skip=2, limit=2)
    assert len(page2) == 2

    # Test last page (1 item)
    page3 = repo.get_all(db_session, skip=4, limit=2)
    assert len(page3) == 1


def test_time_entry_repository_create(db_session):
    """Test creating a time entry through repository"""
    # First create a customer
    customer_repo = CustomerRepository()
    project_repo = ProjectRepository()
    customer = Customer(
        name="TestCustomer",
        contact_email="test@customer.com"
    )
    created_customer = customer_repo.create(db_session, customer)

    # Create a project first
    project = Project(
        project_id="TEST_CREATE_001",
        name="Test Create Project",
        customer=created_customer.name,
        status="active"
    )
    created_project = project_repo.create(db_session, project)

    # Then create the time entry
    repo = TimeEntryRepository()
    entry = TimeEntry(
        week_number=1,
        month="January",
        category="Development",
        subcategory="Coding",
        customer=created_customer.name,  # Use the created customer's name
        project=created_project.project_id,
        task_description="Test entry",
        hours=8.0,
        date=date(2024, 1, 1)
    )

    result = repo.create(db_session, entry)
    assert result is not None
    assert result.customer == created_customer.name
    assert result.project == created_project.project_id
    assert result.hours == 8.0
    assert result.id is not None


def test_time_entry_repository_get_by_id(db_session):
    """Test retrieving a time entry by ID"""
    # First create a customer
    customer_repo = CustomerRepository()
    project_repo = ProjectRepository()
    customer = Customer(
        name="TestCustomer",
        contact_email="test@customer.com"
    )
    created_customer = customer_repo.create(db_session, customer)

    # Create a project first
    project = Project(
        project_id="TEST_GET_001",
        name="Test Get Project",
        customer=created_customer.name,
        status="active"
    )
    created_project = project_repo.create(db_session, project)

    repo = TimeEntryRepository()
    entry = TimeEntry(
        week_number=1,
        month="January",
        category="Development",
        subcategory="Coding",
        customer=created_customer.name,
        project=created_project.project_id,
        task_description="Test entry",
        hours=8.0,
        date=date(2024, 1, 1)
    )

    created = repo.create(db_session, entry)
    retrieved = repo.get_by_id(db_session, created.id)

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.customer == created_customer.name
    assert retrieved.project == created_project.project_id


def test_time_entry_repository_get_by_date(db_session):
    """Test retrieving time entries by date"""
    # First create a customer
    customer_repo = CustomerRepository()
    project_repo = ProjectRepository()
    customer = Customer(
        name="TestCustomer",
        contact_email="test@customer.com"
    )
    created_customer = customer_repo.create(db_session, customer)

    # Create a project first
    project = Project(
        project_id="TEST_DATE_001",
        name="Test Date Project",
        customer=created_customer.name,
        status="active"
    )
    created_project = project_repo.create(db_session, project)

    repo = TimeEntryRepository()
    entry_date = date(2024, 1, 1)
    entry = TimeEntry(
        week_number=1,
        month="January",
        category="Development",
        subcategory="Coding",
        customer=created_customer.name,
        project=created_project.project_id,
        task_description="Test entry",
        hours=8.0,
        date=entry_date
    )

    repo.create(db_session, entry)
    entries = repo.get_by_date(db_session, entry_date)

    assert len(entries) == 1
    assert entries[0].date == entry_date
    assert entries[0].customer == created_customer.name


def test_time_entry_repository_get_all(db_session):
    """Test retrieving all time entries"""
    # First create a customer
    customer_repo = CustomerRepository()
    project_repo = ProjectRepository()
    customer = Customer(
        name="TestCustomer",
        contact_email="test@customer.com"
    )
    created_customer = customer_repo.create(db_session, customer)

    # Create a project first
    project = Project(
        project_id="TEST_ALL_001",
        name="Test All Project",
        customer=created_customer.name,
        status="active"
    )
    created_project = project_repo.create(db_session, project)

    repo = TimeEntryRepository()
    entries = [
        TimeEntry(
            week_number=1,
            month="January",
            category="Development",
            subcategory="Coding",
            customer=created_customer.name,
            project=created_project.project_id,
            task_description=f"Entry {i}",
            hours=8.0,
            date=date(2024, 1, 1)
        ) for i in range(3)
    ]

    for entry in entries:
        repo.create(db_session, entry)

    all_entries = repo.get_all(db_session)
    assert len(all_entries) >= 3
    assert any(e.customer == created_customer.name and e.project == created_project.project_id for e in all_entries)



def test_time_entry_repository_update(db_session):
    """Test updating a time entry"""
    # First create a customer
    customer_repo = CustomerRepository()
    project_repo = ProjectRepository()
    customer = Customer(
        name="TestCustomer",
        contact_email="test@customer.com"
    )
    created_customer = customer_repo.create(db_session, customer)

    # Create a project first
    project = Project(
        project_id="TEST_UPDATE_001",
        name="Test Update Project",
        customer=created_customer.name,
        status="active"
    )
    created_project = project_repo.create(db_session, project)

    # Then create the time entry
    repo = TimeEntryRepository()
    entry = TimeEntry(
        week_number=1,
        month="January",
        category="Development",
        subcategory="Coding",
        customer=created_customer.name,
        project=created_project.project_id,
        task_description="Original description",
        hours=8.0,
        date=date(2024, 1, 1)
    )

    created = repo.create(db_session, entry)
    created.task_description = "Updated description"
    created.hours = 4.0
    updated = repo.update(db_session, created)

    assert updated is not None
    assert updated.task_description == "Updated description"
    assert updated.hours == 4.0
    retrieved = repo.get_by_id(db_session, created.id)
    assert retrieved is not None
    assert retrieved.task_description == "Updated description"
    assert retrieved.hours == 4.0


def test_time_entry_repository_delete(db_session):
    """Test deleting a time entry"""
    # First create a customer
    customer_repo = CustomerRepository()
    project_repo = ProjectRepository()
    customer = Customer(
        name="TestCustomer",
        contact_email="test@customer.com"
    )
    created_customer = customer_repo.create(db_session, customer)

    # Create a project first
    project = Project(
        project_id="TEST_DELETE_001",
        name="Test Delete Project",
        customer=created_customer.name,
        status="active"
    )
    created_project = project_repo.create(db_session, project)

    repo = TimeEntryRepository()
    entry = TimeEntry(
        week_number=1,
        month="January",
        category="Development",
        subcategory="Coding",
        customer=created_customer.name,
        project=created_project.project_id,
        task_description="Test entry",
        hours=8.0,
        date=date(2024, 1, 1)
    )

    created = repo.create(db_session, entry)
    assert repo.get_by_id(db_session, created.id) is not None

    repo.delete(db_session, created.id)
    assert repo.get_by_id(db_session, created.id) is None


def test_time_entry_repository_pagination(db_session):
    """Test time entry repository pagination"""
    # First create a customer
    customer_repo = CustomerRepository()
    project_repo = ProjectRepository()
    customer = Customer(
        name="TestCustomer",
        contact_email="test@customer.com"
    )
    created_customer = customer_repo.create(db_session, customer)

    # Create a project first
    project = Project(
        project_id="TEST_PAGE_001",
        name="Test Pagination Project",
        customer=created_customer.name,
        status="active"
    )
    created_project = project_repo.create(db_session, project)

    repo = TimeEntryRepository()
    # Create 5 time entries
    for i in range(5):
        entry = TimeEntry(
            week_number=1,
            month="January",
            category="Development",
            subcategory="Coding",
            customer=created_customer.name,
            project=created_project.project_id,
            task_description=f"Entry {i}",
            hours=8.0,
            date=date(2024, 1, 1)
        )
        repo.create(db_session, entry)

    # Test first page (2 items)
    page1 = repo.get_all(db_session, skip=0, limit=2)
    assert len(page1) == 2

    # Test second page (2 items)
    page2 = repo.get_all(db_session, skip=2, limit=2)
    assert len(page2) == 2

    # Test last page (1 item)
    page3 = repo.get_all(db_session, skip=4, limit=2)
    assert len(page3) == 1


def test_customer_cascade_delete_behavior(db_session):
    """Test that deleting a customer properly handles related records."""
    # Create repositories
    customer_repo = CustomerRepository()
    project_repo = ProjectRepository()
    time_entry_repo = TimeEntryRepository()

    # Create a test customer
    customer = Customer(
        name="Cascade Test Customer",
        contact_email="cascade@test.com",
        industry="Technology"  # Added required field
    )
    created_customer = customer_repo.create(db_session, customer)

    # Create a project for this customer
    project = Project(
        project_id="CASCADE_TEST_001",
        name="Cascade Test Project",
        customer=created_customer.name,
        status="active",
        description="Test project for cascade delete"  # Added required field
    )
    created_project = project_repo.create(db_session, project)

    # Create a time entry for this project
    entry = TimeEntry(
        date=date(2024, 1, 1),
        customer=created_customer.name,
        project=created_project.project_id,
        hours=8.0,
        category="Test",
        subcategory="Cascade",
        task_description="Testing cascade delete",
        week_number=1,
        month="January"
    )
    created_entry = time_entry_repo.create(db_session, entry)

    # Delete the customer
    customer_repo.delete(db_session, created_customer.id)

    # Verify project still exists but customer is NULL
    updated_project = project_repo.get_by_project_id(db_session, created_project.project_id)
    assert updated_project is not None, "Project should still exist after customer deletion"
    assert updated_project.customer is None, "Project's customer should be set to NULL"

    # Verify time entry still exists but customer is NULL
    updated_entry = time_entry_repo.get_by_id(db_session, created_entry.id)
    assert updated_entry is not None, "Time entry should still exist after customer deletion"
    assert updated_entry.customer is None, "Time entry's customer should be set to NULL"


def test_customer_name_update_cascade(db_session):
    """Test that updating a customer name cascades to related records."""
    # Create repositories
    customer_repo = CustomerRepository()
    project_repo = ProjectRepository()
    time_entry_repo = TimeEntryRepository()

    # Create a test customer
    customer = Customer(
        name="Update Cascade Test",
        contact_email="updatecascade@test.com",
        industry="Technology"  # Added required field
    )
    created_customer = customer_repo.create(db_session, customer)

    # Create a project for this customer
    project = Project(
        project_id="CASCADE_UPDATE_001",
        name="Update Cascade Test Project",
        customer=created_customer.name,
        status="active",
        description="Test project for cascade update"  # Added required field
    )
    created_project = project_repo.create(db_session, project)

    # Create a time entry
    entry = TimeEntry(
        date=date(2024, 1, 1),
        customer=created_customer.name,
        project=created_project.project_id,
        hours=8.0,
        category="Test",
        subcategory="Cascade",
        task_description="Testing cascade update",
        week_number=1,
        month="January"
    )
    created_entry = time_entry_repo.create(db_session, entry)

    # Update customer name
    created_customer.name = "Updated Customer Name"
    updated_customer = customer_repo.update(db_session, created_customer)

    # Verify cascade updates
    updated_project = project_repo.get_by_project_id(db_session, created_project.project_id)
    assert updated_project.customer == "Updated Customer Name"

    updated_entry = time_entry_repo.get_by_id(db_session, created_entry.id)
    assert updated_entry.customer == "Updated Customer Name"
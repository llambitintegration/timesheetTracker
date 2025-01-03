
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import calendar
from typing import List, Optional
import models
from . import schemas
from logger import Logger

logger = Logger().get_logger()

# Customer operations
def create_customer(db: Session, customer: schemas.CustomerCreate) -> models.Customer:
    """Create a new customer in the database."""
    try:
        logger.debug(f"Attempting to create customer with data: {customer.dict()}")
        db_customer = models.Customer(**customer.dict())
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        logger.info(f"Successfully created customer: {customer.name} in {customer.location}")
        return db_customer
    except Exception as e:
        logger.error(f"Error creating customer {customer.name}: {str(e)}")
        db.rollback()
        raise

def get_customer(db: Session, name: str) -> Optional[models.Customer]:
    """Retrieve a customer by name."""
    logger.debug(f"Attempting to fetch customer with name: {name}")
    customer = db.query(models.Customer).filter(models.Customer.name == name).first()
    if customer:
        logger.info(f"Found customer: {name}")
    else:
        logger.info(f"No customer found with name: {name}")
    return customer

def get_customers(db: Session, skip: int = 0, limit: int = 100) -> List[models.Customer]:
    """Retrieve a list of customers with pagination."""
    logger.debug(f"Fetching customers with offset={skip}, limit={limit}")
    customers = db.query(models.Customer).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(customers)} customers")
    return customers

# Project Manager operations
def create_project_manager(db: Session, project_manager: schemas.ProjectManagerCreate) -> models.ProjectManager:
    """Create a new project manager."""
    try:
        logger.debug(f"Creating project manager with data: {project_manager.dict()}")
        db_project_manager = models.ProjectManager(**project_manager.dict())
        db.add(db_project_manager)
        db.commit()
        db.refresh(db_project_manager)
        logger.info(f"Successfully created project manager: {project_manager.name}")
        return db_project_manager
    except Exception as e:
        logger.error(f"Error creating project manager {project_manager.name}: {str(e)}")
        db.rollback()
        raise

def get_project_manager(db: Session, name: str) -> Optional[models.ProjectManager]:
    """Retrieve a project manager by name."""
    logger.debug(f"Attempting to fetch project manager: {name}")
    manager = db.query(models.ProjectManager).filter(models.ProjectManager.name == name).first()
    if manager:
        logger.info(f"Found project manager: {name}")
    else:
        logger.info(f"No project manager found with name: {name}")
    return manager

def get_project_managers(db: Session, skip: int = 0, limit: int = 100) -> List[models.ProjectManager]:
    """Retrieve a list of project managers with pagination."""
    logger.debug(f"Fetching project managers with offset={skip}, limit={limit}")
    managers = db.query(models.ProjectManager).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(managers)} project managers")
    return managers

# Project operations
def create_project(db: Session, project: schemas.ProjectCreate) -> models.Project:
    """Create a new project."""
    try:
        logger.debug(f"Creating project with data: {project.dict()}")
        db_project = models.Project(**project.dict())
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        logger.info(f"Successfully created project: {project.project_id}")
        return db_project
    except Exception as e:
        logger.error(f"Error creating project {project.project_id}: {str(e)}")
        db.rollback()
        raise

def get_project(db: Session, project_id: str) -> Optional[models.Project]:
    """Retrieve a project by ID."""
    logger.debug(f"Attempting to fetch project: {project_id}")
    project = db.query(models.Project).filter(models.Project.project_id == project_id).first()
    if project:
        logger.info(f"Found project: {project_id}")
    else:
        logger.info(f"No project found with ID: {project_id}")
    return project

def get_projects(
    db: Session,
    customer_name: Optional[str] = None,
    project_manager_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.Project]:
    """Retrieve a list of projects with optional filtering and pagination."""
    logger.debug(
        f"Fetching projects with filters: customer={customer_name}, "
        f"manager={project_manager_name}, skip={skip}, limit={limit}"
    )
    query = db.query(models.Project)
    if customer_name:
        query = query.filter(models.Project.customer_name == customer_name)
    if project_manager_name:
        query = query.filter(models.Project.project_manager_name == project_manager_name)
    
    projects = query.offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(projects)} projects")
    return projects

# Time Entry operations
def create_time_entry(db: Session, entry: schemas.TimeEntryCreate) -> models.TimeEntry:
    """Create a new time entry."""
    try:
        logger.debug(f"Creating time entry with data: {entry.dict()}")
        db_entry = models.TimeEntry(**entry.dict())
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        logger.info(
            f"Successfully created time entry for {entry.customer} - "
            f"{entry.project} ({entry.hours} hours)"
        )
        return db_entry
    except Exception as e:
        logger.error(f"Error creating time entry: {str(e)}")
        db.rollback()
        raise

def get_time_entry(db: Session, entry_id: int) -> Optional[models.TimeEntry]:
    """Retrieve a time entry by ID."""
    logger.debug(f"Attempting to fetch time entry: {entry_id}")
    entry = db.query(models.TimeEntry).filter(models.TimeEntry.id == entry_id).first()
    if entry:
        logger.info(f"Found time entry: {entry_id}")
    else:
        logger.info(f"No time entry found with ID: {entry_id}")
    return entry

def get_time_entries(
    db: Session,
    project_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.TimeEntry]:
    """Retrieve time entries with optional filtering and pagination."""
    logger.debug(
        f"Fetching time entries with filters: project={project_id}, "
        f"customer={customer_name}, skip={skip}, limit={limit}"
    )
    query = db.query(models.TimeEntry)
    if project_id:
        query = query.filter(models.TimeEntry.project == project_id)
    if customer_name:
        query = query.filter(models.TimeEntry.customer == customer_name)
    
    entries = query.offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(entries)} time entries")
    return entries

def update_time_entry(
    db: Session,
    entry_id: int,
    entry: schemas.TimeEntryUpdate
) -> Optional[models.TimeEntry]:
    """Update an existing time entry."""
    logger.debug(f"Attempting to update time entry {entry_id} with data: {entry.dict(exclude_unset=True)}")
    db_entry = db.query(models.TimeEntry).filter(models.TimeEntry.id == entry_id).first()
    if db_entry:
        try:
            update_data = entry.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_entry, key, value)
            db.commit()
            db.refresh(db_entry)
            logger.info(f"Successfully updated time entry: {entry_id}")
            return db_entry
        except Exception as e:
            logger.error(f"Error updating time entry {entry_id}: {str(e)}")
            db.rollback()
            raise
    else:
        logger.warning(f"Attempted to update non-existent time entry: {entry_id}")
        return None

def delete_time_entry(db: Session, entry_id: int) -> bool:
    """Delete a time entry."""
    logger.debug(f"Attempting to delete time entry: {entry_id}")
    db_entry = db.query(models.TimeEntry).filter(models.TimeEntry.id == entry_id).first()
    if db_entry:
        try:
            db.delete(db_entry)
            db.commit()
            logger.info(f"Successfully deleted time entry: {entry_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting time entry {entry_id}: {str(e)}")
            db.rollback()
            raise
    logger.warning(f"Attempted to delete non-existent time entry: {entry_id}")
    return False

def get_weekly_report(
    db: Session,
    employee_id: Optional[str],
    date: datetime
) -> tuple[List, datetime, datetime]:
    """Generate a weekly report."""
    logger.debug(f"Generating weekly report for employee {employee_id}, date: {date}")
    week_start = date - timedelta(days=date.weekday())
    week_end = week_start + timedelta(days=6)
    
    query = db.query(
        models.TimeEntry.employee_id,
        models.TimeEntry.project,
        db.func.sum(models.TimeEntry.hours).label('total_hours')
    ).filter(
        models.TimeEntry.date >= week_start,
        models.TimeEntry.date <= week_end
    ).group_by(
        models.TimeEntry.employee_id,
        models.TimeEntry.project
    )
    
    if employee_id:
        query = query.filter(models.TimeEntry.employee_id == employee_id)
    
    results = query.all()
    logger.info(f"Generated weekly report with {len(results)} entries")
    return results, week_start, week_end

def get_monthly_report(
    db: Session,
    employee_id: Optional[str],
    year: int,
    month: int
) -> List:
    """Generate a monthly report."""
    logger.debug(f"Generating monthly report for employee {employee_id}, {year}-{month}")
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, calendar.monthrange(year, month)[1])
    
    query = db.query(
        models.TimeEntry.employee_id,
        models.TimeEntry.project,
        db.func.sum(models.TimeEntry.hours).label('total_hours')
    ).filter(
        models.TimeEntry.date >= start_date,
        models.TimeEntry.date <= end_date
    ).group_by(
        models.TimeEntry.employee_id,
        models.TimeEntry.project
    )
    
    if employee_id:
        query = query.filter(models.TimeEntry.employee_id == employee_id)
    
    results = query.all()
    logger.info(f"Generated monthly report with {len(results)} entries")
    return results

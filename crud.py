from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import calendar
from typing import List, Optional
import models, schemas
from logger import Logger

logger = Logger().get_logger()

# Customer operations
def create_customer(db: Session, customer: schemas.CustomerCreate):
    try:
        db_customer = models.Customer(**customer.dict())
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        logger.info(f"Successfully created customer: {customer.name}")
        return db_customer
    except Exception as e:
        logger.error(f"Error creating customer {customer.name}: {str(e)}")
        raise

def get_customer(db: Session, name: str):
    return db.query(models.Customer).filter(models.Customer.name == name).first()

def get_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Customer).offset(skip).limit(limit).all()

# Project Manager operations
def create_project_manager(db: Session, project_manager: schemas.ProjectManagerCreate):
    db_project_manager = models.ProjectManager(**project_manager.dict())
    db.add(db_project_manager)
    db.commit()
    db.refresh(db_project_manager)
    return db_project_manager

def get_project_manager(db: Session, name: str):
    return db.query(models.ProjectManager).filter(models.ProjectManager.name == name).first()

def get_project_managers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ProjectManager).offset(skip).limit(limit).all()

# Project operations
def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def get_project(db: Session, project_id: str):
    return db.query(models.Project).filter(models.Project.project_id == project_id).first()

def get_projects(
    db: Session,
    customer_name: Optional[str] = None,
    project_manager_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(models.Project)
    if customer_name:
        query = query.filter(models.Project.customer_name == customer_name)
    if project_manager_name:
        query = query.filter(models.Project.project_manager_name == project_manager_name)
    return query.offset(skip).limit(limit).all()

# Time Entry operations
def create_time_entry(db: Session, entry: schemas.TimeEntryCreate):
    db_entry = models.TimeEntry(**entry.dict())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

def get_time_entry(db: Session, entry_id: int):
    return db.query(models.TimeEntry).filter(models.TimeEntry.id == entry_id).first()

def get_time_entries(
    db: Session,
    project_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(models.TimeEntry)
    if project_id:
        query = query.filter(models.TimeEntry.project_id == project_id)
    if customer_name:
        query = query.filter(models.TimeEntry.customer_name == customer_name)
    return query.offset(skip).limit(limit).all()

def update_time_entry(db: Session, entry_id: int, entry: schemas.TimeEntryUpdate):
    db_entry = db.query(models.TimeEntry).filter(models.TimeEntry.id == entry_id).first()
    if db_entry:
        update_data = entry.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_entry, key, value)
        db.commit()
        db.refresh(db_entry)
    return db_entry

def delete_time_entry(db: Session, entry_id: int):
    db_entry = db.query(models.TimeEntry).filter(models.TimeEntry.id == entry_id).first()
    if db_entry:
        db.delete(db_entry)
        db.commit()
        return True
    return False

def get_weekly_report(db: Session, employee_id: Optional[str], date: datetime):
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
    return results, week_start, week_end

def get_monthly_report(db: Session, employee_id: Optional[str], year: int, month: int):
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
    
    return query.all()
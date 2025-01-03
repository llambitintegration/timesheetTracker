from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import calendar
from typing import List, Optional
import models, schemas

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
    employee_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(models.TimeEntry)
    if employee_id:
        query = query.filter(models.TimeEntry.employee_id == employee_id)
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
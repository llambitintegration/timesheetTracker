from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, date
from models.timeEntry import TimeEntry
from .base_repository import BaseRepository

class TimeEntryRepository(BaseRepository[TimeEntry]):
    def __init__(self):
        super().__init__(TimeEntry)

    def get_by_id(self, db: Session, id: int) -> Optional[TimeEntry]:
        """Get a time entry by ID."""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_by_date(self, db: Session, entry_date: date) -> List[TimeEntry]:
        """Get all time entries for a specific date."""
        return db.query(self.model).filter(self.model.date == entry_date).all()

    def get_by_project(self, db: Session, project_id: str) -> List[TimeEntry]:
        """Get all time entries for a specific project."""
        return db.query(self.model).filter(self.model.project == project_id).all()

    def get_by_customer(self, db: Session, customer_name: str) -> List[TimeEntry]:
        """Get all time entries for a specific customer."""
        return db.query(self.model).filter(self.model.customer == customer_name).all()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[TimeEntry]:
        """Get all time entries with pagination."""
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, entry: TimeEntry) -> TimeEntry:
        """Create a new time entry."""
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def update(self, db: Session, entry: TimeEntry) -> TimeEntry:
        """Update an existing time entry."""
        db.merge(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def delete(self, db: Session, id: int) -> bool:
        """Delete a time entry by ID."""
        entry = self.get_by_id(db, id)
        if entry:
            db.delete(entry)
            db.commit()
            return True
        return False
from typing import List, Optional, Dict, Any, BinaryIO
from sqlalchemy.orm import Session
from datetime import datetime, date
from models.timeEntry import TimeEntry
from database import schemas
from .base_repository import BaseRepository
from utils.xls_analyzer import XLSAnalyzer
from utils.logger import Logger

logger = Logger().get_logger()

class TimeEntryRepository(BaseRepository[TimeEntry]):
    def __init__(self):
        super().__init__(TimeEntry)

    def create(self, db: Session, data: schemas.TimeEntryCreate) -> TimeEntry:
        """Create a new time entry from Pydantic model."""
        if isinstance(data, TimeEntry):
            db_entry = data
        else:
            entry_dict = data.model_dump(exclude={'id', 'created_at', 'updated_at'})
            db_entry = TimeEntry(**entry_dict)
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)
        return db_entry

    def bulk_create(self, db: Session, entries: List[schemas.TimeEntryCreate]) -> List[TimeEntry]:
        """Bulk create time entries from list of Pydantic models."""
        db_entries = [
            TimeEntry(**entry.model_dump(exclude={'id', 'created_at', 'updated_at'}))
            for entry in entries
        ]
        db.add_all(db_entries)
        db.commit()
        for entry in db_entries:
            db.refresh(entry)
        return db_entries

    def update(self, db: Session, entry: TimeEntry, data: Dict[str, Any]) -> TimeEntry:
        """Update an existing time entry with dictionary data."""
        for key, value in data.items():
            setattr(entry, key, value)
        db.commit()
        db.refresh(entry)
        return entry

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

    def delete(self, db: Session, id: int) -> bool:
        """Delete a time entry by ID."""
        entry = self.get_by_id(db, id)
        if entry:
            db.delete(entry)

    def import_excel(self, db: Session, file_contents: bytes) -> List[TimeEntry]:
        """Import time entries from Excel file."""
        try:
            analyzer = XLSAnalyzer()
            records = analyzer.read_excel(file_contents)
            
            entries = []
            for record in records:
                entry_data = schemas.TimeEntryCreate(
                    date=record['Date'].date(),
                    week_number=int(record['Week Number']),
                    month=record['Month'],
                    category=record['Category'],
                    subcategory=record['Subcategory'],
                    customer=record['Customer'],
                    project=record['Project'],
                    task_description=record['Task Description'],
                    hours=float(record.get('Hours', 0))
                )
                entries.append(entry_data)

            # Use bulk create for better performance
            return self.bulk_create(db, entries)
            
        except Exception as e:
            logger.error(f"Error importing Excel data: {str(e)}")
            raise

            db.commit()
            return True
        return False
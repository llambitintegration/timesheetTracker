from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException
from datetime import datetime, date
from database import schemas
from models.timeEntry import TimeEntry
from utils.logger import Logger
from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT, normalize_customer_name, normalize_project_id
from database.customer_repository import CustomerRepository
from database.project_repository import ProjectRepository
from tqdm import tqdm
import pandas as pd

logger = Logger().get_logger()

class TimeEntryService:
    def __init__(self, db: Session):
        self.db = db
        self.customer_repo = CustomerRepository()
        self.project_repo = ProjectRepository()
        logger.debug("TimeEntryService initialized with database session")

    def import_timesheet(self, file_contents: bytes, filename: str) -> List[TimeEntry]:
        """Import timesheet from uploaded file."""
        logger.debug(f"Processing timesheet file: {filename}")

        try:
            from utils.xls_analyzer import XLSAnalyzer
            analyzer = XLSAnalyzer()

            if filename.endswith('.xlsx'):
                records = analyzer.read_excel(file_contents)
            else:
                raise ValueError("Unsupported file format. Please upload an Excel (.xlsx) file.")

            entries = []
            for record in records:
                if not pd.isna(record.get('Date')):
                    entry_data = schemas.TimeEntryCreate(
                        date=record.get('Date'),
                        category=record.get('Category', 'Other'),
                        subcategory=record.get('Subcategory', 'General'),
                        customer=normalize_customer_name(record.get('Customer', DEFAULT_CUSTOMER)) or DEFAULT_CUSTOMER,
                        project=normalize_project_id(record.get('Project', DEFAULT_PROJECT)) or DEFAULT_PROJECT,
                        task_description=record.get('Task Description', ''),
                        hours=float(record.get('Hours', 0.0))
                    )
                    db_entry = self.create_time_entry(entry_data)
                    entries.append(db_entry)

            return entries
        except Exception as e:
            logger.error(f"Error importing timesheet: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_time_entries(
        self,
        project_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TimeEntry]:
        """Retrieve time entries with filters."""
        logger.debug(f"Retrieving time entries with filters: project_id={project_id}, customer={customer_name}, date={date}")
        query = self.db.query(TimeEntry)

        try:
            if project_id:
                logger.debug(f"Applying project filter: {project_id}")
                normalized_project = normalize_project_id(project_id)
                query = query.filter(TimeEntry.project == normalized_project)

            if customer_name:
                logger.debug(f"Applying customer filter: {customer_name}")
                normalized_customer = normalize_customer_name(customer_name)
                query = query.filter(TimeEntry.customer == normalized_customer)

            if date:
                logger.debug(f"Applying date filter: {date}")
                query = query.filter(TimeEntry.date == date)

            logger.debug(f"Applying pagination: skip={skip}, limit={limit}")
            results = query.offset(skip).limit(limit).all()
            logger.info(f"Retrieved {len(results)} time entries")
            return results

        except Exception as e:
            logger.error(f"Error retrieving time entries: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error retrieving time entries: {str(e)}")

    def create_time_entry(self, entry: schemas.TimeEntryCreate) -> TimeEntry:
        """Create a new time entry."""
        try:
            logger.debug(f"Creating time entry: {entry.model_dump()}")
            db_entry = TimeEntry(**entry.model_dump())
            self.db.add(db_entry)
            self.db.commit()
            self.db.refresh(db_entry)
            return db_entry
        except Exception as e:
            logger.error(f"Error creating time entry: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def update_time_entry(self, entry_id: int, entry: schemas.TimeEntryUpdate) -> TimeEntry:
        """Update an existing time entry."""
        try:
            logger.debug(f"Updating time entry {entry_id}")
            db_entry = self.db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
            if not db_entry:
                raise HTTPException(status_code=404, detail="Time entry not found")

            update_data = entry.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_entry, key, value)

            self.db.commit()
            self.db.refresh(db_entry)
            return db_entry
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating time entry: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def delete_time_entry(self, entry_id: int) -> bool:
        """Delete a time entry."""
        try:
            logger.debug(f"Deleting time entry {entry_id}")
            db_entry = self.db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
            if not db_entry:
                raise HTTPException(status_code=404, detail="Time entry not found")

            self.db.delete(db_entry)
            self.db.commit()
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting time entry: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
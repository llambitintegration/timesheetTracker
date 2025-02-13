from typing import List, Optional, Dict, Any, Union
import sqlalchemy as sa
from sqlalchemy.orm import Session
from datetime import datetime, date
from models.timeEntry import TimeEntry
from models.customerModel import Customer
from models.projectModel import Project
from database import schemas
from .base_repository import BaseRepository
from utils.xls_analyzer import XLSAnalyzer
from utils.logger import Logger
from utils.validators import normalize_project_id, normalize_customer_name
import pandas as pd

logger = Logger().get_logger()

class TimeEntryRepository(BaseRepository[TimeEntry]):
    def __init__(self):
        super().__init__(TimeEntry)

    def create(self, db: Session, data: Union[Dict[str, Any], schemas.TimeEntryCreate, TimeEntry]) -> TimeEntry:
        """Create a new time entry with better foreign key handling."""
        try:
            if isinstance(data, TimeEntry):
                db_entry = data
            else:
                if hasattr(data, 'model_dump'):
                    entry_dict = data.model_dump(exclude={'id', 'created_at', 'updated_at'})
                elif isinstance(data, dict):
                    entry_dict = data
                else:
                    raise ValueError(f"Invalid data type for time entry creation: {type(data)}")

                # Validate foreign keys before creation
                if entry_dict.get('project'):
                    project = db.query(Project).filter(
                        Project.project_id == entry_dict['project']
                    ).first()
                    if not project:
                        entry_dict['project'] = None

                if entry_dict.get('customer'):
                    customer = db.query(Customer).filter(
                        Customer.name == entry_dict['customer']
                    ).first()
                    if not customer:
                        entry_dict['customer'] = None

                db_entry = TimeEntry(**entry_dict)

            db.add(db_entry)
            db.commit()
            db.refresh(db_entry)
            logger.info(f"Successfully created time entry: {db_entry.id}")
            return db_entry
        except Exception as e:
            logger.error(f"Error creating time entry: {str(e)}")
            db.rollback()
            raise

    def bulk_create(self, db: Session, entries: List[schemas.TimeEntryCreate]) -> List[TimeEntry]:
        """Bulk create time entries with better error handling."""
        try:
            from services.time_entry_service import TimeEntryService
            service = TimeEntryService(db)

            db_entries = []
            for entry in entries:
                try:
                    db_entry = service.create_time_entry(entry)
                    db_entries.append(db_entry)
                except Exception as e:
                    logger.error(f"Error creating entry: {str(e)}")
                    continue

            return db_entries
        except Exception as e:
            logger.error(f"Error in bulk create: {str(e)}")
            db.rollback()
            raise

    def update(self, db: Session, item: TimeEntry) -> TimeEntry:
        """Update with better error handling."""
        try:
            # Validate foreign keys
            if item.project:
                project = db.query(Project).filter(
                    Project.project_id == item.project
                ).first()
                if not project:
                    item.project = None

            if item.customer:
                customer = db.query(Customer).filter(
                    Customer.name == item.customer
                ).first()
                if not customer:
                    item.customer = None

            db.merge(item)
            db.commit()
            db.refresh(item)
            logger.info(f"Successfully updated time entry: {item.id}")
            return item
        except Exception as e:
            logger.error(f"Error updating time entry: {str(e)}")
            db.rollback()
            raise

    def get_by_id(self, db: Session, id: int) -> Optional[TimeEntry]:
        """Get a time entry by ID with error handling."""
        try:
            entry = db.query(self.model).filter(self.model.id == id).first()
            if not entry:
                logger.warning(f"Time entry not found with ID: {id}")
            return entry
        except Exception as e:
            logger.error(f"Error getting time entry by ID {id}: {str(e)}")
            raise

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
        """Delete with proper error handling."""
        try:
            entry = self.get_by_id(db, id)
            if entry:
                db.delete(entry)
                db.commit()
                logger.info(f"Successfully deleted time entry: {id}")
                return True
            logger.warning(f"Time entry not found for deletion: {id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting time entry: {str(e)}")
            db.rollback()
            raise

    def import_excel(self, db: Session, file_contents: bytes) -> List[TimeEntry]:
        """Import time entries with better validation."""
        try:
            analyzer = XLSAnalyzer()
            records = analyzer.read_excel(file_contents)

            entries = []
            for record in records:
                if not pd.isna(record.get('Date')):
                    customer = normalize_customer_name(record.get('Customer'))
                    project = normalize_project_id(record.get('Project'))

                    # Validate foreign keys
                    if customer:
                        customer_exists = db.query(Customer).filter(
                            Customer.name == customer
                        ).first()
                        if not customer_exists:
                            customer = None

                    if project:
                        project_exists = db.query(Project).filter(
                            Project.project_id == project
                        ).first()
                        if not project_exists:
                            project = None

                    entry_data = schemas.TimeEntryCreate(
                        date=record.get('Date'),
                        category=record.get('Category', 'Other'),
                        subcategory=record.get('Subcategory', 'General'),
                        customer=customer,
                        project=project,
                        task_description=record.get('Task Description', ''),
                        hours=float(record.get('Hours', 0.0))
                    )
                    entries.append(entry_data)

            return self.bulk_create(db, entries)
        except Exception as e:
            logger.error(f"Error importing Excel data: {str(e)}")
            raise
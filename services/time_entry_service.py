
from sqlalchemy.orm import Session
from typing import List, Optional
from database import schemas
from models.timeEntry import TimeEntry
from utils.logger import Logger

logger = Logger().get_logger()

class TimeEntryService:
    def __init__(self, db: Session):
        self.db = db
        
    def create_time_entry(self, entry: schemas.TimeEntryCreate) -> TimeEntry:
        """Create a new time entry."""
        try:
            logger.debug(f"Creating time entry with data: {entry.dict()}")
            entry_dict = entry.dict()
            if not entry_dict.get('category'):
                entry_dict['category'] = 'Other'
            if not entry_dict.get('subcategory'):
                entry_dict['subcategory'] = 'General'
                
            db_entry = TimeEntry(**entry_dict)
            self.db.add(db_entry)
            self.db.commit()
            self.db.refresh(db_entry)
            logger.info(f"Successfully created time entry for {entry.customer} - {entry.project}")
            return db_entry
        except Exception as e:
            logger.error(f"Error creating time entry: {str(e)}")
            self.db.rollback()
            raise

    def create_many_entries(self, entries: List[schemas.TimeEntryCreate]) -> List[TimeEntry]:
        """Create multiple time entries in a single transaction."""
        created_entries = []
        try:
            for entry in entries:
                db_entry = TimeEntry(**entry.dict())
                self.db.add(db_entry)
                created_entries.append(db_entry)
            
            self.db.commit()
            logger.info(f"Successfully created {len(created_entries)} time entries")
            return created_entries
        except Exception as e:
            logger.error(f"Error creating multiple time entries: {str(e)}")
            self.db.rollback()
            raise

    def get_time_entries(
        self,
        project_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TimeEntry]:
        """Retrieve time entries with filters."""
        query = self.db.query(TimeEntry)
        if project_id:
            query = query.filter(TimeEntry.project == project_id)
        if customer_name:
            query = query.filter(TimeEntry.customer == customer_name)
        return query.offset(skip).limit(limit).all()

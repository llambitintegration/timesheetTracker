
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
            db_entry = TimeEntry(**entry.dict())
            self.db.add(db_entry)
            self.db.commit()
            self.db.refresh(db_entry)
            logger.info(f"Successfully created time entry for {entry.customer} - {entry.project}")
            return db_entry
        except Exception as e:
            logger.error(f"Error creating time entry: {str(e)}")
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

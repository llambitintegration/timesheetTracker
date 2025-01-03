from sqlalchemy.orm import Session
from typing import List
import logging

logger = logging.getLogger(__name__)

class TimesheetRepository:
    def __init__(self, model):
        self.model = model

    def get_by_customer(self, db: Session, customer_name: str) -> List[TimeEntry]:
        return db.query(self.model).filter(self.model.customer == customer_name).all()
        
    def bulk_create(self, db: Session, entries: List[TimeEntry]) -> List[TimeEntry]:
        """Bulk create time entries"""
        try:
            db.bulk_save_objects(entries)
            db.commit()
            return entries
        except Exception as e:
            db.rollback()
            logger.error(f"Error in bulk create: {str(e)}")
            raise

#The following is necessary to avoid import errors, but is not part of the provided changes.  Assumed structure based on context.
class TimeEntry:
    customer = None # Placeholder, needs actual definition
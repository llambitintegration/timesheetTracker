
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from models.timeEntry import TimeEntry
from .base_repository import BaseRepository

class TimesheetRepository(BaseRepository[TimeEntry]):
    def __init__(self):
        super().__init__(TimeEntry)

    def get_by_project(self, db: Session, project_id: str) -> List[TimeEntry]:
        return db.query(self.model).filter(self.model.project == project_id).all()

    def get_by_customer(self, db: Session, customer_name: str) -> List[TimeEntry]:
        return db.query(self.model).filter(self.model.customer == customer_name).all()

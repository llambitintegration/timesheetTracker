
from typing import List, Optional
from sqlalchemy.orm import Session
from models.projectModel import Project
from .base_repository import BaseRepository

class ProjectRepository(BaseRepository[Project]):
    def __init__(self):
        super().__init__(Project)

    def get_by_project_id(self, db: Session, project_id: str) -> Optional[Project]:
        return db.query(self.model).filter(self.model.project_id == project_id).first()

    def get_by_customer(self, db: Session, customer_name: str) -> List[Project]:
        return db.query(self.model).filter(self.model.customer == customer_name).all()

    def get_by_project_manager(self, db: Session, manager_name: str) -> List[Project]:
        return db.query(self.model).filter(self.model.project_manager == manager_name).all()

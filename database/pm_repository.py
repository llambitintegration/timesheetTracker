
from typing import Optional
from sqlalchemy.orm import Session
from models.projectManagerModel import ProjectManager
from .base_repository import BaseRepository

class ProjectManagerRepository(BaseRepository[ProjectManager]):
    def __init__(self):
        super().__init__(ProjectManager)

    def get_by_name(self, db: Session, name: str) -> Optional[ProjectManager]:
        return db.query(self.model).filter(self.model.name == name).first()

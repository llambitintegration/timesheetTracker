from typing import Optional, List
from sqlalchemy.orm import Session
from models.projectManagerModel import ProjectManager
from .base_repository import BaseRepository

class ProjectManagerRepository(BaseRepository[ProjectManager]):
    def __init__(self):
        super().__init__(ProjectManager)

    def get_by_name(self, db: Session, name: str) -> Optional[ProjectManager]:
        """Get a project manager by name."""
        return db.query(self.model).filter(self.model.name == name).first()

    def get_by_email(self, db: Session, email: str) -> Optional[ProjectManager]:
        """Get a project manager by email."""
        return db.query(self.model).filter(self.model.email == email).first()

    def create(self, db: Session, project_manager_data: dict) -> ProjectManager:
        """Create a new project manager."""
        db_project_manager = ProjectManager(**project_manager_data)
        db.add(db_project_manager)
        db.commit()
        db.refresh(db_project_manager)
        return db_project_manager

    def update(self, db: Session, project_manager: ProjectManager) -> ProjectManager:
        """Update an existing project manager."""
        db.merge(project_manager)
        db.commit()
        db.refresh(project_manager)
        return project_manager

    def delete(self, db: Session, email: str) -> bool:
        """Delete a project manager by email."""
        project_manager = self.get_by_email(db, email)
        if project_manager:
            db.delete(project_manager)
            db.commit()
            return True
        return False

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[ProjectManager]:
        """Get all project managers with pagination."""
        return db.query(self.model).offset(skip).limit(limit).all()
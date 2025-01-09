from typing import List, Optional
from sqlalchemy.orm import Session
from models.projectModel import Project
from .base_repository import BaseRepository
from utils.logger import Logger

logger = Logger().get_logger()

class ProjectRepository(BaseRepository[Project]):
    def __init__(self):
        super().__init__(Project)
        logger.debug("ProjectRepository initialized")

    def get_by_project_id(self, db: Session, project_id: str) -> Optional[Project]:
        """Get a project by its unique project_id."""
        logger.debug(f"Fetching project with ID: {project_id}")
        return db.query(self.model).filter(self.model.project_id == project_id).first()

    def get_by_customer(self, db: Session, customer_name: str) -> List[Project]:
        """Get all projects for a specific customer."""
        logger.debug(f"Fetching projects for customer: {customer_name}")
        return db.query(self.model).filter(self.model.customer == customer_name).all()

    def get_by_project_manager(self, db: Session, manager_name: str) -> List[Project]:
        """Get all projects managed by a specific project manager."""
        logger.debug(f"Fetching projects for manager: {manager_name}")
        return db.query(self.model).filter(self.model.project_manager == manager_name).all()

    def create(self, db: Session, data: dict) -> Project:
        """Create a new project."""
        logger.debug(f"Creating new project with data: {data}")
        try:
            # Check if project with same ID already exists
            existing_project = self.get_by_project_id(db, data['project_id'])
            if existing_project:
                logger.warning(f"Project with ID {data['project_id']} already exists")
                raise ValueError(f"Project with ID {data['project_id']} already exists")

            db_project = Project(**data)
            db.add(db_project)
            db.commit()
            db.refresh(db_project)
            logger.info(f"Successfully created project: {db_project.project_id}")
            return db_project
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            db.rollback()
            raise

    def update(self, db: Session, item: Project) -> Project:
        """Update an existing project."""
        logger.debug(f"Updating project: {item.project_id}")
        try:
            db.merge(item)
            db.commit()
            db.refresh(item)
            logger.info(f"Successfully updated project: {item.project_id}")
            return item
        except Exception as e:
            logger.error(f"Error updating project: {str(e)}")
            db.rollback()
            raise

    def delete(self, db: Session, project_id: str) -> bool:
        """Delete a project by its project_id."""
        logger.debug(f"Attempting to delete project: {project_id}")
        try:
            project = self.get_by_project_id(db, project_id)
            if project:
                db.delete(project)
                db.commit()
                logger.info(f"Successfully deleted project: {project_id}")
                return True
            logger.warning(f"Project not found for deletion: {project_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting project: {str(e)}")
            db.rollback()
            raise

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get all projects with pagination."""
        logger.debug(f"Fetching all projects with skip={skip}, limit={limit}")
        projects = db.query(self.model).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(projects)} projects")
        return projects
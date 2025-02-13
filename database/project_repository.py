from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models.projectModel import Project
from .base_repository import BaseRepository
from utils.logger import Logger
from database import schemas

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

    def create(self, db: Session, data: Dict[str, Any] | schemas.ProjectCreate | Project) -> Project:
        """Create a new project with schema support."""
        logger.debug(f"Creating new project with data: {data}")
        try:
            # Convert input to project instance
            if isinstance(data, Project):
                db_project = data
            elif hasattr(data, 'model_dump'):
                project_data = data.model_dump()
                db_project = Project(**project_data)
            elif isinstance(data, dict):
                db_project = Project(**data)
            else:
                raise ValueError(f"Invalid data type for project creation: {type(data)}")

            # Check if project with same ID already exists
            existing_project = self.get_by_project_id(db, db_project.project_id)
            if existing_project:
                logger.warning(f"Project with ID {db_project.project_id} already exists")
                raise ValueError(f"Project with ID {db_project.project_id} already exists")

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
        """Update an existing project with better error handling."""
        logger.debug(f"Updating project: {item.project_id}")
        try:
            # Check if project exists
            existing = self.get_by_project_id(db, item.project_id)
            if not existing:
                raise ValueError(f"Project with ID {item.project_id} not found")

            # Check if project_id is being changed and if new ID exists
            if existing.project_id != item.project_id:
                duplicate = self.get_by_project_id(db, item.project_id)
                if duplicate:
                    raise ValueError(f"Project with ID {item.project_id} already exists")

            # Perform the update
            db.merge(item)
            db.commit()
            db.refresh(item)
            logger.info(f"Successfully updated project: {item.project_id}")
            return item
        except Exception as e:
            logger.error(f"Error updating project: {str(e)}")
            db.rollback()
            raise

    def delete(self, db: Session, id: str) -> bool:
        """Delete a project by its project_id with enhanced error handling."""
        logger.debug(f"Attempting to delete project: {id}")
        try:
            project = self.get_by_project_id(db, id)
            if project:
                db.delete(project)
                db.commit()
                logger.info(f"Successfully deleted project: {id}")
                return True
            logger.warning(f"Project not found for deletion: {id}")
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
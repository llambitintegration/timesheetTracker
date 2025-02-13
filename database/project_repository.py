from typing import List, Optional, Dict, Any, Union
import sqlalchemy as sa
from sqlalchemy.orm import Session
from models.projectModel import Project
from models.timeEntry import TimeEntry
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

    def create(self, db: Session, data: Union[Dict[str, Any], schemas.ProjectCreate, Project]) -> Project:
        """Create with better foreign key handling."""
        try:
            if isinstance(data, Project):
                db_project = data
            else:
                if hasattr(data, 'model_dump'):
                    project_data = data.model_dump()
                elif isinstance(data, dict):
                    project_data = data
                else:
                    raise ValueError(f"Invalid data type for project creation: {type(data)}")

                # Handle None values for foreign keys
                if 'customer' in project_data and not project_data['customer']:
                    project_data.pop('customer')
                if 'project_manager' in project_data and not project_data['project_manager']:
                    project_data.pop('project_manager')

                project_data['status'] = project_data.get('status', 'active')
                db_project = Project(**project_data)

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
        """Update with better error handling."""
        try:
            existing = self.get_by_project_id(db, item.project_id)
            if not existing:
                raise ValueError(f"Project with ID {item.project_id} not found")

            # Handle None values for foreign keys
            if hasattr(item, 'customer') and not item.customer:
                delattr(item, 'customer')
            if hasattr(item, 'project_manager') and not item.project_manager:
                delattr(item, 'project_manager')

            db.merge(item)
            db.commit()
            db.refresh(item)
            logger.info(f"Successfully updated project: {item.project_id}")
            return item
        except Exception as e:
            logger.error(f"Error updating project: {str(e)}")
            db.rollback()
            raise

    def get(self, db: Session, id: int) -> Optional[Project]:
        """Override base get to maintain compatibility."""
        project = db.query(self.model).filter(self.model.id == id).first()
        if not project:
            logger.warning(f"Project not found with ID: {id}")
        return project

    def delete(self, db: Session, id: int) -> bool:
        """Override base delete to handle both numeric id and project_id."""
        try:
            # First try to find by numeric ID
            project = self.get(db, id)
            if not project:
                # If not found by numeric ID, try project_id
                project = self.get_by_project_id(db, str(id))

            if project:
                # Update related time entries to set project to NULL
                db.query(TimeEntry).filter(
                    TimeEntry.project == project.project_id
                ).update(
                    {TimeEntry.project: None},
                    synchronize_session=False
                )

                db.delete(project)
                db.commit()
                logger.info(f"Successfully deleted project: {project.project_id}")
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
from sqlalchemy.orm import Session
from typing import List, Optional
from database.project_repository import ProjectRepository 
from database import schemas
from models.projectModel import Project
from utils.logger import Logger

logger = Logger().get_logger()

class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository()
        logger.debug("ProjectService initialized with database session")

    def create_project(self, project: schemas.ProjectCreate) -> Project:
        """Create a new project with validation."""
        try:
            logger.debug(f"Starting creation of project with data: {project.model_dump()}")

            # Check if project already exists with same project_id
            existing_project = self.project_repo.get_by_project_id(self.db, project.project_id)
            if existing_project:
                logger.warning(f"Project with ID {project.project_id} already exists")
                raise ValueError(f"Project with ID {project.project_id} already exists")

            # Convert pydantic model to dict and create project
            project_data = project.model_dump(exclude={'id', 'created_at', 'updated_at'})
            logger.debug("Adding project to database session")
            created_project = self.project_repo.create(self.db, project_data)

            logger.info(f"Successfully created project: {created_project.project_id}")
            return created_project
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            self.db.rollback()
            raise

    def get_project(self, project_id: str) -> Optional[Project]:
        """Retrieve a project by project_id."""
        logger.debug(f"Attempting to fetch project with ID: {project_id}")
        project = self.project_repo.get_by_project_id(self.db, project_id)
        if project:
            logger.info(f"Found project: {project_id}")
        else:
            logger.info(f"No project found with ID: {project_id}")
        return project

    def get_all_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """Retrieve all projects with pagination."""
        logger.debug(f"Fetching projects with offset={skip}, limit={limit}")
        projects = self.project_repo.get_all(self.db, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(projects)} projects")
        return projects

    def get_projects_by_customer(self, customer_name: str) -> List[Project]:
        """Get all projects for a specific customer."""
        logger.debug(f"Fetching projects for customer: {customer_name}")
        projects = self.project_repo.get_by_customer(self.db, customer_name)
        logger.info(f"Retrieved {len(projects)} projects for customer {customer_name}")
        return projects

    def get_projects_by_manager(self, manager_name: str) -> List[Project]:
        """Get all projects for a specific project manager."""
        logger.debug(f"Fetching projects for manager: {manager_name}")
        projects = self.project_repo.get_by_project_manager(self.db, manager_name)
        logger.info(f"Retrieved {len(projects)} projects for manager {manager_name}")
        return projects

    def update_project(self, project_id: str, project_update: schemas.ProjectBase) -> Optional[Project]:
        """Update an existing project."""
        logger.debug(f"Attempting to update project {project_id} with data: {project_update.model_dump(exclude_unset=True)}")

        existing_project = self.project_repo.get_by_project_id(self.db, project_id)
        if not existing_project:
            logger.warning(f"Project not found: {project_id}")
            return None

        try:
            # Update only the fields that are provided
            update_data = project_update.model_dump(exclude={'id', 'created_at', 'updated_at'}, exclude_unset=True)
            for key, value in update_data.items():
                setattr(existing_project, key, value)

            updated_project = self.project_repo.update(self.db, existing_project)
            logger.info(f"Successfully updated project: {project_id}")
            return updated_project
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {str(e)}")
            self.db.rollback()
            raise

    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        logger.debug(f"Attempting to delete project: {project_id}")
        try:
            result = self.project_repo.delete(self.db, project_id)
            if result:
                logger.info(f"Successfully deleted project: {project_id}")
            else:
                logger.warning(f"Project not found for deletion: {project_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            self.db.rollback()
            raise

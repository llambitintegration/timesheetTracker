from sqlalchemy.orm import Session
from typing import List, Optional
from database.pm_repository import ProjectManagerRepository
from database import schemas
from models.projectManagerModel import ProjectManager
from utils.logger import Logger
from fastapi import HTTPException

logger = Logger().get_logger()

class ProjectManagerService:
    def __init__(self, db: Session):
        self.db = db
        self.pm_repo = ProjectManagerRepository()
        logger.debug("ProjectManagerService initialized with database session")

    def create_project_manager(self, project_manager: schemas.ProjectManagerCreate) -> ProjectManager:
        """Create a new project manager with validation."""
        try:
            logger.debug(f"Starting creation of project manager with data: {project_manager.model_dump()}")

            # Check if project manager already exists with same email
            existing_pm = self.pm_repo.get_by_email(self.db, project_manager.email)
            if existing_pm:
                logger.warning(f"Project manager with email {project_manager.email} already exists")
                raise HTTPException(
                    status_code=400,
                    detail=f"Project manager with email {project_manager.email} already exists"
                )

            # Convert pydantic model to dict and create project manager
            pm_data = project_manager.model_dump(exclude={'id', 'created_at', 'updated_at'})
            logger.debug("Adding project manager to database session")
            created_pm = self.pm_repo.create(self.db, pm_data)

            logger.info(f"Successfully created project manager: {created_pm.name}")
            return created_pm
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating project manager: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def get_project_manager(self, email: str) -> Optional[ProjectManager]:
        """Retrieve a project manager by email."""
        logger.debug(f"Attempting to fetch project manager with email: {email}")
        pm = self.pm_repo.get_by_email(self.db, email)
        if not pm:
            logger.warning(f"No project manager found with email: {email}")
            raise HTTPException(status_code=404, detail="Project manager not found")
        logger.info(f"Found project manager: {pm.name}")
        return pm

    def get_all_project_managers(self, skip: int = 0, limit: int = 100) -> List[ProjectManager]:
        """Retrieve all project managers with pagination."""
        logger.debug(f"Fetching project managers with offset={skip}, limit={limit}")
        pms = self.pm_repo.get_all(self.db, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(pms)} project managers")
        return pms

    def update_project_manager(self, email: str, pm_update: schemas.ProjectManagerUpdate) -> ProjectManager:
        """Update an existing project manager."""
        logger.debug(f"Attempting to update project manager {email} with data: {pm_update.model_dump(exclude_unset=True)}")

        try:
            existing_pm = self.pm_repo.get_by_email(self.db, email)
            if not existing_pm:
                logger.warning(f"Project manager not found: {email}")
                raise HTTPException(status_code=404, detail="Project manager not found")

            update_data = pm_update.model_dump(exclude={'id', 'created_at', 'updated_at'}, exclude_unset=True)

            for key, value in update_data.items():
                if value is not None:  # Only update non-None values
                    setattr(existing_pm, key, value)

            updated_pm = self.pm_repo.update(self.db, existing_pm)
            logger.info(f"Successfully updated project manager: {email}")
            return updated_pm
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating project manager {email}: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def delete_project_manager(self, email: str) -> bool:
        """Delete a project manager by email."""
        logger.debug(f"Attempting to delete project manager with email: {email}")
        try:
            # First check if the project manager exists
            if not self.pm_repo.get_by_email(self.db, email):
                logger.warning(f"Project manager not found for deletion: {email}")
                raise HTTPException(status_code=404, detail="Project manager not found")

            success = self.pm_repo.delete(self.db, email)
            if success:
                logger.info(f"Successfully deleted project manager: {email}")
                return True

            logger.error(f"Failed to delete project manager: {email}")
            raise HTTPException(status_code=500, detail="Failed to delete project manager")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting project manager {email}: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
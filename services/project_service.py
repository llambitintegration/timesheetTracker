from sqlalchemy.orm import Session
from typing import List, Optional
from database.project_repository import ProjectRepository 
from database.customer_repository import CustomerRepository
from database.pm_repository import ProjectManagerRepository
from database import schemas
from models.projectModel import Project
from utils.logger import Logger
from utils.validators import normalize_customer_name, normalize_project_id, normalize_project_manager
from fastapi import HTTPException

logger = Logger().get_logger()

class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository()
        self.customer_repo = CustomerRepository()
        self.pm_repo = ProjectManagerRepository()
        logger.debug("ProjectService initialized")

    def _ensure_customer_exists(self, customer_name: Optional[str]) -> Optional[str]:
        """Ensure customer exists, return normalized customer name."""
        if not customer_name:
            return None

        try:
            normalized_name = normalize_customer_name(customer_name)
            if not normalized_name:
                return None

            # Check if customer exists
            existing = self.customer_repo.get_by_name(self.db, normalized_name)
            if existing:
                logger.debug(f"Found existing customer: {normalized_name}")
                return normalized_name

            # Create new customer using CustomerCreate schema
            customer_data = schemas.CustomerCreate(
                name=normalized_name,
                contact_email=f"{normalized_name.lower().replace(' ', '_')}@example.com",
                status="active"
            )

            # Convert to dictionary for database operation
            customer_dict = customer_data.model_dump()
            new_customer = self.customer_repo.create(self.db, customer_dict)
            self.db.refresh(new_customer)
            logger.info(f"Created new customer: {normalized_name}")
            return normalized_name

        except Exception as e:
            logger.error(f"Error ensuring customer exists: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to validate customer: {str(e)}")

    def _ensure_project_manager_exists(self, manager_name: Optional[str]) -> bool:
        """Ensure project manager exists. Return True if exists or created."""
        if not manager_name:
            return True

        try:
            normalized_name = normalize_project_manager(manager_name)
            if not normalized_name:
                return True

            # Check if project manager exists
            existing = self.pm_repo.get_by_name(self.db, normalized_name)
            if existing:
                logger.debug(f"Found existing project manager: {normalized_name}")
                return True

            # Create project manager
            pm_data = schemas.ProjectManagerCreate(
                name=normalized_name,
                email=f"{normalized_name.lower().replace(' ', '.')}@company.com"
            )
            self.pm_repo.create(self.db, pm_data.model_dump())
            logger.info(f"Created new project manager: {normalized_name}")
            return True

        except Exception as e:
            logger.error(f"Error verifying project manager: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to verify project manager: {str(e)}")

    def create_project(self, project: schemas.ProjectCreate) -> Project:
        """Create a new project with validation."""
        try:
            logger.debug(f"Starting creation of project with data: {project.model_dump()}")

            # Normalize and validate customer if provided
            customer_name = self._ensure_customer_exists(project.customer)

            # Create or validate project manager if provided
            if project.project_manager:
                self._ensure_project_manager_exists(project.project_manager)

            # Check if project already exists
            existing_project = self.project_repo.get_by_project_id(self.db, project.project_id)
            if existing_project:
                logger.warning(f"Project with ID {project.project_id} already exists")
                raise HTTPException(status_code=400, detail=f"Project with ID {project.project_id} already exists")

            # Convert pydantic model to dict and create project
            project_data = project.model_dump()
            project_data['customer'] = customer_name
            project_data['project_manager'] = normalize_project_manager(project_data.get('project_manager'))

            logger.debug(f"Creating new project with data: {project_data}")
            created_project = self.project_repo.create(self.db, project_data)
            self.db.refresh(created_project)

            logger.info(f"Successfully created project: {created_project.project_id}")
            return created_project

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def get_project(self, project_id: str) -> Optional[Project]:
        """Retrieve a project by project_id."""
        logger.debug(f"Fetching project with ID: {project_id}")
        project = self.project_repo.get_by_project_id(self.db, project_id)
        if not project:
            logger.warning(f"Project not found: {project_id}")
            raise HTTPException(status_code=404, detail="Project not found")
        logger.info(f"Found project: {project_id}")
        return project

    def get_all_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """Retrieve all projects with pagination."""
        logger.debug(f"Fetching projects with offset={skip}, limit={limit}")
        try:
            projects = self.project_repo.get_all(self.db, skip=skip, limit=limit)
            logger.info(f"Retrieved {len(projects)} projects")
            return projects
        except Exception as e:
            logger.error(f"Error fetching projects: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def update_project(self, project_id: str, project_update: schemas.ProjectUpdate) -> Optional[Project]:
        """Update an existing project."""
        logger.debug(f"Attempting to update project {project_id}")

        try:
            existing_project = self.get_project(project_id)
            if not existing_project:
                logger.warning(f"Project not found: {project_id}")
                raise HTTPException(status_code=404, detail="Project not found")

            # Update only the fields that are provided
            update_data = project_update.model_dump(exclude={'id', 'created_at', 'updated_at'}, exclude_unset=True)

            # If project manager is being updated, ensure they exist
            if 'project_manager' in update_data:
                manager_name = normalize_project_manager(update_data['project_manager'])
                update_data['project_manager'] = manager_name
                if manager_name:
                    self._ensure_project_manager_exists(manager_name)

            # If customer is being updated, ensure they exist
            if 'customer' in update_data:
                customer_name = self._ensure_customer_exists(update_data['customer'])
                update_data['customer'] = customer_name

            for key, value in update_data.items():
                setattr(existing_project, key, value)

            updated_project = self.project_repo.update(self.db, existing_project)
            logger.info(f"Successfully updated project: {project_id}")
            return updated_project

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        logger.debug(f"Attempting to delete project: {project_id}")
        try:
            # First check if project exists
            existing_project = self.get_project(project_id)
            if not existing_project:
                logger.warning(f"Project not found: {project_id}")
                raise HTTPException(status_code=404, detail="Project not found")

            result = self.project_repo.delete(self.db, project_id)
            if result:
                logger.info(f"Successfully deleted project: {project_id}")
                return True

            logger.error(f"Failed to delete project: {project_id}")
            raise HTTPException(status_code=500, detail="Failed to delete project")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
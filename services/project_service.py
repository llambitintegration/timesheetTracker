from sqlalchemy.orm import Session
from typing import List, Optional
from database.project_repository import ProjectRepository 
from database.customer_repository import CustomerRepository
from database.pm_repository import ProjectManagerRepository  # Added PM repository
from database import schemas
from models.projectModel import Project
from utils.logger import Logger
from utils.validators import (
    DEFAULT_CUSTOMER, DEFAULT_PROJECT, 
    normalize_customer_name, ensure_default_project_manager
)

logger = Logger().get_logger()

class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository()
        self.customer_repo = CustomerRepository()
        self.pm_repo = ProjectManagerRepository()  # Added PM repository
        logger.debug("ProjectService initialized with database session")

    def _ensure_customer_exists(self, customer_name: str) -> str:
        """Ensure customer exists, return normalized customer name."""
        if not customer_name or customer_name == '-':
            logger.debug("No customer name provided, using default")
            return DEFAULT_CUSTOMER

        try:
            normalized_name = normalize_customer_name(customer_name)
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
            raise ValueError(f"Failed to validate customer: {str(e)}")

    def _ensure_project_manager_exists(self, manager_name: str) -> bool:
        """Ensure project manager exists. Return True if exists."""
        try:
            # Check if project manager exists
            existing = self.pm_repo.get_by_name(self.db, manager_name)
            if existing:
                logger.debug(f"Found existing project manager: {manager_name}")
                return True

            logger.error(f"Project manager not found: {manager_name}")
            return False
        except Exception as e:
            logger.error(f"Error verifying project manager: {str(e)}")
            return False

    def create_project(self, project: schemas.ProjectCreate) -> Project:
        """Create a new project with validation."""
        try:
            logger.debug(f"Starting creation of project with data: {project.model_dump()}")

            # Ensure default project manager exists
            ensure_default_project_manager(self.db)

            # Normalize and validate customer
            customer_name = self._ensure_customer_exists(project.customer)
            if customer_name == DEFAULT_CUSTOMER and project.customer != DEFAULT_CUSTOMER:
                logger.error(f"Failed to ensure customer exists: {project.customer}")
                raise ValueError(f"Could not create or verify customer: {project.customer}")

            # Create or validate project manager
            if project.project_manager != '-':
                if not self._ensure_project_manager_exists(project.project_manager):
                    # Auto-create project manager
                    pm_data = schemas.ProjectManagerCreate(
                        name=project.project_manager,
                        email=f"{project.project_manager.lower().replace(' ', '.')}@company.com"
                    )
                    self.pm_repo.create(self.db, pm_data.model_dump())
                    logger.info(f"Created new project manager: {project.project_manager}")

            # Check if project already exists
            existing_project = self.project_repo.get_by_project_id(self.db, project.project_id)
            if existing_project:
                logger.warning(f"Project with ID {project.project_id} already exists")
                raise ValueError(f"Project with ID {project.project_id} already exists")

            # Convert pydantic model to dict and create project
            project_data = project.model_dump()
            project_data['customer'] = customer_name
            project_data['project_manager'] = project_data.get('project_manager') or 'Unassigned'

            logger.debug(f"Creating new project with data: {project_data}")
            created_project = self.project_repo.create(self.db, project_data)
            self.db.refresh(created_project)

            logger.info(f"Successfully created project: {created_project.project_id}")
            return created_project

        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            self.db.rollback()
            raise

    def get_project(self, project_id: str) -> Optional[Project]:
        """Retrieve a project by project_id."""
        logger.debug(f"Fetching project with ID: {project_id}")
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
        logger.debug(f"Attempting to update project {project_id}")

        existing_project = self.get_project(project_id)
        if not existing_project:
            logger.warning(f"Project not found: {project_id}")
            return None

        try:
            # Update only the fields that are provided
            update_data = project_update.model_dump(exclude={'id', 'created_at', 'updated_at'}, exclude_unset=True)

            # If project manager is being updated, ensure they exist
            if 'project_manager' in update_data:
                if update_data['project_manager'] is None or update_data['project_manager'] == '-':
                    update_data['project_manager'] = DEFAULT_PROJECT_MANAGER
                elif not self._ensure_project_manager_exists(update_data['project_manager']):
                    # Auto-create project manager
                    pm_name = update_data['project_manager']
                    pm_data = schemas.ProjectManagerCreate(
                        name=pm_name,
                        email=f"{pm_name.lower().replace(' ', '.')}@company.com"
                    )
                    self.pm_repo.create(self.db, pm_data.model_dump())
                    logger.info(f"Created new project manager: {pm_name}")

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
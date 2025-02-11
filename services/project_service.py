from sqlalchemy.orm import Session
from typing import List, Optional
from database.project_repository import ProjectRepository 
from database.customer_repository import CustomerRepository
from database.pm_repository import ProjectManagerRepository  # Added PM repository
from database import schemas
from models.projectModel import Project
from utils.logger import Logger
from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT, normalize_customer_name

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
            self.customer_repo.create(self.db, customer_dict)
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

            # Project manager is required and must exist
            if not project.project_manager:
                logger.error("Project manager is required")
                raise ValueError("Project manager is required for project creation")

            # Verify project manager exists before proceeding
            if not self._ensure_project_manager_exists(project.project_manager):
                logger.error(f"Project manager does not exist: {project.project_manager}")
                raise ValueError(f"Project manager not found: {project.project_manager}")

            # Normalize and validate customer
            customer_name = self._ensure_customer_exists(project.customer)
            if customer_name == DEFAULT_CUSTOMER and project.customer != DEFAULT_CUSTOMER:
                logger.error(f"Failed to ensure customer exists: {project.customer}")
                raise ValueError(f"Could not create or verify customer: {project.customer}")

            # Check if project already exists
            existing_project = self.project_repo.get_by_project_id(self.db, project.project_id)
            if existing_project:
                logger.warning(f"Project with ID {project.project_id} already exists")
                raise ValueError(f"Project with ID {project.project_id} already exists")

            # Convert pydantic model to dict
            project_data = project.to_dict()
            project_data['customer'] = customer_name

            logger.debug(f"Creating new project with data: {project_data}")
            created_project = self.project_repo.create(self.db, project_data)

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
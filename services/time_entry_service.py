from sqlalchemy.orm import Session
from typing import List, Optional
from database import schemas
from models.timeEntry import TimeEntry
from utils.logger import Logger
from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT, normalize_customer_name, normalize_project_id
from database.customer_repository import CustomerRepository
from database.project_repository import ProjectRepository

logger = Logger().get_logger()

class TimeEntryService:
    def __init__(self, db: Session):
        self.db = db
        self.customer_repo = CustomerRepository()
        self.project_repo = ProjectRepository()
        logger.debug("TimeEntryService initialized with database session")

    def _ensure_customer_exists(self, customer_name: str) -> str:
        """Ensure customer exists, create if not. Return normalized customer name."""
        if not customer_name or customer_name == '-':
            return DEFAULT_CUSTOMER

        try:
            normalized_name = normalize_customer_name(customer_name)
            # Check if customer exists
            existing = self.customer_repo.get_by_name(self.db, normalized_name)
            if not existing:
                # Create new customer
                customer_data = schemas.CustomerCreate(
                    name=normalized_name,
                    contact_email=f"{normalized_name.lower().replace(' ', '_')}@example.com",
                    status="active"
                )
                self.customer_repo.create(self.db, customer_data)
                logger.info(f"Created new customer: {normalized_name}")
            return normalized_name
        except Exception as e:
            logger.error(f"Error ensuring customer exists: {str(e)}")
            return DEFAULT_CUSTOMER

    def _ensure_project_exists(self, project_id: str, customer_name: str) -> str:
        """Ensure project exists, create if not. Return normalized project ID."""
        if not project_id or project_id == '-':
            return DEFAULT_PROJECT

        try:
            normalized_id = normalize_project_id(project_id)
            # Check if project exists
            existing = self.project_repo.get_by_project_id(self.db, normalized_id)

            if existing:
                # Verify project belongs to customer
                if existing.customer != customer_name:
                    logger.warning(f"Project {normalized_id} does not belong to customer {customer_name}")
                    return DEFAULT_PROJECT
                return normalized_id

            # Create new project if it doesn't exist
            try:
                project_data = schemas.ProjectCreate(
                    project_id=normalized_id,
                    name=normalized_id,
                    customer=customer_name,
                    status="active"
                )
                self.project_repo.create(self.db, project_data)
                logger.info(f"Created new project: {normalized_id} for customer: {customer_name}")
                return normalized_id
            except Exception as e:
                logger.error(f"Failed to create project {normalized_id}: {str(e)}")
                return DEFAULT_PROJECT

        except Exception as e:
            logger.error(f"Error ensuring project exists: {str(e)}")
            return DEFAULT_PROJECT

    def create_time_entry(self, entry: schemas.TimeEntryCreate) -> TimeEntry:
        """Create a new time entry with proper validation."""
        try:
            logger.debug(f"Starting creation of time entry with data: {entry.model_dump()}")

            # Ensure customer exists and get normalized name
            customer_name = self._ensure_customer_exists(entry.customer)

            # Ensure project exists with correct customer association
            project_id = self._ensure_project_exists(entry.project, customer_name)

            # If project validation failed, also reset customer to default
            if project_id == DEFAULT_PROJECT:
                customer_name = DEFAULT_CUSTOMER

            # Set default hours if not provided
            if entry.hours is None:
                entry.hours = 0.0
                logger.debug("No hours provided, defaulting to 0.0")

            # Update entry with validated customer and project
            entry_dict = entry.model_dump(exclude={'id', 'created_at', 'updated_at'})
            entry_dict.update({
                'customer': customer_name,
                'project': project_id
            })

            # Create TimeEntry instance
            db_entry = TimeEntry(**entry_dict)

            logger.debug("Adding entry to database session")
            try:
                self.db.add(db_entry)
                self.db.commit()
                self.db.refresh(db_entry)
            except Exception as e:
                logger.error(f"Database error while creating time entry: {str(e)}")
                self.db.rollback()
                # If there's a database error, try one more time with default project and customer
                if project_id != DEFAULT_PROJECT:
                    entry_dict.update({
                        'customer': DEFAULT_CUSTOMER,
                        'project': DEFAULT_PROJECT
                    })
                    db_entry = TimeEntry(**entry_dict)
                    self.db.add(db_entry)
                    self.db.commit()
                    self.db.refresh(db_entry)
                else:
                    raise

            logger.info(f"Successfully created time entry for {customer_name} - {project_id}")
            return db_entry

        except Exception as e:
            logger.error(f"Error creating time entry: {str(e)}")
            self.db.rollback()
            raise

    def create_many_entries(self, entries: List[schemas.TimeEntryCreate]) -> List[TimeEntry]:
        """Create multiple time entries with proper validation."""
        created_entries = []
        logger.info(f"Beginning bulk creation of {len(entries)} time entries")
        try:
            for idx, entry in enumerate(entries, 1):
                logger.debug(f"Processing entry {idx}/{len(entries)}")
                db_entry = self.create_time_entry(entry)
                created_entries.append(db_entry)
                logger.debug(f"Added entry {idx} to session: {db_entry.customer} - {db_entry.project}")

            total_hours = sum(entry.hours for entry in created_entries)
            logger.info(f"Successfully created {len(created_entries)} time entries (Total: {total_hours} hours)")
            return created_entries
        except Exception as e:
            logger.error(f"Error during bulk creation: {str(e)}")
            self.db.rollback()
            raise

    def get_time_entries(
        self,
        project_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TimeEntry]:
        """Retrieve time entries with filters."""
        logger.debug(f"Retrieving time entries with filters: project_id={project_id}, customer={customer_name}")
        query = self.db.query(TimeEntry)

        if project_id:
            logger.debug(f"Applying project filter: {project_id}")
            query = query.filter(TimeEntry.project == normalize_project_id(project_id))
        if customer_name:
            logger.debug(f"Applying customer filter: {customer_name}")
            query = query.filter(TimeEntry.customer == normalize_customer_name(customer_name))

        logger.debug(f"Applying pagination: skip={skip}, limit={limit}")
        results = query.offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(results)} time entries")
        return results
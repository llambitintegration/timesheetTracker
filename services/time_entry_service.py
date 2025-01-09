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

    def create_time_entry(self, entry: schemas.TimeEntryCreate) -> TimeEntry:
        """Create a new time entry with proper validation and defaults."""
        try:
            logger.debug(f"Starting creation of time entry with data: {entry.model_dump()}")
            entry_dict = entry.model_dump(exclude={'id', 'created_at', 'updated_at'})  # Exclude ID and timestamps

            # Calculate week number and month from date
            entry_dict['week_number'] = TimeEntry.get_week_number(entry_dict['date'])
            entry_dict['month'] = TimeEntry.get_month_name(entry_dict['date'])

            # Validate customer exists and get normalized name
            customer_name = None
            if entry_dict.get('customer'):
                customer = self.customer_repo.get_by_name(self.db, normalize_customer_name(entry_dict['customer']))
                if customer:
                    customer_name = customer.name
                else:
                    logger.info(f"Customer {entry_dict['customer']} not found, defaulting to {DEFAULT_CUSTOMER}")

            # Validate project exists and belongs to customer
            project_id = None
            if entry_dict.get('project') and customer_name:
                normalized_project_id = normalize_project_id(entry_dict['project'])
                project = self.project_repo.get_by_project_id(self.db, normalized_project_id)
                if project and project.customer == customer_name:
                    project_id = project.project_id
                else:
                    logger.info(f"Project {entry_dict['project']} not found or doesn't belong to customer, defaulting both customer and project to defaults")
                    customer_name = None  # Reset customer name to trigger default

            # Apply defaults if either validation failed
            entry_dict['customer'] = customer_name or DEFAULT_CUSTOMER
            entry_dict['project'] = project_id or DEFAULT_PROJECT

            logger.debug("Validating and setting default categories")
            if not entry_dict.get('category'):
                logger.info("No category provided, defaulting to 'Other'")
                entry_dict['category'] = 'Other'
            if not entry_dict.get('subcategory'):
                logger.info("No subcategory provided, defaulting to 'General'")
                entry_dict['subcategory'] = 'General'

            # Set default hours if not provided
            if not entry_dict.get('hours'):
                entry_dict['hours'] = 0.0

            logger.debug("Creating TimeEntry model instance")
            db_entry = TimeEntry(**entry_dict)

            logger.debug("Adding entry to database session")
            self.db.add(db_entry)

            logger.debug("Committing transaction")
            self.db.commit()

            logger.debug("Refreshing database entry")
            self.db.refresh(db_entry)

            logger.info(f"Successfully created time entry [{db_entry.id}] for {db_entry.customer} - {db_entry.project} ({db_entry.hours} hours)")
            return db_entry
        except Exception as e:
            logger.error(f"Error creating time entry: {str(e)}")
            logger.debug("Rolling back transaction")
            self.db.rollback()
            raise

    def create_many_entries(self, entries: List[schemas.TimeEntryCreate]) -> List[TimeEntry]:
        """Create multiple time entries in a single transaction."""
        created_entries = []
        logger.info(f"Beginning bulk creation of {len(entries)} time entries")
        try:
            for idx, entry in enumerate(entries, 1):
                logger.debug(f"Processing entry {idx}/{len(entries)}")
                db_entry = self.create_time_entry(entry)
                created_entries.append(db_entry)
                logger.debug(f"Added entry {idx} to session: {db_entry.customer} - {db_entry.project}")

            total_hours = sum(entry.hours for entry in entries)
            logger.info(f"Successfully created {len(created_entries)} time entries (Total: {total_hours} hours)")
            return created_entries
        except Exception as e:
            logger.error(f"Error during bulk creation: {str(e)}")
            logger.debug("Rolling back transaction")
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
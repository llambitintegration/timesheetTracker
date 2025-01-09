from sqlalchemy.orm import Session
from typing import List, Optional
from database import schemas
from models.timeEntry import TimeEntry
from utils.logger import Logger
from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT, normalize_customer_name, normalize_project_id

logger = Logger().get_logger()

class TimeEntryService:
    def __init__(self, db: Session):
        self.db = db
        logger.debug("TimeEntryService initialized with database session")

    def create_time_entry(self, entry: schemas.TimeEntryCreate) -> TimeEntry:
        """Create a new time entry with proper validation and defaults."""
        try:
            logger.debug(f"Starting creation of time entry with data: {entry.model_dump()}")
            entry_dict = entry.model_dump()

            # Handle default values for customer and project
            if not entry_dict.get('customer'):
                logger.info("No customer provided, defaulting to Unassigned")
                entry_dict['customer'] = DEFAULT_CUSTOMER
            else:
                entry_dict['customer'] = normalize_customer_name(entry_dict['customer'])

            if not entry_dict.get('project'):
                logger.info("No project provided, defaulting to Unassigned")
                entry_dict['project'] = DEFAULT_PROJECT
            else:
                entry_dict['project'] = normalize_project_id(entry_dict['project'])

            logger.debug("Validating and setting default categories")
            if not entry_dict.get('category'):
                logger.info("No category provided, defaulting to 'Other'")
                entry_dict['category'] = 'Other'
            if not entry_dict.get('subcategory'):
                logger.info("No subcategory provided, defaulting to 'General'")
                entry_dict['subcategory'] = 'General'

            logger.debug("Creating TimeEntry model instance")
            db_entry = TimeEntry(**entry_dict)

            logger.debug("Adding entry to database session")
            self.db.add(db_entry)

            logger.debug("Committing transaction")
            self.db.commit()

            logger.debug("Refreshing database entry")
            self.db.refresh(db_entry)

            logger.info(f"Successfully created time entry [{db_entry.id}] for {entry_dict['customer']} - {entry_dict['project']} ({entry_dict['hours']} hours)")
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
            query = query.filter(TimeEntry.project == project_id)
        if customer_name:
            logger.debug(f"Applying customer filter: {customer_name}")
            query = query.filter(TimeEntry.customer == customer_name)

        logger.debug(f"Applying pagination: skip={skip}, limit={limit}")
        results = query.offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(results)} time entries")
        return results
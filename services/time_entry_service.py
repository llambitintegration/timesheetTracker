` line at the beginning.  It also adds the missing `from utils.xls_analyzer import XLSAnalyzer` import statement needed for the `process_excel_upload` function. The rest of the original code is kept intact, as indicated by the comment in the edited snippet.

The combination will involve replacing the first line of the original file with the corrected imports and logger initialization from the edited snippet, and then appending the rest of the original file's content.


<replit_final_file>
from sqlalchemy.orm import Session
from typing import List, Optional
from database import schemas
from models.timeEntry import TimeEntry
from utils.logger import Logger
from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT, normalize_customer_name, normalize_project_id
from database.customer_repository import CustomerRepository
from database.project_repository import ProjectRepository
from typing import List, Dict, Any, Tuple
from tqdm import tqdm
import asyncio
from fastapi import HTTPException, BackgroundTasks
from datetime import datetime
from utils.xls_analyzer import XLSAnalyzer

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
            logger.debug("No customer name or dash provided, using default")
            return DEFAULT_CUSTOMER

        try:
            normalized_name = normalize_customer_name(customer_name)
            if not normalized_name:
                logger.warning("Customer name normalization failed, using default")
                return DEFAULT_CUSTOMER

            # Check if customer exists
            existing = self.customer_repo.get_by_name(self.db, normalized_name)
            if not existing:
                # Create new customer
                customer_data = schemas.CustomerCreate(
                    name=normalized_name,
                    contact_email=f"{normalized_name.lower().replace(' ', '_')}@example.com",
                    status="active"
                )
                new_customer = self.customer_repo.create(self.db, customer_data.model_dump())
                self.db.refresh(new_customer)
                logger.info(f"Created new customer: {normalized_name}")
            return normalized_name
        except Exception as e:
            logger.error(f"Error ensuring customer exists: {str(e)}")
            return DEFAULT_CUSTOMER

    def _ensure_project_exists(self, project_id: str, customer_name: str) -> str:
        """Ensure project exists, create if not. Return normalized project ID."""
        if not project_id or project_id == '-':
            logger.debug("No project ID or dash provided, using default")
            return DEFAULT_PROJECT

        try:
            normalized_id = normalize_project_id(project_id)
            if not normalized_id:
                logger.warning("Project ID normalization failed, using default")
                return DEFAULT_PROJECT

            # Check if project exists
            existing = self.project_repo.get_by_project_id(self.db, normalized_id)
            if existing:
                # Verify project belongs to customer
                if existing.customer != customer_name:
                    logger.warning(f"Project {normalized_id} does not belong to customer {customer_name}")
                    return DEFAULT_PROJECT
                return normalized_id

            # Create new project with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    project_data = schemas.ProjectCreate(
                        project_id=normalized_id,
                        name=normalized_id,
                        customer=customer_name,
                        project_manager='-',  # Explicitly set default project manager
                        status="active"
                    )
                    self.project_repo.create(self.db, project_data)
                    logger.info(f"Created new project: {normalized_id} for customer: {customer_name}")
                    return normalized_id
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to create project {normalized_id} after {max_retries} attempts: {str(e)}")
                        return DEFAULT_PROJECT
                    logger.warning(f"Retry {attempt + 1} for project creation {normalized_id}: {str(e)}")
                    self.db.rollback()

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

    async def process_entries_chunk(
        self,
        entries: List[schemas.TimeEntryCreate],
        progress_key: str
    ) -> List[TimeEntry]:
        """Process a chunk of entries with progress tracking."""
        created_entries = []
        total = len(entries)

        try:
            # Pre-process unique customers and projects
            unique_customers = {entry.customer for entry in entries if entry.customer}
            unique_projects = {entry.project for entry in entries if entry.project}

            # Bulk create customers
            for customer in unique_customers:
                if customer and customer != DEFAULT_CUSTOMER:
                    try:
                        normalized_name = normalize_customer_name(customer)
                        if not self.customer_repo.get_by_name(self.db, normalized_name):
                            customer_data = schemas.CustomerCreate(
                                name=normalized_name,
                                contact_email=f"{normalized_name.lower().replace(' ', '_')}@example.com",
                                status="active"
                            )
                            self.customer_repo.create(self.db, customer_data.model_dump())
                    except Exception as e:
                        logger.error(f"Error creating customer {customer}: {str(e)}")

            # Bulk create projects
            for project in unique_projects:
                if project and project != DEFAULT_PROJECT:
                    try:
                        normalized_id = normalize_project_id(project)
                        if not self.project_repo.get_by_project_id(self.db, normalized_id):
                            customer = next(
                                (entry.customer for entry in entries if entry.project == project),
                                DEFAULT_CUSTOMER
                            )
                            project_data = schemas.ProjectCreate(
                                project_id=normalized_id,
                                name=normalized_id,
                                customer=customer,
                                project_manager='-',
                                status="active"
                            )
                            self.project_repo.create(self.db, project_data)
                    except Exception as e:
                        logger.error(f"Error creating project {project}: {str(e)}")

            # Bulk create time entries
            entries_to_create = []
            for entry in entries:
                try:
                    entry_dict = entry.model_dump(exclude={'id', 'created_at', 'updated_at'})
                    entries_to_create.append(TimeEntry(**entry_dict))
                except Exception as e:
                    logger.error(f"Error preparing time entry: {str(e)}")
                    continue

            if entries_to_create:
                self.db.bulk_save_objects(entries_to_create)
                self.db.commit()
                created_entries.extend(entries_to_create)

            # Update progress
            progress = (len(created_entries) / total) * 100
            await self.update_progress(progress_key, progress)

            return created_entries

        except Exception as e:
            logger.error(f"Error in bulk processing: {str(e)}")
            self.db.rollback()
            raise

    async def update_progress(self, progress_key: str, progress: float):
        """Update progress in Redis or similar storage."""
        # In a real implementation, this would store progress in Redis or similar
        # For now, we'll just log it
        logger.info(f"Upload progress {progress_key}: {progress:.2f}%")

    async def process_excel_upload(
        self,
        file_contents: bytes,
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """Process Excel upload with progress tracking."""
        try:
            analyzer = XLSAnalyzer()
            records, total_rows = analyzer.read_excel(file_contents)

            if not records:
                raise ValueError("No valid records found in Excel file")

            # Generate unique progress key
            progress_key = f"upload_{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Convert records to TimeEntryCreate instances
            entries = []
            for record in records:
                try:
                    entry_data = schemas.TimeEntryCreate(
                        date=record['Date'],
                        week_number=record['Week Number'],
                        month=record['Month'],
                        category=record['Category'],
                        subcategory=record['Subcategory'],
                        customer=record['Customer'],
                        project=record['Project'],
                        task_description=record['Task Description'],
                        hours=record['Hours']
                    )
                    entries.append(entry_data)
                except Exception as e:
                    logger.error(f"Error creating entry data: {str(e)}")
                    continue

            # Process in chunks of 1000
            chunk_size = 1000
            chunks = [entries[i:i + chunk_size] for i in range(0, len(entries), chunk_size)]

            all_created_entries = []
            for chunk in chunks:
                created_entries = await self.process_entries_chunk(chunk, progress_key)
                all_created_entries.extend(created_entries)

            return {
                "status": "success",
                "total_processed": len(all_created_entries),
                "total_records": total_rows,
                "progress_key": progress_key
            }

        except Exception as e:
            logger.error(f"Error processing Excel upload: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

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
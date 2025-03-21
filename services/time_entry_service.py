from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, BackgroundTasks
from datetime import datetime, date
from database import schemas
from models.timeEntry import TimeEntry
from utils.logger import Logger
from utils.validators import normalize_customer_name, normalize_project_id
from database.customer_repository import CustomerRepository
from database.project_repository import ProjectRepository
from utils.xls_analyzer import XLSAnalyzer
from tqdm import tqdm

logger = Logger().get_logger()

class TimeEntryService:
    def __init__(self, db: Session):
        self.db = db
        self.customer_repo = CustomerRepository()
        self.project_repo = ProjectRepository()
        logger.debug("TimeEntryService initialized with database session")

    def _ensure_customer_exists(self, customer_name: Optional[str]) -> Optional[str]:
        """Ensure customer exists, create if not. Return normalized customer name or None."""
        try:
            if not customer_name:
                logger.debug("No customer name provided")
                return None

            normalized_name = normalize_customer_name(customer_name)
            if not normalized_name:
                logger.debug("Customer name normalization returned None")
                return None

            # Check if customer exists
            existing = self.customer_repo.get_by_name(self.db, normalized_name)
            if not existing:
                # Create new customer
                customer_data = schemas.CustomerCreate(
                    name=normalized_name,
                    contact_email=f"{normalized_name.lower().replace(' ', '_')}@example.com",
                    status="active"
                )
                new_customer = self.customer_repo.create(self.db, customer_data)
                logger.info(f"Created new customer: {normalized_name}")
            return normalized_name
        except Exception as e:
            logger.error(f"Error ensuring customer exists: {str(e)}")
            return None

    def _ensure_project_exists(self, project_id: Optional[str], customer_name: Optional[str]) -> Optional[str]:
        """Ensure project exists, create if not. Return normalized project ID or None."""
        try:
            if not project_id:
                logger.debug("No project ID provided")
                return None

            normalized_id = normalize_project_id(project_id)
            if not normalized_id:
                logger.debug("Project ID normalization returned None")
                return None

            # Check if project exists
            existing = self.project_repo.get_by_project_id(self.db, normalized_id)
            if not existing:
                # Create new project
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
            logger.error(f"Error ensuring project exists: {str(e)}")
            return None

    def create_time_entry(self, entry: schemas.TimeEntryCreate) -> TimeEntry:
        """Create a new time entry with proper validation."""
        try:
            logger.debug(f"Starting creation of time entry with data: {entry.model_dump()}")

            # Validate and normalize customer if provided
            customer_name = self._ensure_customer_exists(entry.customer)

            # Validate and normalize project if provided
            project_id = self._ensure_project_exists(entry.project, customer_name)

            # Set default hours if not provided
            if entry.hours is None:
                entry.hours = 0.0
                logger.debug("No hours provided, defaulting to 0.0")

            # Create entry with validated customer and project
            entry_dict = entry.model_dump(exclude={'id', 'created_at', 'updated_at'})
            entry_dict.update({
                'customer': customer_name,
                'project': project_id
            })

            # Create TimeEntry instance
            db_entry = TimeEntry(**entry_dict)

            logger.debug("Adding entry to database session")
            self.db.add(db_entry)
            self.db.commit()
            self.db.refresh(db_entry)

            logger.info(f"Successfully created time entry for {customer_name} - {project_id}")
            return db_entry

        except Exception as e:
            logger.error(f"Error creating time entry: {str(e)}")
            self.db.rollback()
            raise

    def bulk_create(self, db: Session, entries: List[schemas.TimeEntryCreate]) -> List[TimeEntry]:
        """Bulk create time entries."""
        created_entries = []
        try:
            logger.debug(f"Starting bulk creation of {len(entries)} time entries")

            for entry in entries:
                try:
                    # Use create_time_entry for consistent validation and creation
                    db_entry = self.create_time_entry(entry)
                    created_entries.append(db_entry)
                except Exception as e:
                    logger.error(f"Error creating entry in bulk operation: {str(e)}")
                    # Continue with next entry instead of failing entire batch
                    continue

            logger.info(f"Successfully created {len(created_entries)} time entries in bulk")
            return created_entries

        except Exception as e:
            logger.error(f"Error in bulk create operation: {str(e)}")
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
            # Pre-process unique customers and projects for batch creation
            unique_customers = {
                normalize_customer_name(entry.customer)
                for entry in entries
                if entry.customer
            }
            unique_projects = {
                normalize_project_id(entry.project)
                for entry in entries
                if entry.project
            }

            # Create customers in bulk
            for customer_name in unique_customers:
                if not customer_name:
                    continue
                try:
                    if not self.customer_repo.get_by_name(self.db, customer_name):
                        customer_data = schemas.CustomerCreate(
                            name=customer_name,
                            contact_email=f"{customer_name.lower().replace(' ', '_')}@example.com",
                            status="active"
                        )
                        self.customer_repo.create(self.db, customer_data)
                        logger.info(f"Created new customer: {customer_name}")
                except Exception as e:
                    logger.error(f"Error creating customer {customer_name}: {str(e)}")

            # Create projects in bulk
            for project_id in unique_projects:
                if not project_id:
                    continue
                try:
                    if not self.project_repo.get_by_project_id(self.db, project_id):
                        # Find the associated customer for this project
                        project_entries = [e for e in entries if normalize_project_id(e.project) == project_id]
                        if project_entries:
                            customer_name = normalize_customer_name(project_entries[0].customer)
                            project_data = schemas.ProjectCreate(
                                project_id=project_id,
                                name=project_id,
                                customer=customer_name,
                                status="active"
                            )
                            self.project_repo.create(self.db, project_data)
                            logger.info(f"Created new project: {project_id} for customer: {customer_name}")
                except Exception as e:
                    logger.error(f"Error creating project {project_id}: {str(e)}")

            # Prepare time entries for bulk insert
            entries_to_create = []
            for entry in entries:
                try:
                    # Normalize and validate customer and project
                    normalized_customer = normalize_customer_name(entry.customer)
                    normalized_project = normalize_project_id(entry.project)

                    entry_dict = entry.model_dump(exclude={'id', 'created_at', 'updated_at'})
                    entry_dict.update({
                        'customer': normalized_customer,
                        'project': normalized_project
                    })
                    entries_to_create.append(TimeEntry(**entry_dict))
                except Exception as e:
                    logger.error(f"Error preparing entry: {str(e)}")
                    continue

            # Bulk insert time entries
            if entries_to_create:
                self.db.bulk_save_objects(entries_to_create)
                self.db.commit()
                created_entries.extend(entries_to_create)

            # Update progress
            progress = (len(created_entries) / total) * 100 if total > 0 else 100
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
            records = analyzer.read_excel(file_contents)

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
                        subcategory=record.get('Subcategory', ''),
                        customer=record['Customer'],
                        project=record['Project'],
                        task_description=record['Task Description'],
                        hours=record['Hours']
                    )
                    entries.append(entry_data)
                except Exception as e:
                    logger.error(f"Error creating entry data: {str(e)}")
                    continue

            # Process in chunks of 100 entries
            chunk_size = 100
            chunks = [entries[i:i + chunk_size] for i in range(0, len(entries), chunk_size)]

            # Add background task for processing chunks
            async def process_chunks():
                created_entries = []
                for chunk in chunks:
                    processed_entries = await self.process_entries_chunk(chunk, progress_key)
                    created_entries.extend(processed_entries)
                    # Update progress after each chunk
                    progress = (len(created_entries) / len(entries)) * 100
                    await self.update_progress(progress_key, progress)

            if background_tasks:
                background_tasks.add_task(process_chunks)

            return {
                "message": "Upload processing started",
                "progress_key": progress_key,
                "total_records": len(records)
            }

        except Exception as e:
            logger.error(f"Error processing Excel upload: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    def get_time_entries(
        self,
        date: Optional[date] = None,
        project_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TimeEntry]:
        """Retrieve time entries with filters."""
        logger.debug(f"Retrieving time entries with filters: date={date}, project_id={project_id}, customer={customer_name}")
        query = self.db.query(TimeEntry)

        if date:
            logger.debug(f"Applying date filter: {date}")
            query = query.filter(TimeEntry.date == date)
        if project_id:
            normalized_project = normalize_project_id(project_id)
            if normalized_project:
                logger.debug(f"Applying project filter: {normalized_project}")
                query = query.filter(TimeEntry.project == normalized_project)
        if customer_name:
            normalized_customer = normalize_customer_name(customer_name)
            if normalized_customer:
                logger.debug(f"Applying customer filter: {normalized_customer}")
                query = query.filter(TimeEntry.customer == normalized_customer)

        logger.debug(f"Applying pagination: skip={skip}, limit={limit}")
        results = query.offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(results)} time entries")
        return results

    def update_entry(self, entry_id: int, entry: schemas.TimeEntryUpdate) -> Optional[TimeEntry]:
        """Update an existing time entry."""
        try:
            logger.debug(f"Attempting to update time entry {entry_id}")
            db_entry = self.db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()

            if not db_entry:
                logger.warning(f"Time entry {entry_id} not found")
                return None

            update_data = entry.model_dump(exclude_unset=True)

            # Validate and normalize customer if provided
            if 'customer' in update_data:
                update_data['customer'] = self._ensure_customer_exists(update_data['customer'])

            # Validate and normalize project if provided
            if 'project' in update_data:
                update_data['project'] = self._ensure_project_exists(
                    update_data['project'],
                    update_data.get('customer', db_entry.customer)
                )

            # Validate hours
            if 'hours' in update_data and (
                update_data['hours'] < 0 or 
                update_data['hours'] > 24
            ):
                raise ValueError("Hours must be between 0 and 24")

            # Update the entry
            for key, value in update_data.items():
                setattr(db_entry, key, value)

            self.db.commit()
            self.db.refresh(db_entry)
            logger.info(f"Successfully updated time entry {entry_id}")
            return db_entry

        except Exception as e:
            logger.error(f"Error updating time entry {entry_id}: {str(e)}")
            self.db.rollback()
            raise ValueError(str(e))

    def delete_entry(self, entry_id: int) -> bool:
        """Delete a time entry."""
        try:
            logger.debug(f"Attempting to delete time entry {entry_id}")
            db_entry = self.db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()

            if not db_entry:
                logger.warning(f"Time entry {entry_id} not found")
                return False

            self.db.delete(db_entry)
            self.db.commit()
            logger.info(f"Successfully deleted time entry {entry_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting time entry {entry_id}: {str(e)}")
            self.db.rollback()
            raise
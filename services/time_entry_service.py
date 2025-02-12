from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException
from datetime import datetime, date
from database import schemas
from models.timeEntry import TimeEntry
from utils.logger import Logger
from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT, normalize_customer_name, normalize_project_id
from database.customer_repository import CustomerRepository
from database.project_repository import ProjectRepository
from tqdm import tqdm

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
                new_customer = self.customer_repo.create(self.db, customer_data)
                logger.info(f"Created new customer: {normalized_name}")
            return normalized_name
        except Exception as e:
            logger.error(f"Error ensuring customer exists: {str(e)}")
            return DEFAULT_CUSTOMER

    def _ensure_project_exists(self, project_id: str, customer_name: str) -> str:
        """Ensure project exists, create if not. Return normalized project ID."""
        try:
            if not project_id or project_id == '-':
                logger.debug("No project ID or dash provided, using default")
                return DEFAULT_PROJECT

            normalized_id = normalize_project_id(project_id)
            if not normalized_id:
                logger.warning("Project ID normalization failed, using default")
                return DEFAULT_PROJECT

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
            return DEFAULT_PROJECT

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
                if entry.customer and entry.customer != DEFAULT_CUSTOMER
            }
            unique_projects = {
                normalize_project_id(entry.project)
                for entry in entries
                if entry.project and entry.project != DEFAULT_PROJECT
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
                                customer=customer_name or DEFAULT_CUSTOMER,
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
                    normalized_customer = normalize_customer_name(entry.customer) if entry.customer else DEFAULT_CUSTOMER
                    normalized_project = normalize_project_id(entry.project) if entry.project else DEFAULT_PROJECT

                    # If project doesn't exist, use default project and customer
                    if not self.project_repo.get_by_project_id(self.db, normalized_project):
                        normalized_project = DEFAULT_PROJECT
                        normalized_customer = DEFAULT_CUSTOMER

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
        project_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[TimeEntry]:
        """Retrieve time entries with filters."""
        logger.debug(f"Retrieving time entries with filters: project_id={project_id}, customer={customer_name}, date={date}")
        query = self.db.query(TimeEntry)

        try:
            if project_id:
                logger.debug(f"Applying project filter: {project_id}")
                normalized_project = normalize_project_id(project_id)
                query = query.filter(TimeEntry.project == normalized_project)

            if customer_name:
                logger.debug(f"Applying customer filter: {customer_name}")
                normalized_customer = normalize_customer_name(customer_name)
                query = query.filter(TimeEntry.customer == normalized_customer)

            if date:
                logger.debug(f"Applying date filter: {date}")
                query = query.filter(TimeEntry.date == date)

            logger.debug(f"Applying pagination: skip={skip}, limit={limit}")
            results = query.offset(skip).limit(limit).all()
            logger.info(f"Retrieved {len(results)} time entries")
            return results

        except Exception as e:
            logger.error(f"Error retrieving time entries: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error retrieving time entries: {str(e)}")

    def create_time_entry(self, entry: schemas.TimeEntryCreate) -> TimeEntry:
        """Create a new time entry."""
        try:
            logger.debug(f"Creating time entry: {entry.model_dump()}")
            db_entry = TimeEntry(**entry.model_dump())
            self.db.add(db_entry)
            self.db.commit()
            self.db.refresh(db_entry)
            return db_entry
        except Exception as e:
            logger.error(f"Error creating time entry: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def update_time_entry(self, entry_id: int, entry: schemas.TimeEntryUpdate) -> TimeEntry:
        """Update an existing time entry."""
        try:
            logger.debug(f"Updating time entry {entry_id}")
            db_entry = self.db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
            if not db_entry:
                raise HTTPException(status_code=404, detail="Time entry not found")

            update_data = entry.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_entry, key, value)

            self.db.commit()
            self.db.refresh(db_entry)
            return db_entry
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating time entry: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def delete_time_entry(self, entry_id: int) -> bool:
        """Delete a time entry."""
        try:
            logger.debug(f"Deleting time entry {entry_id}")
            db_entry = self.db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
            if not db_entry:
                raise HTTPException(status_code=404, detail="Time entry not found")

            self.db.delete(db_entry)
            self.db.commit()
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting time entry: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Union, BinaryIO, Tuple, Optional
from io import StringIO, BytesIO
import utils
from database import crud, schemas
from utils.logger import Logger
from models.timeEntry import TimeEntry
from database.timesheet_repository import TimeEntryRepository
from database.customer_repository import CustomerRepository
from database.project_repository import ProjectRepository
from utils.xls_analyzer import XLSAnalyzer
from utils.validators import normalize_customer_name, normalize_project_id
from datetime import datetime
import json
from decimal import Decimal
import pandas as pd

logger = Logger().get_logger()

class TimesheetService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TimeEntryRepository()
        self.customer_repo = CustomerRepository()
        self.project_repo = ProjectRepository()
        logger.debug("TimesheetService initialized")

    def create_entry(self, entry: schemas.TimeEntryCreate) -> TimeEntry:
        """Create a new time entry"""
        try:
            # Normalize customer and project values
            entry.customer = normalize_customer_name(entry.customer)
            entry.project = normalize_project_id(entry.project)

            # Create entry in the database
            return self.repository.create(self.db, entry)
        except Exception as e:
            logger.error(f"Error creating time entry: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    def _serialize_time_entry(self, entry: TimeEntry) -> Dict[str, Any]:
        """Serialize a TimeEntry object to a dictionary"""
        return {
            "id": entry.id,
            "week_number": entry.week_number,
            "month": entry.month,
            "category": entry.category,
            "subcategory": entry.subcategory,
            "customer": entry.customer,
            "project": entry.project,
            "task_description": entry.task_description,
            "hours": float(entry.hours) if entry.hours is not None else None,
            "date": entry.date.strftime("%Y-%m-%d") if entry.date else None,
            "created_at": entry.created_at.strftime("%Y-%m-%dT%H:%M:%S") if entry.created_at else None,
            "updated_at": entry.updated_at.strftime("%Y-%m-%dT%H:%M:%S") if entry.updated_at else None
        }

    def _bulk_create_entries(self, entries: List[schemas.TimeEntryCreate]) -> List[Dict[str, Any]]:
        """Bulk create time entries in a single transaction"""
        try:
            created_entries = []

            # Process all entries first to ensure customers and projects exist
            processed_entries = []
            for entry in entries:
                # Create customer if not exists and customer is provided
                if entry.customer:
                    customer = self.customer_repo.get_by_name(self.db, entry.customer)
                    if not customer:
                        customer_data = schemas.CustomerCreate(
                            name=entry.customer,
                            contact_email=f"{entry.customer.lower().replace(' ', '_')}@example.com",
                            status="active"
                        )
                        customer = self.customer_repo.create(self.db, customer_data)
                        logger.info(f"Created new customer: {customer.name}")

                # Create project if not exists and project is provided
                if entry.project and entry.customer:
                    project = self.project_repo.get_by_project_id(self.db, entry.project)
                    if not project:
                        project_data = schemas.ProjectCreate(
                            project_id=entry.project,
                            name=entry.project,
                            customer=entry.customer,
                            status="active"
                        )
                        project = self.project_repo.create(self.db, project_data)
                        logger.info(f"Created new project: {project.project_id} for customer: {entry.customer}")

                processed_entries.append(entry)

            # Now create all time entries
            for entry in processed_entries:
                entry_dict = {k: v for k, v in entry.model_dump().items() if k not in {'id', 'created_at', 'updated_at'}}
                db_entry = TimeEntry(**entry_dict)
                self.db.add(db_entry)
                created_entries.append(db_entry)

            self.db.commit()
            return [self._serialize_time_entry(entry) for entry in created_entries]

        except Exception as e:
            logger.error(f"Error during bulk creation: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error during bulk creation: {str(e)}")

    async def upload_timesheet(self, file: UploadFile) -> Dict[str, Any]:
        """Upload and process timesheet file"""
        logger.info(f"Processing timesheet upload: {file.filename}")

        try:
            contents = await file.read()
            if not contents:
                raise HTTPException(status_code=400, detail="Empty file provided")

            if not file.filename.lower().endswith('.xlsx'):
                raise HTTPException(
                    status_code=400,
                    detail="Only Excel (.xlsx) files are supported"
                )

            entries = self.repository.import_excel(self.db, contents)
            if not entries:
                logger.warning("No valid entries found in file")
                raise HTTPException(
                    status_code=400,
                    detail="No valid entries found in the file"
                )

            logger.info(f"Processing {len(entries)} entries")
            entry_creates = [
                schemas.TimeEntryCreate(
                    category=entry.category,
                    subcategory=entry.subcategory,
                    customer=normalize_customer_name(entry.customer),
                    project=normalize_project_id(entry.project),
                    task_description=entry.task_description,
                    hours=entry.hours,
                    date=entry.date
                ) for entry in entries
            ]

            created_entries = self._bulk_create_entries(entry_creates)
            logger.info(f"Successfully created {len(created_entries)} time entries")

            return {
                "entries": created_entries,
                "message": "Upload successful"
            }

        except ValueError as e:
            logger.error(f"Error processing timesheet: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing timesheet: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    def get_entries(self, skip: int = 0, limit: int = 100) -> List[TimeEntry]:
        """Get paginated time entries"""
        return crud.get_time_entries(self.db, skip=skip, limit=limit)

    def get_entries_by_date(self, date: datetime) -> List[TimeEntry]:
        """Get time entries for a specific date"""
        try:
            entries = crud.get_time_entries_by_date(self.db, date)
            if not entries:
                logger.info(f"No entries found for date: {date}")
                return []
            logger.info(f"Found {len(entries)} entries for date: {date}")
            return entries
        except Exception as e:
            logger.error(f"Error fetching time entries for date {date}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def update_entry(self, entry_id: int, entry: schemas.TimeEntryUpdate) -> TimeEntry:
        """Update an existing time entry"""
        db_entry = crud.get_time_entry(self.db, entry_id)
        if not db_entry:
            raise HTTPException(status_code=404, detail="Time entry not found")
        return crud.update_time_entry(self.db, db_entry, entry)

    def delete_entry(self, entry_id: int) -> Dict[str, str]:
        """Delete a time entry"""
        db_entry = crud.get_time_entry(self.db, entry_id)
        if not db_entry:
            raise HTTPException(status_code=404, detail="Time entry not found")
        crud.delete_time_entry(self.db, db_entry)
        return {"message": "Time entry deleted successfully"}

    def _process_dataframe(self, df: "pd.DataFrame") -> List[schemas.TimeEntryCreate]:
        """Process pandas DataFrame into time entries"""
        required_columns = {
            'Week Number', 'Month', 'Category', 'Subcategory',
            'Task Description', 'Hours', 'Date'
        }

        # Check for required columns
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )

        valid_entries = []
        for idx, row in df.iterrows():
            try:
                hours = float(row['Hours'])
                if hours <= 0 or hours > 24:
                    logger.warning(f"Invalid hours value in row {idx + 1}: {hours}")
                    continue

                entry_dict = {
                    'week_number': int(row['Week Number']) if 'Week Number' in row else 0,
                    'month': str(row['Month']) if 'Month' in row else '',
                    'category': str(row['Category']),
                    'subcategory': str(row['Subcategory']) if 'Subcategory' in row else '',
                    'customer': normalize_customer_name(row['Customer']) if 'Customer' in row else None,
                    'project': normalize_project_id(row['Project']) if 'Project' in row else None,
                    'task_description': str(row['Task Description']) if 'Task Description' in row else '',
                    'hours': hours,
                    'date': pd.to_datetime(row['Date']).date()
                }
                valid_entries.append(schemas.TimeEntryCreate(**entry_dict))
            except Exception as e:
                logger.error(f"Error processing row {idx + 1}: {str(e)}")
                continue

        return valid_entries
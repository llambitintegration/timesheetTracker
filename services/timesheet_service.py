from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Union, BinaryIO, Tuple, Optional
from io import StringIO, BytesIO
import utils
from database import crud, schemas
from utils.logger import Logger
from models.timeEntry import TimeEntry
from database.timesheet_repository import TimeEntryRepository
import pandas as pd
from utils.validators import validate_database_references
from datetime import datetime
import json
from decimal import Decimal

logger = Logger().get_logger()

class TimesheetService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TimeEntryRepository()
        logger.debug("TimesheetService initialized")

    def create_entry(self, entry: schemas.TimeEntryCreate) -> TimeEntry:
        """Create a new time entry"""
        return self.repository.create(self.db, entry)

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
            # Prepare all entries first
            db_entries = [
                TimeEntry(**entry.model_dump(exclude={'id', 'created_at', 'updated_at'}))
                for entry in entries
            ]

            # Add all entries in a single batch
            self.db.add_all(db_entries)
            self.db.commit()

            # Serialize all entries after successful commit
            return [self._serialize_time_entry(entry) for entry in db_entries]
        except Exception as e:
            logger.error(f"Error during bulk creation: {str(e)}")
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error during bulk creation: {str(e)}")

    async def upload_timesheet(self, file: UploadFile) -> Dict[str, Any]:
        """Upload and process timesheet file with bulk upload support"""
        logger.info(f"Processing timesheet upload: {file.filename}")
        validation_errors: List[Dict[str, Any]] = []

        try:
            contents = await file.read()
            if not contents:
                raise HTTPException(status_code=400, detail="Empty file provided")

            file_extension = file.filename.lower().split('.')[-1]

            if file_extension == 'xlsx':
                entries = self._process_excel(contents)
            elif file_extension in ['csv', 'txt']:
                entries = utils.parse_csv(StringIO(contents.decode('utf-8')))
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file format: {file_extension}. Supported formats are: xlsx, csv, txt"
                )

            if not entries:
                logger.warning("No valid entries found in file")
                raise HTTPException(
                    status_code=400,
                    detail="No valid entries found in the file"
                )

            logger.info(f"Processing {len(entries)} entries")
            validated_entries, db_validation_errors = validate_database_references(self.db, entries)
            validation_errors.extend(db_validation_errors)

            if not validated_entries:
                raise HTTPException(
                    status_code=400,
                    detail="No valid entries after validation"
                )

            created_entries = self._bulk_create_entries(validated_entries)
            logger.info(f"Successfully created {len(created_entries)} time entries in bulk")

            return {
                "entries": created_entries,
                "validation_errors": validation_errors
            }

        except HTTPException as e:
            logger.error(f"Error processing timesheet: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error processing timesheet: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    def _process_excel(self, contents: bytes) -> List[schemas.TimeEntryCreate]:
        """Process Excel file contents - first worksheet only"""
        try:
            df = pd.read_excel(BytesIO(contents), sheet_name=0)  # Only read first worksheet
            return self._process_dataframe(df)
        except Exception as e:
            logger.error(f"Error processing Excel file: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Error processing Excel file: {str(e)}"
            )

    def _process_dataframe(self, df: pd.DataFrame) -> List[schemas.TimeEntryCreate]:
        """Process pandas DataFrame into time entries"""
        required_columns = {
            'Week Number', 'Month', 'Category', 'Subcategory',
            'Customer', 'Project', 'Task Description', 'Hours', 'Date'
        }

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
                    'week_number': int(row['Week Number']),
                    'month': str(row['Month']),
                    'category': str(row['Category']),
                    'subcategory': str(row['Subcategory']),
                    'customer': str(row['Customer']),
                    'project': str(row['Project']),
                    'task_description': str(row['Task Description']),
                    'hours': hours,
                    'date': pd.to_datetime(row['Date']).date()
                }
                valid_entries.append(schemas.TimeEntryCreate(**entry_dict))
            except Exception as e:
                logger.error(f"Error processing row {idx + 1}: {str(e)}")
                continue

        return valid_entries

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
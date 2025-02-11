from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Union
from io import StringIO, BytesIO
import utils
from database import crud, schemas
from utils.logger import Logger
from models.timeEntry import TimeEntry
from database.timesheet_repository import TimeEntryRepository

logger = Logger().get_logger()

class TimesheetService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TimeEntryRepository()

    def create_entry(self, entry: schemas.TimeEntryCreate) -> TimeEntry:
        """Create a new time entry"""
        return self.repository.create(self.db, entry)

    async def upload_timesheet(self, file: UploadFile) -> Dict[str, Any]:
        """Upload and process timesheet file"""
        logger.info(f"Processing timesheet upload: {file.filename}")
        validation_errors = []

        try:
            contents = await file.read()
            # Accept both .txt and traditional spreadsheet formats
            if file.filename.endswith(('.txt', '.csv')):
                text_contents = contents.decode('utf-8')
                entries = utils.parse_csv(StringIO(text_contents))
            elif file.filename.endswith('.xlsx'):
                entries = utils.parse_excel(BytesIO(contents))
            else:
                logger.error(f"Unsupported file format: {file.filename}")
                raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a .txt, .csv, or .xlsx file.")

            if not entries:
                logger.warning("No valid entries found in file")
                return {"entries": [], "validation_errors": ["No valid entries found in the file"]}

            created_entries = []
            for entry in entries:
                try:
                    created_entry = crud.create_time_entry(self.db, entry)
                    created_entries.append(created_entry)
                except Exception as e:
                    logger.error(f"Error creating entry: {str(e)}")
                    validation_errors.append({
                        "entry": entry.dict(),
                        "error": str(e)
                    })

            logger.info(f"Successfully created {len(created_entries)} time entries")
            return {
                "entries": created_entries,
                "validation_errors": validation_errors
            }
        except Exception as e:
            logger.error(f"Error processing timesheet: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    def get_entries(self, skip: int = 0, limit: int = 100) -> List[TimeEntry]:
        return crud.get_time_entries(self.db, skip=skip, limit=limit)

    def get_entries_by_date(self, date) -> List[TimeEntry]:
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
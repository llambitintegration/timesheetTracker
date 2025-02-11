from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List
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

    async def upload_timesheet(self, file: UploadFile) -> List[schemas.TimeEntry]:
        """Upload and process timesheet file"""
        logger.info(f"Processing timesheet upload: {file.filename}")
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
                return []

            created_entries = crud.create_time_entries(self.db, entries)
            logger.info(f"Successfully created {len(created_entries)} time entries")
            return created_entries
        except Exception as e:
            logger.error(f"Error processing timesheet: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    def get_entries(self, skip: int = 0, limit: int = 100) -> List[schemas.TimeEntry]:
        return crud.get_time_entries(self.db, skip=skip, limit=limit)

    def get_entries_by_date(self, date) -> List[schemas.TimeEntry]:
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
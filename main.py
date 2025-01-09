from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, date
import calendar
from dotenv import load_dotenv

from database import schemas, crud, get_db, verify_database, engine
from utils.logger import Logger
from utils import utils
from models import TimeEntry

logger = Logger().get_logger()
app = FastAPI(title="Timesheet Management API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

load_dotenv()

@app.on_event("startup")
async def startup_event():
    """Verify database connection on startup"""
    logger.info("Verifying database connection on startup")
    try:
        if not verify_database():
            logger.warning("Database verification failed - schema may need initialization")
    except Exception as e:
        logger.error(f"Error verifying database: {str(e)}")
        raise

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to Timesheet Management API",
        "documentation": "/docs",
        "redoc": "/redoc"
    }

@app.post("/time-entries/upload", response_model=List[schemas.TimeEntry])
async def upload_timesheet_entries(
    entries: List[schemas.TimeEntryCreate],
    db: Session = Depends(get_db)
):
    """Upload multiple time entries directly."""
    logger.info(f"Processing {len(entries)} time entries")
    return crud.create_time_entries(db, entries)

@app.post("/upload/", response_model=List[schemas.TimeEntry])
async def upload_timesheet(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process timesheet file"""
    logger.info(f"Processing timesheet upload: {file.filename}")
    try:
        if file.filename.endswith('.xlsx'):
            entries = utils.parse_excel(file.file)
        elif file.filename.endswith('.csv'):
            entries = utils.parse_csv(file.file)
        else:
            logger.error(f"Unsupported file format: {file.filename}")
            raise HTTPException(status_code=400, detail="Unsupported file format")

        if not entries:
            raise HTTPException(status_code=400, detail="No valid entries found in file")

        created_entries = crud.create_time_entries(db, entries)
        logger.info(f"Successfully created {len(created_entries)} time entries")
        return created_entries
    except Exception as e:
        logger.error(f"Error processing timesheet: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/customers/", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating new customer: {customer.name}")
    return crud.create_customer(db, customer)

@app.get("/customers/", response_model=List[schemas.Customer])
def read_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info(f"Fetching customers with skip={skip}, limit={limit}")
    return crud.get_customers(db, skip=skip, limit=limit)

@app.get("/customers/{name}", response_model=schemas.Customer)
def read_customer(name: str, db: Session = Depends(get_db)):
    logger.info(f"Fetching customer: {name}")
    customer = crud.get_customer(db, name)
    if customer is None:
        logger.warning(f"Customer not found: {name}")
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.post("/project-managers/", response_model=schemas.ProjectManager)
def create_project_manager(
    project_manager: schemas.ProjectManagerCreate,
    db: Session = Depends(get_db)
):
    logger.info(f"Creating new project manager: {project_manager.name}")
    return crud.create_project_manager(db, project_manager)

@app.get("/project-managers/", response_model=List[schemas.ProjectManager])
def read_project_managers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    logger.info(f"Fetching project managers with skip={skip}, limit={limit}")
    return crud.get_project_managers(db, skip=skip, limit=limit)

@app.get("/project-managers/{name}", response_model=schemas.ProjectManager)
def read_project_manager(name: str, db: Session = Depends(get_db)):
    logger.info(f"Fetching project manager: {name}")
    project_manager = crud.get_project_manager(db, name)
    if project_manager is None:
        logger.warning(f"Project manager not found: {name}")
        raise HTTPException(status_code=404, detail="Project Manager not found")
    return project_manager

@app.post("/projects/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating new project: {project.project_id}")
    return crud.create_project(db, project)

@app.get("/projects/", response_model=List[schemas.Project])
def read_projects(
    customer_name: Optional[str] = None,
    project_manager_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    logger.info(
        f"Fetching projects with customer={customer_name}, "
        f"manager={project_manager_name}, skip={skip}, limit={limit}"
    )
    return crud.get_projects(db, customer_name, project_manager_name, skip, limit)

@app.get("/projects/{project_id}", response_model=schemas.Project)
def read_project(project_id: str, db: Session = Depends(get_db)):
    logger.info(f"Fetching project: {project_id}")
    project = crud.get_project(db, project_id)
    if project is None:
        logger.warning(f"Project not found: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.post("/init-db/")
async def initialize_database(force: bool = False, db: Session = Depends(get_db)):
    """Initialize database and run migrations"""
    logger.info("Initializing database")
    try:
        if not force and verify_database():
            return {"status": "success", "message": "Database already initialized"}

        from alembic.config import Config
        from alembic import command

        logger.info("Running database migrations")
        alembic_cfg = Config("alembic.ini")
        logger.debug(f"Alembic config loaded from: {alembic_cfg.config_file_name}")
        logger.debug(f"Script location: {alembic_cfg.get_main_option('script_location')}")

        try:
            logger.info("Starting migration process")
            command.upgrade(alembic_cfg, "head")
            logger.info("Migration completed successfully")
        except Exception as migration_error:
            logger.error(f"Migration failed: {str(migration_error)}")
            logger.exception("Migration stack trace:")
            raise

        logger.info("Verifying database state after migration")
        if not verify_database():
            raise Exception("Database verification failed after migration")

        logger.info("Database initialized successfully")
        return {"status": "success", "message": "Database initialized"}
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/time-entries/", response_model=schemas.TimeEntry)
def create_time_entry(entry: schemas.TimeEntryCreate, db: Session = Depends(get_db)):
    logger.info("Creating new time entry")
    return crud.create_time_entry(db, entry)

@app.get("/time-summaries/", response_model=schemas.TimeSummary)
def get_time_summaries(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    project_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get time entries summary within a date range."""
    logger.info(f"Fetching time summaries from {start_date} to {end_date}")
    return crud.get_time_summaries(db, start_date, end_date, project_id, customer_name)

@app.get("/time-entries/by-month/{month}", response_model=schemas.TimeSummary)
def get_time_entries_by_month(
    month: str = Path(..., description="Month name (e.g., January)"),
    year: int = Query(..., description="Year (e.g., 2025)"),
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get time entries for a specific month."""
    logger.info(f"Fetching time entries for {month} {year}")
    return crud.get_time_entries_by_month(db, month, year, project_id)

@app.get("/time-entries/by-week/{week_number}", response_model=schemas.TimeSummary)
def get_time_entries_by_week(
    week_number: int = Path(..., ge=1, le=53),
    year: int = Query(..., description="Year (e.g., 2025)"),
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get time entries for a specific week number."""
    logger.info(f"Fetching time entries for week {week_number} of {year}")
    return crud.get_time_entries_by_week(db, week_number, year, project_id)

@app.get("/time-entries/by-date/{date}", response_model=List[schemas.TimeEntry])
def get_time_entries_by_date(
    date: date,
    db: Session = Depends(get_db)
):
    """
    Get all time entries for a specific date.
    Date format: YYYY-MM-DD
    """
    logger.info(f"Fetching time entries for date: {date}")
    try:
        entries = crud.get_time_entries_by_date(db, date)
        if not entries:
            logger.info(f"No entries found for date: {date}")
            return []
        logger.info(f"Found {len(entries)} entries for date: {date}")
        return entries
    except Exception as e:
        logger.error(f"Error fetching time entries for date {date}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/weekly", response_model=schemas.WeeklyReport)
def get_weekly_report(
    date: datetime = Query(default=None),
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    logger.info(f"Generating weekly report for date={date}, project={project_id}")
    if date is None:
        date = datetime.now()

    week_start = date - timedelta(days=date.weekday())
    week_end = week_start + timedelta(days=6)

    query = db.query(
        models.TimeEntry.project,
        models.TimeEntry.customer,
        db.func.sum(models.TimeEntry.hours).label('total_hours')
    ).filter(
        models.TimeEntry.week_number == week_start.isocalendar()[1]
    ).group_by(
        models.TimeEntry.project,
        models.TimeEntry.customer
    )

    if project_id:
        query = query.filter(models.TimeEntry.project == project_id)

    results = query.all()
    entries = [
        schemas.ReportEntry(
            total_hours=float(r.total_hours),
            category=r.customer or "Unassigned",
            project=r.project,
            period=f"{week_start.date()} to {week_end.date()}"
        )
        for r in results
    ]

    total_hours = sum(entry.total_hours for entry in entries)
    return schemas.WeeklyReport(
        entries=entries,
        total_hours=total_hours,
        week_number=week_start.isocalendar()[1],
        month=calendar.month_name[week_start.month]
    )

@app.get("/reports/monthly", response_model=schemas.MonthlyReport)
def get_monthly_report(
    year: int = Query(...),
    month: int = Query(...),
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    logger.info(f"Generating monthly report for {year}-{month}, project={project_id}")
    query = db.query(
        models.TimeEntry.project,
        models.TimeEntry.customer,
        db.func.sum(models.TimeEntry.hours).label('total_hours')
    ).filter(
        models.TimeEntry.month == calendar.month_name[month]
    ).group_by(
        models.TimeEntry.project,
        models.TimeEntry.customer
    )

    if project_id:
        query = query.filter(models.TimeEntry.project == project_id)

    results = query.all()
    entries = [
        schemas.ReportEntry(
            total_hours=float(r.total_hours),
            category=r.customer or "Unassigned",
            project=r.project,
            period=f"{year}-{month:02d}"
        )
        for r in results
    ]

    total_hours = sum(entry.total_hours for entry in entries)
    return schemas.MonthlyReport(
        entries=entries,
        total_hours=total_hours,
        month=month,
        year=year
    )

@app.get("/time-entries/by-date/{date}", response_model=List[schemas.TimeEntry])
def get_time_entries_by_date(
    date: date,
    db: Session = Depends(get_db)
):
    """
    Get all time entries for a specific date.
    Date format: YYYY-MM-DD
    """
    logger.info(f"Fetching time entries for date: {date}")
    try:
        entries = crud.get_time_entries_by_date(db, date)
        if not entries:
            logger.info(f"No entries found for date: {date}")
            return []
        logger.info(f"Found {len(entries)} entries for date: {date}")
        return entries
    except Exception as e:
        logger.error(f"Error fetching time entries for date {date}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
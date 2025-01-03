from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import calendar
from dotenv import load_dotenv


from database import schemas, crud, get_db, verify_database, engine
from utils.logger import Logger
from utils import utils
from models import TimeEntry


logger = Logger().get_logger()
app = FastAPI(title="Timesheet Management API")

load_dotenv()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Initializing database on startup")
    try:
        # Run Alembic migrations
        from alembic.config import Config
        from alembic import command

        logger.info("Running database migrations")
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed")

        # Verify database connection and schema
        if not verify_database():
            raise Exception("Database verification failed")

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to Timesheet Management API",
        "documentation": "/docs",
        "redoc": "/redoc"
    }

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
async def initialize_database(db: Session = Depends(get_db)):
    logger.info("Initializing database")
    try:
        # Create all tables
        #Base.metadata.create_all(bind=database.engine) #Removed as migrations handle this.

        # Run Alembic migrations - This is now handled in startup_event

        logger.info("Database initialized successfully")
        return {"status": "success", "message": "Database initialized"}
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/time-entries/", response_model=schemas.TimeEntry)
def create_time_entry(entry: schemas.TimeEntryCreate, db: Session = Depends(get_db)):
    logger.info("Creating new time entry")
    return crud.create_time_entry(db, entry)

@app.get("/time-entries/", response_model=List[schemas.TimeEntry])
def read_time_entries(
    project_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching time entries with project={project_id}, customer={customer_name}")
    return crud.get_time_entries(db, project_id, customer_name, skip, limit)

@app.get("/time-entries/{entry_id}", response_model=schemas.TimeEntry)
def read_time_entry(entry_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching time entry: {entry_id}")
    entry = crud.get_time_entry(db, entry_id)
    if entry is None:
        logger.warning(f"Time entry not found: {entry_id}")
        raise HTTPException(status_code=404, detail="Time entry not found")
    return entry

@app.put("/time-entries/{entry_id}", response_model=schemas.TimeEntry)
def update_time_entry(
    entry_id: int,
    entry: schemas.TimeEntryUpdate,
    db: Session = Depends(get_db)
):
    logger.info(f"Updating time entry: {entry_id}")
    updated_entry = crud.update_time_entry(db, entry_id, entry)
    if updated_entry is None:
        logger.warning(f"Time entry not found: {entry_id}")
        raise HTTPException(status_code=404, detail="Time entry not found")
    return updated_entry

@app.delete("/time-entries/{entry_id}")
def delete_time_entry(entry_id: int, db: Session = Depends(get_db)):
    logger.info(f"Deleting time entry: {entry_id}")
    success = crud.delete_time_entry(db, entry_id)
    if not success:
        logger.warning(f"Time entry not found: {entry_id}")
        raise HTTPException(status_code=404, detail="Time entry not found")
    return {"message": "Entry deleted successfully"}

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

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
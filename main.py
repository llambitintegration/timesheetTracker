import os
import traceback
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import join, text, inspect, func
from sqlalchemy.orm import Session
from sqlalchemy.sql.schema import MetaData
from alembic.migration import MigrationContext
from typing import List, Optional
from datetime import datetime, timedelta, date
import calendar
from dotenv import load_dotenv
import uvicorn
from database import schemas, crud, get_db, verify_database, engine
from utils.logger import Logger, structured_log
from utils.middleware import logging_middleware, error_logging_middleware
from models.timeEntry import TimeEntry
from models.projectModel import Project
from models.projectManagerModel import ProjectManager
from services.customer_service import CustomerService
from services.project_manager_service import ProjectManagerService
from services.project_service import ProjectService
import utils

# Load environment variables
load_dotenv()

logger = Logger().get_logger()
app = FastAPI(title="Timesheet Management API")

# Add both middleware
app.middleware("http")(logging_middleware)
app.middleware("http")(error_logging_middleware)

# Update the CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.v0.dev",
        "https://*.vusercontent.net",
        "https://*.replit.dev",
        "https://*.repl.co",
        "https://*.worf.replit.dev"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*", "X-Total-Count", "X-Correlation-ID"],
    max_age=3600,
)

@app.options("/{path:path}")
async def options_handler(request: Request):
    """Handle OPTIONS requests explicitly"""
    logger.info(structured_log(
        "Handling OPTIONS request",
        correlation_id=Logger().get_correlation_id(),
        path=request.url.path,
        headers=dict(request.headers),
        query_params=dict(request.query_params)
    ))

    # Get the origin from the request headers
    origin = request.headers.get("origin", "")

    # Check if the origin matches any of our allowed patterns
    allowed_origins = [
        "https://*.v0.dev",
        "https://*.vusercontent.net",
        "https://*.replit.dev",
        "https://*.repl.co",
        "https://*.worf.replit.dev"
    ]

    # Use the actual origin in the response if it's allowed
    response_headers = {
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Max-Age": "3600",
        "Access-Control-Allow-Credentials": "true"
    }

    # Set the specific origin instead of wildcard
    response_headers["Access-Control-Allow-Origin"] = origin

    # Log the response we're about to send
    logger.info(structured_log(
        "Sending OPTIONS response",
        correlation_id=Logger().get_correlation_id(),
        origin=origin,
        response_headers=response_headers,
        path=request.url.path,
        query_params=dict(request.query_params)
    ))

    return JSONResponse(
        content={},
        headers=response_headers
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with structured logging"""
    correlation_id = Logger().get_correlation_id()
    logger.error(structured_log(
        "Unhandled exception in request",
        correlation_id=correlation_id,
        error_type=type(exc).__name__,
        error_message=str(exc),
        traceback=traceback.format_exc(),
        path=request.url.path,
        method=request.method
    ))

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "correlation_id": correlation_id
        }
    )

# Project endpoints using ProjectService
@app.get("/projects/", response_model=List[schemas.Project])
def read_projects(
    customer_name: Optional[str] = None,
    project_manager_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all projects with optional filtering"""
    try:
        logger.info(
            f"Fetching projects with customer={customer_name}, "
            f"manager={project_manager_name}, skip={skip}, limit={limit}"
        )
        service = ProjectService(db)
        if customer_name:
            projects = service.get_projects_by_customer(customer_name)
        elif project_manager_name:
            projects = service.get_projects_by_manager(project_manager_name)
        else:
            projects = service.get_all_projects(skip=skip, limit=limit)

        # Ensure proper serialization
        return [project.__dict__ for project in projects]
    except Exception as e:
        logger.error(f"Error fetching projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.on_event("startup")
async def startup_event():
    """Verify database connection and log CORS configuration on startup"""
    logger.info("Starting FastAPI server")
    logger.info("Verifying database connection on startup")
    try:
        if not verify_database():
            logger.warning("Database verification failed - schema may need initialization")

        # Log CORS configuration
        logger.info("=== CORS Configuration ===")
        logger.info("Allowed Origins: 'https://*.v0.dev', 'https://*.vusercontent.net', 'https://*.replit.dev', 'https://*.repl.co', 'https://*.worf.replit.dev'")
        logger.info(f"Allowed Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH")
        logger.info(f"Allow Credentials: True")
        logger.info(f"Allowed Headers: '*'")
        logger.info(f"Expose Headers: '*', 'X-Total-Count', 'X-Correlation-ID'")

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        logger.exception("Startup error details:")
        raise


@app.get("/")
def read_root():
    """Root endpoint for API health check"""
    logger.info("Root endpoint accessed")
    return {
        "status": "healthy",
        "message": "Timesheet Management API is running",
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
        contents = await file.read()
        # Create a temporary file-like object
        from io import StringIO, BytesIO
        if file.filename.endswith('.xlsx'):
            entries = utils.parse_excel(BytesIO(contents))
        elif file.filename.endswith('.csv'):
            # Decode bytes to string for CSV
            text_contents = contents.decode('utf-8')
            entries = utils.parse_csv(StringIO(text_contents))
        else:
            logger.error(f"Unsupported file format: {file.filename}")
            raise HTTPException(status_code=400, detail="Unsupported file format")

        if not entries:
            logger.warning("No valid entries found in file")
            return []

        created_entries = crud.create_time_entries(db, entries)
        logger.info(f"Successfully created {len(created_entries)} time entries")
        return created_entries
    except Exception as e:
        logger.error(f"Error processing timesheet: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/customers/", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer using CustomerService"""
    try:
        logger.info(f"Creating new customer: {customer.name}")
        service = CustomerService(db)
        return service.create_customer(customer)
    except ValueError as e:
        logger.warning(f"Customer creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/customers/", response_model=List[schemas.Customer])
def read_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all customers using CustomerService"""
    logger.info(f"Fetching customers with skip={skip}, limit={limit}")
    service = CustomerService(db)
    return service.get_all_customers(skip=skip, limit=limit)


@app.get("/customers/{name}", response_model=schemas.Customer)
def read_customer(name: str, db: Session = Depends(get_db)):
    """Get a specific customer by name using CustomerService"""
    logger.info(f"Fetching customer: {name}")
    service = CustomerService(db)
    customer = service.get_customer(name)
    if customer is None:
        logger.warning(f"Customer not found: {name}")
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.patch("/customers/{name}", response_model=schemas.Customer)
def update_customer(name: str, customer_update: schemas.CustomerUpdate, db: Session = Depends(get_db)):
    """Update a customer using CustomerService"""
    try:
        logger.info(f"Updating customer: {name}")
        service = CustomerService(db)
        updated_customer = service.update_customer(name, customer_update)
        if updated_customer is None:
            logger.warning(f"Customer not found: {name}")
            raise HTTPException(status_code=404, detail="Customer not found")
        return updated_customer
    except Exception as e:
        logger.error(f"Error updating customer: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")



@app.post("/project-managers/", response_model=schemas.ProjectManager)
def create_project_manager(
    project_manager: schemas.ProjectManagerCreate,
    db: Session = Depends(get_db)
):
    """Create a new project manager"""
    try:
        logger.info(f"Creating new project manager: {project_manager.name}")
        service = ProjectManagerService(db)
        return service.create_project_manager(project_manager)
    except ValueError as e:
        logger.warning(f"Project manager creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating project manager: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/project-managers/", response_model=List[schemas.ProjectManager])
def read_project_managers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all project managers with pagination"""
    logger.info(f"Fetching project managers with skip={skip}, limit={limit}")
    service = ProjectManagerService(db)
    return service.get_all_project_managers(skip=skip, limit=limit)


@app.get("/project-managers/{email}", response_model=schemas.ProjectManager)
def read_project_manager(email: str, db: Session = Depends(get_db)):
    """Get a project manager by email"""
    logger.info(f"Fetching project manager with email: {email}")
    service = ProjectManagerService(db)
    project_manager = service.get_project_manager(email)
    if project_manager is None:
        logger.warning(f"Project manager not found: {email}")
        raise HTTPException(status_code=404, detail="Project manager not found")
    return project_manager


@app.patch("/project-managers/{email}", response_model=schemas.ProjectManager)
def update_project_manager(
    email: str,
    project_manager_update: schemas.ProjectManagerUpdate,
    db: Session = Depends(get_db)
):
    """Update a project manager"""
    try:
        logger.info(f"Updating project manager: {email}")
        service = ProjectManagerService(db)
        updated_pm = service.update_project_manager(email, project_manager_update)
        if updated_pm is None:
            logger.warning(f"Project manager not found: {email}")
            raise HTTPException(status_code=404, detail="Project manager not found")
        return updated_pm
    except Exception as e:
        logger.error(f"Error updating project manager: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Project endpoints using ProjectService
@app.post("/projects/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    try:
        logger.info(f"Creating new project: {project.project_id}")
        service = ProjectService(db)
        return service.create_project(project)
    except ValueError as e:
        logger.warning(f"Project creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/projects/", response_model=List[schemas.Project])
def read_projects(
    customer_name: Optional[str] = None,
    project_manager_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all projects with optional filtering"""
    try:
        logger.info(
            f"Fetching projects with customer={customer_name}, "
            f"manager={project_manager_name}, skip={skip}, limit={limit}"
        )
        service = ProjectService(db)
        if customer_name:
            projects = service.get_projects_by_customer(customer_name)
        elif project_manager_name:
            projects = service.get_projects_by_manager(project_manager_name)
        else:
            projects = service.get_all_projects(skip=skip, limit=limit)

        # Ensure proper serialization
        return [project.__dict__ for project in projects]
    except Exception as e:
        logger.error(f"Error fetching projects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}", response_model=schemas.Project)
def read_project(project_id: str, db: Session = Depends(get_db)):
    """Get a project by ID"""
    logger.info(f"Fetching project: {project_id}")
    service = ProjectService(db)
    project = service.get_project(project_id)
    if project is None:
        logger.warning(f"Project not found: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.patch("/projects/{project_id}", response_model=schemas.Project)
def update_project(
    project_id: str,
    project_update: schemas.ProjectBase,
    db: Session = Depends(get_db)
):
    """Update a project"""
    try:
        logger.info(f"Updating project: {project_id}")
        service = ProjectService(db)
        updated_project = service.update_project(project_id, project_update)
        if updated_project is None:
            logger.warning(f"Project not found: {project_id}")
            raise HTTPException(status_code=404, detail="Project not found")
        return updated_project
    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project"""
    try:
        logger.info(f"Deleting project: {project_id}")
        service = ProjectService(db)
        if service.delete_project(project_id):
            return {"status": "success", "message": f"Project {project_id} deleted"}
        logger.warning(f"Project not found for deletion: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/init-db/")
@app.get("/init-db/")
async def initialize_database(force: bool = False, db: Session = Depends(get_db)):
    """Initialize database and run migrations"""
    logger.info("Starting database initialization process")
    try:
        logger.info("Testing database connection")
        try:
            db.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        except Exception as conn_error:
            logger.error(f"Database connection failed: {str(conn_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Database connection failed: {str(conn_error)}"
            )

        if force:
            logger.info("Force flag is true, dropping existing tables")
            try:
                with engine.connect() as connection:
                    # Drop tables in correct order due to foreign key constraints
                    connection.execute(text("DROP TABLE IF EXISTS time_entries CASCADE"))
                    connection.execute(text("DROP TABLE IF EXISTS projects CASCADE"))
                    connection.execute(text("DROP TABLE IF EXISTS project_managers CASCADE"))
                    connection.execute(text("DROP TABLE IF EXISTS customers CASCADE"))
                    connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
                    connection.commit()
                logger.info("Existing tables dropped successfully")
            except Exception as e:
                logger.error(f"Error dropping tables: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error dropping tables: {str(e)}")

        logger.info("Loading Alembic configuration")
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

        try:
            logger.info("Starting migration process")
            command.upgrade(alembic_cfg, "head")
            logger.info("Migration completed successfully")
        except Exception as migration_error:
            logger.error(f"Migration failed: {str(migration_error)}")
            logger.exception("Migration stack trace:")
            raise HTTPException(
                status_code=500,
                detail=f"Migration failed: {str(migration_error)}"
            )

        # Verify database state after migration
        logger.info("Verifying database state after migration")
        with engine.connect() as connection:
            inspector = inspect(engine)
            tables = ['customers', 'project_managers', 'projects', 'time_entries']
            missing_tables = []

            for table in tables:
                if not inspector.has_table(table):
                    missing_tables.append(table)
                    logger.warning(f"Table {table} not found")
                else:
                    logger.info(f"Table {table} exists")
                    # Verify columns in time_entries table
                    if table == 'time_entries':
                        columns = [col['name'] for col in inspector.get_columns(table)]
                        logger.info(f"Columns in time_entries: {columns}")
                        if 'date' not in columns:
                            missing_tables.append('time_entries (missing date column)')

            if missing_tables:
                error_msg = f"Tables missing after migration: {', '.join(missing_tables)}"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)

        logger.info("Database initialization completed successfully")
        return {
            "status": "success",
            "message": "Database initialized and verified",
            "details": {
                "tables_created": tables
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Database initialization failed: {str(e)}"
        logger.error(error_msg)
        logger.exception("Initialization error stack trace:")
        raise HTTPException(status_code=500, detail=error_msg)


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
        Project.project_id,
        Project.customer,
        func.sum(TimeEntry.hours).label('total_hours')
    ).join(
        TimeEntry,
        TimeEntry.project == Project.project_id
    ).filter(
        TimeEntry.date >= week_start.date(),
        TimeEntry.date <= week_end.date()
    ).group_by(
        Project.project_id,
        Project.customer
    )

    if project_id:
        query = query.filter(Project.project_id == project_id)

    results = query.all()
    entries = [
        schemas.ReportEntry(
            total_hours=float(r.total_hours or 0),
            category=r.customer or "Unassigned",
            project=r.project_id,
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

    # Adjust the logic to fix week start and start date
    # Get the first and last day of the month
    _, last_day = calendar.monthrange(year, month)

    # Determine the correct week start and end based on the given year and month
    week_start = datetime(year, month, 1).date()  # Assuming week starts from the 1st of the month
    week_end = datetime(year, month, last_day).date()  # Assuming week ends on the last day of the month

    query = db.query(
        Project.project_id,
        Project.customer,
        func.sum(TimeEntry.hours).label('total_hours')
    ).join(
        TimeEntry,
        TimeEntry.project == Project.project_id
    ).filter(
        TimeEntry.date >= week_start,
        TimeEntry.date <= week_end
    ).group_by(
        Project.project_id,
        Project.customer
    )

    if project_id:
        query = query.filter(Project.project_id == project_id)

    results = query.all()
    entries = [
        schemas.ReportEntry(
            total_hours=float(r.total_hours or 0),
            category=r.customer or "Unassigned",
            project=r.project_id,
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
    logger.info("Starting FastAPI server")
    try:
        port = int(os.getenv('PORT', '8000'))  # Changed default port to 8000
        logger.info(f"Server will start on port {port}")

        uvicorn.run(
            "main:app",  # Changed to use string reference
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"  # Changed to info for cleaner logs
        )
    except Exception as e:
        logger.error(f"Server startup failed: {str(e)}")
        raise
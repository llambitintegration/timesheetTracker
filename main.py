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
from services.timesheet_service import TimesheetService
from services.report_service import ReportService
import utils
import re
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

logger = Logger().get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    logger.info("Starting FastAPI server")
    logger.info("Verifying database connection on startup")
    try:
        if not verify_database():
            logger.warning("Database verification failed - schema may need initialization")

        # Log CORS configuration
        logger.info("=== CORS Configuration ===")
        logger.info(f"Allowed Origins: '*'")
        logger.info(f"Allowed Methods: 'GET, POST, PUT, DELETE, OPTIONS, PATCH'")
        logger.info(f"Allow Credentials: False")
        logger.info(f"Allowed Headers: '*'")
        logger.info(f"Expose Headers: 'X-Total-Count, X-Correlation-ID'")

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        logger.exception("Startup error details:")
        raise

    yield

    logger.info("Shutting down FastAPI server")

# Create FastAPI app
app = FastAPI(
    title="Timesheet Management API",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Correlation-ID"]
)

# Add other middleware after CORS
app.middleware("http")(logging_middleware)
app.middleware("http")(error_logging_middleware)

@app.middleware("http")
async def cors_headers_middleware(request: Request, call_next):
    """Ensure consistent CORS headers across all responses"""
    correlation_id = Logger().get_correlation_id()

    # Handle preflight requests specially
    if request.method == "OPTIONS":
        logger.info(structured_log(
            "Processing CORS preflight request",
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            origin=request.headers.get("origin"),
            request_method=request.headers.get("access-control-request-method"),
            request_headers=request.headers.get("access-control-request-headers")
        ))

        return JSONResponse(
            content={},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS,PATCH",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "3600",
                "Access-Control-Allow-Credentials": "false",
                "Access-Control-Expose-Headers": "X-Total-Count,X-Correlation-ID"
            }
        )

    # Handle regular requests
    response = await call_next(request)

    logger.debug(structured_log(
        "Adding CORS headers to response",
        correlation_id=correlation_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code
    ))

    # Ensure CORS headers are present and consistent
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS,PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "false"
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count,X-Correlation-ID"

    return response


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to the Timesheet Management API"}

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    logger.info(structured_log(
        "Health check accessed",
        correlation_id=Logger().get_correlation_id(),
        method=request.method,
        path="/health"
    ))

    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

@app.get("/time-entries", response_model=List[schemas.TimeEntry])
def get_time_entries(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get paginated time entries"""
    service = TimesheetService(db)
    return service.get_entries(skip=skip, limit=limit)

@app.post("/time-entries", response_model=schemas.TimeEntry)
def create_time_entry(entry: schemas.TimeEntryCreate, db: Session = Depends(get_db)):
    """Create a new time entry"""
    service = TimesheetService(db)
    return service.create_entry(entry)

@app.put("/time-entries/{entry_id}", response_model=schemas.TimeEntry)
def update_time_entry(entry_id: int, entry: schemas.TimeEntryUpdate, db: Session = Depends(get_db)):
    """Update an existing time entry"""
    service = TimesheetService(db)
    return service.update_entry(entry_id, entry)

@app.delete("/time-entries/{entry_id}")
def delete_time_entry(entry_id: int, db: Session = Depends(get_db)):
    """Delete a time entry"""
    service = TimesheetService(db)
    return service.delete_entry(entry_id)

@app.get("/projects", response_model=List[schemas.Project])
def get_projects(db: Session = Depends(get_db)):
    """Get all projects"""
    service = ProjectService(db)
    return service.get_all_projects()

@app.post("/projects", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    service = ProjectService(db)
    return service.create_project(project)

@app.put("/projects/{project_id}", response_model=schemas.Project)
def update_project(project_id: str, project: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    """Update an existing project"""
    service = ProjectService(db)
    return service.update_project(project_id, project)

@app.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project"""
    service = ProjectService(db)
    return service.delete_project(project_id)

@app.get("/project-managers", response_model=List[schemas.ProjectManager])
def get_project_managers(db: Session = Depends(get_db)):
    """Get all project managers"""
    service = ProjectManagerService(db)
    return service.get_all_project_managers()

@app.post("/project-managers", response_model=schemas.ProjectManager)
def create_project_manager(manager: schemas.ProjectManagerCreate, db: Session = Depends(get_db)):
    """Create a new project manager"""
    service = ProjectManagerService(db)
    return service.create_project_manager(manager)

@app.put("/project-managers/{email}", response_model=schemas.ProjectManager)
def update_project_manager(email: str, manager: schemas.ProjectManagerUpdate, db: Session = Depends(get_db)):
    """Update an existing project manager"""
    service = ProjectManagerService(db)
    return service.update_project_manager(email, manager)

@app.delete("/project-managers/{email}")
def delete_project_manager(email: str, db: Session = Depends(get_db)):
    """Delete a project manager"""
    service = ProjectManagerService(db)
    return service.delete_project_manager(email)

@app.get("/customers", response_model=List[schemas.Customer])
def get_customers(db: Session = Depends(get_db)):
    """Get all customers"""
    service = CustomerService(db)
    return service.get_all_customers()

@app.post("/customers", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer"""
    service = CustomerService(db)
    return service.create_customer(customer)

@app.put("/customers/{name}", response_model=schemas.Customer)
def update_customer(name: str, customer: schemas.CustomerUpdate, db: Session = Depends(get_db)):
    """Update an existing customer"""
    service = CustomerService(db)
    return service.update_customer(name, customer)

@app.delete("/customers/{name}")
def delete_customer(name: str, db: Session = Depends(get_db)):
    """Delete a customer"""
    service = CustomerService(db)
    return service.delete_customer(name)

@app.post("/time-entries/upload/", response_model=List[schemas.TimeEntry])
async def upload_timesheet(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process timesheet file"""
    service = TimesheetService(db)
    return await service.upload_timesheet(file)

@app.post("/init-db/")
async def initialize_database(force: bool = False, db: Session = Depends(get_db)):
    """Initialize database and run migrations"""
    from services.database_service import DatabaseService
    service = DatabaseService(db)
    return await service.initialize_database(force)

@app.get("/reports/weekly", response_model=schemas.WeeklyReport)
def get_weekly_report(
    date: datetime = Query(default=None),
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get weekly time report"""
    service = ReportService(db)
    return service.get_weekly_report(date, project_id)

@app.get("/reports/monthly", response_model=schemas.MonthlyReport)
def get_monthly_report(
    year: int = Query(...),
    month: int = Query(...),
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get monthly time report"""
    service = ReportService(db)
    return service.get_monthly_report(year, month, project_id)


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

@app.post("/dev/sample-data", include_in_schema=False)
def create_sample_data(db: Session = Depends(get_db)):
    """Create sample time entries for testing"""
    sample_entries = [
        schemas.TimeEntryCreate(
            category="Development",
            subcategory="Frontend",
            customer="ECOLAB",
            project="Project_Magic_Bullet",
            task_description="Worked on React components",
            hours=8.0,
            date=date(2025, 2, 1)
        ),
        schemas.TimeEntryCreate(
            category="Development",
            subcategory="Backend",
            customer="ECOLAB",
            project="Project_Magic_Bullet",
            task_description="Implemented API endpoints",
            hours=6.0,
            date=date(2025, 2, 2)
        ),
        schemas.TimeEntryCreate(
            category="Testing",
            subcategory="QA",
            customer="ECOLAB",
            project="Project_Magic_Bullet",
            task_description="End-to-end testing",
            hours=4.0,
            date=date(2025, 2, 3)
        )
    ]

    created_entries = []
    for entry in sample_entries:
        try:
            created_entry = crud.create_time_entry(db, entry)
            created_entries.append(created_entry)
        except Exception as e:
            logger.error(f"Error creating sample entry: {str(e)}")
            continue

    return {"message": f"Created {len(created_entries)} sample entries"}

if __name__ == "__main__":
    logger.info("Starting FastAPI server")
    try:
        port = int(os.getenv('PORT', '8000'))
        logger.info(f"Server will start on port {port}")

        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Server startup failed: {str(e)}")
        raise
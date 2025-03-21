from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Query, Request, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import os
import traceback
from database import crud, schemas, get_db
from services.timesheet_service import TimesheetService
from services.customer_service import CustomerService
from services.project_service import ProjectService
from services.project_manager_service import ProjectManagerService
from services.database_service import DatabaseService
from services.time_entry_service import TimeEntryService
from services.report_service import ReportService
from utils.logger import Logger
from utils.middleware import logging_middleware, error_logging_middleware
from utils.structured_log import structured_log

# Initialize logger
logger = Logger().get_logger()

app = FastAPI(
    title="Timesheet Management API",
    description="A FastAPI-based timesheet management system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Basic CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic root endpoint for testing
@app.get("/")
async def root():
    """Root endpoint for testing API accessibility"""
    return {"status": "ok", "message": "API is running"}

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

@app.get("/debug/database", include_in_schema=False)
async def debug_database(request: Request, db: Session = Depends(get_db)):
    """Debug endpoint to verify database connection"""
    logger.info(structured_log(
        "Database debug endpoint accessed",
        correlation_id=Logger().get_correlation_id(),
        method=request.method,
        path="/debug/database"
    ))

    service = DatabaseService(db)
    connection_info = await service._test_connection()

    return JSONResponse(content={
        "status": "connected",
        "database": connection_info[0],
        "user": connection_info[1],
        "server": f"{connection_info[2]}:{connection_info[3]}",
        "version": connection_info[4]
    })

@app.get("/time-entries", response_model=List[schemas.TimeEntry])
def get_time_entries(
    date: date = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get paginated time entries for a specific date"""
    service = TimeEntryService(db)
    return service.get_time_entries(date=date, skip=skip, limit=limit)

@app.post("/time-entries", response_model=schemas.TimeEntry, status_code=201)
def create_time_entry(entry: schemas.TimeEntryCreate, db: Session = Depends(get_db)):
    """Create a new time entry"""
    service = TimesheetService(db)
    return service.create_entry(entry)

@app.get("/time-entries/{entry_id}", response_model=schemas.TimeEntry)
def get_time_entry(entry_id: int, db: Session = Depends(get_db)):
    """Get a specific time entry by ID"""
    entry = crud.get_time_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    return entry

@app.put("/time-entries/{entry_id}", response_model=schemas.TimeEntry)
def update_time_entry(
    entry_id: int,
    entry: schemas.TimeEntryUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing time entry"""
    try:
        service = TimeEntryService(db)
        updated_entry = service.update_entry(entry_id, entry)
        if not updated_entry:
            raise HTTPException(status_code=404, detail="Time entry not found")
        return updated_entry
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating time entry {entry_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/time-entries/{entry_id}", status_code=204)
def delete_time_entry(entry_id: int, db: Session = Depends(get_db)):
    """Delete a time entry"""
    try:
        service = TimeEntryService(db)
        if not service.delete_entry(entry_id):
            raise HTTPException(status_code=404, detail="Time entry not found")
        return None
    except Exception as e:
        logger.error(f"Error deleting time entry {entry_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/projects", response_model=List[schemas.Project])
def get_projects(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all projects with pagination"""
    service = ProjectService(db)
    return service.get_all_projects(skip=skip, limit=limit)

@app.post("/projects", response_model=schemas.Project, status_code=201)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    service = ProjectService(db)
    return service.create_project(project)

@app.get("/projects/{project_id}", response_model=schemas.Project)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get a specific project by ID"""
    service = ProjectService(db)
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@app.put("/projects/{project_id}", response_model=schemas.Project)
def update_project(project_id: str, project: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    """Update an existing project"""
    service = ProjectService(db)
    updated_project = service.update_project(project_id, project)
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated_project

@app.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project"""
    service = ProjectService(db)
    if not service.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return None

@app.get("/project-managers", response_model=List[schemas.ProjectManager])
def get_project_managers(db: Session = Depends(get_db)):
    """Get all project managers"""
    service = ProjectManagerService(db)
    return service.get_all_project_managers()

@app.post("/project-managers", response_model=schemas.ProjectManager, status_code=201)
def create_project_manager(manager: schemas.ProjectManagerCreate, db: Session = Depends(get_db)):
    """Create a new project manager"""
    service = ProjectManagerService(db)
    return service.create_project_manager(manager)

@app.get("/project-managers/{email}", response_model=schemas.ProjectManager)
def get_project_manager(email: str, db: Session = Depends(get_db)):
    """Get a specific project manager by email"""
    service = ProjectManagerService(db)
    manager = service.get_project_manager(email)
    if not manager:
        raise HTTPException(status_code=404, detail="Project manager not found")
    return manager

@app.put("/project-managers/{email}", response_model=schemas.ProjectManager)
def update_project_manager(
    email: str,
    manager: schemas.ProjectManagerUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing project manager"""
    try:
        service = ProjectManagerService(db)
        updated_manager = service.update_project_manager(email, manager)
        if not updated_manager:
            raise HTTPException(status_code=404, detail="Project manager not found")
        return updated_manager
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/project-managers/{email}", status_code=204)
def delete_project_manager(email: str, db: Session = Depends(get_db)):
    """Delete a project manager"""
    try:
        service = ProjectManagerService(db)
        if not email:
            raise HTTPException(status_code=400, detail="Project manager email is required")
        if not service.delete_project_manager(email):
            raise HTTPException(status_code=404, detail="Project manager not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
def update_customer(
    name: str,
    customer: schemas.CustomerUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing customer"""
    service = CustomerService(db)
    return service.update_customer(name, customer)

@app.delete("/customers/{name}")
def delete_customer(name: str, db: Session = Depends(get_db)):
    """Delete a customer"""
    service = CustomerService(db)
    if not name:
        raise HTTPException(status_code=400, detail="Customer name is required")
    return service.delete_customer(name)

@app.get("/customers/{name}", response_model=schemas.Customer)
def get_customer(name: str, db: Session = Depends(get_db)):
    """Get a specific customer by name"""
    service = CustomerService(db)
    customer = service.get_customer(name)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.post("/time-entries/upload/")
async def upload_timesheet(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Upload and process timesheet file with progress tracking"""
    logger.info(f"Processing timesheet upload: {file.filename}")

    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Check file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    file_size = 0
    contents = await file.read()
    file_size = len(contents)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Check file extension
    if not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(
            status_code=400,
            detail="Only Excel (.xlsx) files are supported"
        )

    # Accept both standard Excel content types
    allowed_content_types = {
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel',
        'multipart/form-data'
    }

    content_type = file.content_type.split(';')[0].strip()
    if content_type not in allowed_content_types:
        logger.warning(f"Received content type: {content_type}")
        logger.warning(f"Allowed content types: {allowed_content_types}")

    try:
        service = TimeEntryService(db)
        result = await service.process_excel_upload(contents, background_tasks)

        return JSONResponse(
            status_code=202,  # Accepted
            content={
                "message": "Upload processing started",
                "progress_key": result["progress_key"],
                "total_records": result["total_records"]
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing timesheet: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/time-entries/upload/{progress_key}/status")
async def get_upload_status(progress_key: str):
    """Get the status of an ongoing upload"""
    # In a real implementation, this would fetch progress from Redis or similar
    # For now, we'll return a mock response
    return JSONResponse(
        content={
            "status": "processing",
            "progress": 50  # This would be the actual progress in a real implementation
        }
    )

@app.post("/init-db/")
async def initialize_database(force: bool = False, db: Session = Depends(get_db)):
    """Initialize database and run migrations"""
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

import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
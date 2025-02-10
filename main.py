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

# Add lifespan context manager before app initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup logic
    logger.info("Starting FastAPI server")
    logger.info("Verifying database connection on startup")
    try:
        if not verify_database():
            logger.warning("Database verification failed - schema may need initialization")

        # Log CORS configuration
        logger.info("=== CORS Configuration ===")
        logger.info(f"Allowed Origins: ['https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net']")
        logger.info(f"Allowed Methods: 'GET,POST,PUT,DELETE,OPTIONS,PATCH'")
        logger.info(f"Allow Credentials: False")
        logger.info(f"Allowed Headers: '*'")
        logger.info(f"Expose Headers: 'X-Total-Count', 'X-Correlation-ID'")

    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        logger.exception("Startup error details:")
        raise

    yield  # Server runs here

    # Shutdown logic (if any)
    logger.info("Shutting down FastAPI server")

# Update app initialization to use lifespan
app = FastAPI(
    title="Timesheet Management API",
    lifespan=lifespan
)

# Add both middleware
app.middleware("http")(logging_middleware)
app.middleware("http")(error_logging_middleware)

# Update CORS configuration with proper settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://kzmk61p9ygadt1kvrsrm.lite.vusercontent.net"],  # Specific origin instead of wildcard
    allow_credentials=False,  # Must be False since frontend doesn't need credentials
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],  # Allow all headers
    expose_headers=["X-Total-Count", "X-Correlation-ID"],
    max_age=3600
)

@app.get("/")
@app.post("/")
@app.put("/")
@app.delete("/")
@app.patch("/")
@app.options("/")
async def read_root(request: Request):
    """Root endpoint for API health check"""
    logger.info("Root endpoint accessed")
    return {
        "status": "healthy",
        "message": "Timesheet Management API is running",
        "documentation": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    logger.info(structured_log(
        "Health check accessed",
        correlation_id=Logger().get_correlation_id(),
        method=request.method,
        path="/health"
    ))

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.options("/{path:path}")
async def options_handler(request: Request):
    """Handle OPTIONS requests explicitly"""
    methods = "GET,POST,PUT,DELETE,OPTIONS,PATCH"
    response = JSONResponse(content={})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = methods
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600"
    response.headers["Access-Control-Allow-Credentials"] = "false"
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count,X-Correlation-ID"
    return response

# Move catch-all route to the end of file and update its behavior
@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(request: Request, path_name: str):
    """Catch-all route to handle nonexistent paths with 404"""
    return JSONResponse(
        status_code=404,
        content={"detail": f"Path '/{path_name}' not found"}
    )

@app.post("/timesheet/upload/", response_model=List[schemas.TimeEntry])
async def upload_timesheet(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process timesheet file"""
    service = TimesheetService(db)
    return await service.upload_timesheet(file)

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

@app.get("/customers/")
async def customers_endpoint(route: str = "", skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    General endpoint for managing customer interactions.
    Sub-routes specify the operation: list all customers or operate on a specific one.
    """
    # Handle sub-routes
    sub_route_handlers = {
        '': CustomerService(db).get_all_customers,  # List all customers
        ':name': CustomerService(db).get_customer,  # Get specific customer
        '/:name': CustomerService(db).update_customer  # Update specific customer
    }

    if route in sub_route_handlers:
        try:
            logger.info(f"Customer endpoint accessed with route: {route}")
            if route == '':
                return sub_route_handlers[route](skip=skip, limit=limit)
            else:
                name = route.split('/')[-1]
                if ':name' in route:
                    customer = sub_route_handlers[':name'](name)
                    if customer is None:
                        logger.warning(f"Customer not found: {name}")
                        raise HTTPException(status_code=404, detail="Customer not found")
                    return customer
                else:
                    # Mocked customer update for purposes of showcasing sub-endpoint
                    customer_update = schemas.CustomerUpdate(...)  # Placeholder for actual update data
                    updated_customer = sub_route_handlers['/:name'](name, customer_update)
                    if updated_customer is None:
                        logger.warning(f"Customer not found: {name}")
                        raise HTTPException(status_code=404, detail="Customer not found")
                    return updated_customer
        except Exception as e:
            logger.error(f"Error in customer operation: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    logger.error(f"Invalid sub-route for customers: {route}")
    raise HTTPException(status_code=404, detail="Sub-route not found")

@app.route('/project-managers', methods=['GET', 'POST'])
async def manage_project_managers(
    request: Request,  # Add request parameter
    email: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    project_manager: Optional[schemas.ProjectManagerCreate] = None,
    project_manager_update: Optional[schemas.ProjectManagerUpdate] = None,
    db: Session = Depends(get_db)
):
    """
    Endpoint to manage project managers.
    - `GET`: Fetch all project managers or a specific manager by email.
    - `POST`: Create a new project manager.
    - `PATCH`: Update an existing project manager.
    """
    try:
        if request.method == 'GET':
            if email:
                logger.info(f"Fetching project manager with email: {email}")
                service = ProjectManagerService(db)
                project_manager = service.get_project_manager(email)
                if project_manager is None:
                    logger.warning(f"Project manager not found: {email}")
                    raise HTTPException(status_code=404, detail="Project manager not found")
                return project_manager
            else:
                logger.info(f"Fetching project managers with skip={skip}, limit={limit}")
                service = ProjectManagerService(db)
                return service.get_all_project_managers(skip=skip, limit=limit)
        elif request.method == 'POST' and project_manager is not None:
            logger.info(f"Creating new project manager: {project_manager.name}")
            service = ProjectManagerService(db)
            return service.create_project_manager(project_manager)
        elif request.method == 'PATCH' and email and project_manager_update:
            logger.info(f"Updating project manager: {email}")
            service = ProjectManagerService(db)
            updated_pm = service.update_project_manager(email, project_manager_update)
            if updated_pm is None:
                logger.warning(f"Project manager not found: {email}")
                raise HTTPException(status_code=404, detail="Project manager not found")
            return updated_pm
        else:
            logger.error(f"Invalid request method: {request.method}")
            raise HTTPException(status_code=405, detail="Method not allowed")
    except ValueError as e:
        logger.warning(f"Project manager operation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error managing project managers: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.route('/projects', methods=['GET', 'POST', 'PATCH', 'DELETE'])
async def manage_projects(
    request: Request,
    project_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    project_manager_name: Optional[str] = None,
    project_data: Optional[schemas.ProjectCreate] = None,
    project_update: Optional[schemas.ProjectBase] = None,
    db: Session = Depends(get_db),
):
    """
    Endpoint to manage projects.
    - `GET`: Retrieve projects with optional filters.
    - `POST`: Create a new project.
    - `PATCH`: Update an existing project.
    - `DELETE`: Remove a project by ID.
    """
    service = ProjectService(db)

    if request.method == 'GET':
        logger.info(
            f"Fetching projects with customer={customer_name}, "
            f"manager={project_manager_name}"
        )
        if customer_name:
            return service.get_projects_by_customer(customer_name)
        elif project_manager_name:
            return service.get_projects_by_manager(project_manager_name)
        return service.get_all_projects()

    if request.method == 'POST' and project_data:
        logger.info(f"Creating new project: {project_data.project_id}")
        try:
            return service.create_project(project_data)
        except ValueError as e:
            logger.warning(f"Project creation failed: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    if request.method == 'PATCH' and project_id and project_update:
        logger.info(f"Updating project: {project_id}")
        updated_project = service.update_project(project_id, project_update)
        if updated_project is None:
            logger.warning(f"Project not found: {project_id}")
            raise HTTPException(status_code=404, detail="Project not found")
        return updated_project

    if request.method == 'DELETE' and project_id:
        logger.info(f"Deleting project: {project_id}")
        if service.delete_project(project_id):
            return {"status": "success", "message": f"Project {project_id} deleted"}
        logger.warning(f"Project not found for deletion: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")

    logger.error(f"Invalid request method or missing parameters: {request.method}")
    raise HTTPException(status_code=400, detail="Invalid request method or missing parameters")

@app.post("/init-db/")
@app.get("/init-db/")
async def initialize_database(force: bool = False, db: Session = Depends(get_db)):
    """Initialize database and run migrations"""
    from services.database_service import DatabaseService
    service = DatabaseService(db)
    return await service.initialize_database(force)

@app.get("/time-entries", response_model=List[schemas.TimeEntry])
@app.get("/time-entries/", response_model=List[schemas.TimeEntry])
def get_time_entries(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get paginated time entries"""
    service = TimesheetService(db)
    return service.get_entries(skip=skip, limit=limit)

@app.get("/time-entries/by-date/{date}", response_model=List[schemas.TimeEntry])
def get_time_entries_by_date(
    date: date,
    db: Session = Depends(get_db)
):
    """Get time entries for a specific date"""
    service = TimesheetService(db)
    return service.get_entries_by_date(date)

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
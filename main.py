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
        logger.info(f"Allowed Origins: ['*']")  # Allow all origins
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

# Update CORS configuration with more permissive settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False since frontend doesn't need credentials
    allow_methods=["*"],  # Allow all methods
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
    logger.info(f"Root endpoint accessed via {request.method}")
    response = JSONResponse(content={
        "status": "healthy",
        "message": "Timesheet Management API is running",
        "documentation": "/docs",
        "redoc": "/redoc"
    }, headers={"Access-Control-Allow-Origin": "*"})  # Allow CORS on response
    return response

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}

@app.options("/{path:path}")
async def options_handler(request: Request):
    """Handle OPTIONS requests explicitly"""
    methods = "GET,POST,PUT,DELETE,OPTIONS,PATCH"
    response = JSONResponse(content={})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600"
    response.headers["Access-Control-Allow-Credentials"] = "false"
    response.headers["Access-Control-Expose-Headers"] = "X-Total-Count,X-Correlation-ID"
    return response

#The cors_middleware is redundant given the CORSMiddleware above.  Removing it.

# Move catch-all route to the end of file and update its behavior
@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(request: Request, path_name: str):
    """Catch-all route to handle nonexistent paths with 404"""
    logger.info(f"Non-existent path accessed: /{path_name}")
    raise HTTPException(status_code=404, detail=f"Path '/{path_name}' not found")

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
        from alembic import
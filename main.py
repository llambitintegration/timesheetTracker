import os
import traceback
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query, Path, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, date
import calendar
from dotenv import load_dotenv
import uvicorn
from contextlib import asynccontextmanager

# Import local modules
from database.database import get_db, engine
from database import schemas, crud
from utils.logger import Logger
from utils.middleware import logging_middleware, error_logging_middleware
from models.timeEntry import TimeEntry
from models.projectModel import Project
from models.projectManagerModel import ProjectManager
from services.customer_service import CustomerService
from services.project_manager_service import ProjectManagerService
from services.project_service import ProjectService
import utils
from alembic import command
from alembic.config import Config

# Load environment variables
load_dotenv()

logger = Logger().get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    try:
        logger.info("Starting FastAPI server")

        # Basic database connection test
        logger.info("Testing database connection")
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                connection.commit()
                logger.info("Database connection successful")
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise

        # Log CORS Configuration
        logger.info("CORS Configuration enabled with credentials=False")
        yield
    finally:
        logger.info("Shutting down FastAPI server")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Timesheet Management API",
    description="API for managing timesheets with CORS support",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS - Must be first middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Correlation-ID"]
)

# Add logging middleware after CORS
app.middleware("http")(logging_middleware)
app.middleware("http")(error_logging_middleware)

@app.get("/")
async def read_root():
    """Root endpoint for API health check"""
    return {
        "status": "healthy",
        "message": "Timesheet Management API is running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            connection.commit()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "database": "disconnected"}


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

#This section remains unchanged
from alembic import command
from alembic.config import Config

# Fix the initialize_database function
@app.post("/init-db/")
@app.get("/init-db/")
async def initialize_database(force: bool = False, db: Session = Depends(get_db)):
    """Initialize database and run migrations"""
    logger.info("Starting database initialization process")
    try:
        # Test database connection
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

        # Handle force flag
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

        # Run Alembic migrations
        logger.info("Loading Alembic configuration")
        try:
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            logger.info("Database migration completed successfully")
            return {"status": "success", "message": "Database initialized successfully"}
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Migration error: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during database initialization")

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8080)
    except Exception as e:
        logger.error(f"Server startup failed: {str(e)}")
        raise
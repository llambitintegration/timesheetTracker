from fastapi import FastAPI, HTTPException, Depends, Query, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from database import schemas, get_db
from services.time_entry_service import TimeEntryService
from utils.logger import Logger
from utils.middleware import logging_middleware, error_logging_middleware
import uvicorn

app = FastAPI()
logger = Logger().get_logger()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Add logging middleware
app.middleware("http")(logging_middleware)
app.middleware("http")(error_logging_middleware)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to the Timesheet Management API"}

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    logger.info(f"Health check accessed from {request.client.host}")
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

@app.get("/time-entries", response_model=List[schemas.TimeEntry])
def get_time_entries(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    date: Optional[date] = Query(default=None, description="Filter entries by specific date (YYYY-MM-DD)"),
    project_id: Optional[str] = Query(default=None, description="Filter by project ID"),
    customer_name: Optional[str] = Query(default=None, description="Filter by customer name"),
    db: Session = Depends(get_db)
):
    """Get paginated time entries with optional date, project, and customer filters"""
    try:
        service = TimeEntryService(db)
        entries = service.get_time_entries(
            project_id=project_id,
            customer_name=customer_name,
            date=date,
            skip=skip,
            limit=limit
        )
        return entries
    except Exception as e:
        logger.error(f"Error getting time entries: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/time-entries", response_model=schemas.TimeEntry, status_code=201)
def create_time_entry(entry: schemas.TimeEntryCreate, db: Session = Depends(get_db)):
    """Create a new time entry"""
    service = TimeEntryService(db)
    return service.create_time_entry(entry)

@app.put("/time-entries/{entry_id}", response_model=schemas.TimeEntry)
def update_time_entry(entry_id: int, entry: schemas.TimeEntryUpdate, db: Session = Depends(get_db)):
    """Update an existing time entry"""
    service = TimeEntryService(db)
    return service.update_time_entry(entry_id, entry)

@app.delete("/time-entries/{entry_id}")
def delete_time_entry(entry_id: int, db: Session = Depends(get_db)):
    """Delete a time entry"""
    service = TimeEntryService(db)
    return service.delete_time_entry(entry_id)

@app.post("/time-entries/upload", status_code=202)
async def upload_timesheet(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload timesheet file (Excel/CSV)"""
    try:
        contents = await file.read()
        service = TimeEntryService(db)
        entries = service.import_timesheet(contents, file.filename)
        return {"message": "File processed successfully", "entries_created": len(entries)}
    except Exception as e:
        logger.error(f"Error processing timesheet: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Placeholder for GET /projects endpoint
@app.get("/projects")
async def get_projects(db: Session = Depends(get_db)):
    """Get all projects."""
    #Implementation needed here.
    return []

# Placeholder for POST /projects endpoint
@app.post("/projects")
async def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    #Implementation needed here.
    return {}

# Placeholder for PUT /projects/{project_id} endpoint
@app.put("/projects/{project_id}")
async def update_project(project_id: int, project: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    """Update an existing project."""
    #Implementation needed here.
    return {}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    correlation_id = Logger().get_correlation_id()
    logger.error(f"Unhandled exception in request: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "correlation_id": correlation_id
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
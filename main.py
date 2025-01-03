from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import calendar
import pandas as pd

import crud, models, schemas, database, utils

app = FastAPI(title="Timesheet Management API")

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

# Customer endpoints
@app.post("/customers/", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(database.get_db)):
    return crud.create_customer(db, customer)

@app.get("/customers/", response_model=List[schemas.Customer])
def read_customers(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return crud.get_customers(db, skip=skip, limit=limit)

@app.get("/customers/{name}", response_model=schemas.Customer)
def read_customer(name: str, db: Session = Depends(database.get_db)):
    customer = crud.get_customer(db, name)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

# Project Manager endpoints
@app.post("/project-managers/", response_model=schemas.ProjectManager)
def create_project_manager(project_manager: schemas.ProjectManagerCreate, db: Session = Depends(database.get_db)):
    return crud.create_project_manager(db, project_manager)

@app.get("/project-managers/", response_model=List[schemas.ProjectManager])
def read_project_managers(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    return crud.get_project_managers(db, skip=skip, limit=limit)

@app.get("/project-managers/{name}", response_model=schemas.ProjectManager)
def read_project_manager(name: str, db: Session = Depends(database.get_db)):
    project_manager = crud.get_project_manager(db, name)
    if project_manager is None:
        raise HTTPException(status_code=404, detail="Project Manager not found")
    return project_manager

# Project endpoints
@app.post("/projects/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(database.get_db)):
    return crud.create_project(db, project)

@app.get("/projects/", response_model=List[schemas.Project])
def read_projects(
    customer_name: Optional[str] = None,
    project_manager_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    return crud.get_projects(db, customer_name, project_manager_name, skip, limit)

@app.get("/projects/{project_id}", response_model=schemas.Project)
def read_project(project_id: str, db: Session = Depends(database.get_db)):
    project = crud.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# Time Entry endpoints
@app.post("/upload/", response_model=List[schemas.TimeEntry])
async def upload_timesheet(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    try:
        if file.filename.endswith('.xlsx'):
            entries = utils.parse_excel(file.file)
        elif file.filename.endswith('.csv'):
            entries = utils.parse_csv(file.file)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        created_entries = []
        for entry in entries:
            created_entry = crud.create_time_entry(db, entry)
            created_entries.append(created_entry)

        return created_entries
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/time-entries/", response_model=schemas.TimeEntry)
def create_time_entry(entry: schemas.TimeEntryCreate, db: Session = Depends(database.get_db)):
    return crud.create_time_entry(db, entry)

@app.get("/time-entries/", response_model=List[schemas.TimeEntry])
def read_time_entries(
    project_id: Optional[str] = None,
    customer_name: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    return crud.get_time_entries(db, project_id, customer_name, skip, limit)

@app.get("/time-entries/{entry_id}", response_model=schemas.TimeEntry)
def read_time_entry(entry_id: int, db: Session = Depends(database.get_db)):
    entry = crud.get_time_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Time entry not found")
    return entry

@app.put("/time-entries/{entry_id}", response_model=schemas.TimeEntry)
def update_time_entry(
    entry_id: int,
    entry: schemas.TimeEntryUpdate,
    db: Session = Depends(database.get_db)
):
    updated_entry = crud.update_time_entry(db, entry_id, entry)
    if updated_entry is None:
        raise HTTPException(status_code=404, detail="Time entry not found")
    return updated_entry

@app.delete("/time-entries/{entry_id}")
def delete_time_entry(entry_id: int, db: Session = Depends(database.get_db)):
    success = crud.delete_time_entry(db, entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Time entry not found")
    return {"message": "Entry deleted successfully"}

@app.get("/reports/weekly", response_model=schemas.WeeklyReport)
def get_weekly_report(
    date: datetime = Query(default=None),
    project_id: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    if date is None:
        date = datetime.now()

    week_start = date - timedelta(days=date.weekday())
    week_end = week_start + timedelta(days=6)

    query = db.query(
        models.TimeEntry.project_id,
        models.TimeEntry.customer_name,
        db.func.sum(models.TimeEntry.hours).label('total_hours')
    ).filter(
        models.TimeEntry.week_number == week_start.isocalendar()[1]
    ).group_by(
        models.TimeEntry.project_id,
        models.TimeEntry.customer_name
    )

    if project_id:
        query = query.filter(models.TimeEntry.project_id == project_id)

    results = query.all()

    entries = [
        schemas.ReportEntry(
            employee_id=r.customer_name,
            total_hours=float(r.total_hours),
            project=r.project_id,
            period=f"{week_start.date()} to {week_end.date()}"
        )
        for r in results
    ]

    total_hours = sum(entry.total_hours for entry in entries)

    return schemas.WeeklyReport(
        entries=entries,
        total_hours=total_hours,
        week_start=week_start,
        week_end=week_end
    )

@app.get("/reports/monthly", response_model=schemas.MonthlyReport)
def get_monthly_report(
    year: int = Query(...),
    month: int = Query(...),
    project_id: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(
        models.TimeEntry.project_id,
        models.TimeEntry.customer_name,
        db.func.sum(models.TimeEntry.hours).label('total_hours')
    ).filter(
        models.TimeEntry.month == calendar.month_name[month]
    ).group_by(
        models.TimeEntry.project_id,
        models.TimeEntry.customer_name
    )

    if project_id:
        query = query.filter(models.TimeEntry.project_id == project_id)

    results = query.all()

    entries = [
        schemas.ReportEntry(
            employee_id=r.customer_name,
            total_hours=float(r.total_hours),
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
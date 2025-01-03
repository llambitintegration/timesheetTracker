from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import pandas as pd

import crud, models, schemas, database, utils

app = FastAPI(title="Timesheet Management API")

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

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
def create_time_entry(
    entry: schemas.TimeEntryCreate,
    db: Session = Depends(database.get_db)
):
    return crud.create_time_entry(db, entry)

@app.get("/time-entries/", response_model=List[schemas.TimeEntry])
def read_time_entries(
    employee_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db)
):
    entries = crud.get_time_entries(db, employee_id, skip, limit)
    return entries

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
    employee_id: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    if date is None:
        date = datetime.now()

    results, week_start, week_end = crud.get_weekly_report(db, employee_id, date)

    entries = [
        schemas.ReportEntry(
            employee_id=r.employee_id,
            total_hours=float(r.total_hours),
            project=r.project,
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
    employee_id: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    results = crud.get_monthly_report(db, employee_id, year, month)

    entries = [
        schemas.ReportEntry(
            employee_id=r.employee_id,
            total_hours=float(r.total_hours),
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
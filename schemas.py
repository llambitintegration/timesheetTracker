from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class TimeEntryBase(BaseModel):
    employee_id: str
    project: str
    task: str
    hours: float = Field(..., gt=0, le=24)
    date: datetime
    description: Optional[str] = None

class TimeEntryCreate(TimeEntryBase):
    pass

class TimeEntry(TimeEntryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TimeEntryUpdate(BaseModel):
    project: Optional[str] = None
    task: Optional[str] = None
    hours: Optional[float] = Field(None, gt=0, le=24)
    date: Optional[datetime] = None
    description: Optional[str] = None

class ReportEntry(BaseModel):
    employee_id: str
    total_hours: float
    project: str
    period: str

class WeeklyReport(BaseModel):
    entries: List[ReportEntry]
    total_hours: float
    week_start: datetime
    week_end: datetime

class MonthlyReport(BaseModel):
    entries: List[ReportEntry]
    total_hours: float
    month: int
    year: int
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional, List

class CustomerBase(BaseModel):
    name: str
    location: str

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    class Config:
        from_attributes = True

class ProjectManagerBase(BaseModel):
    name: str
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')

class ProjectManagerCreate(ProjectManagerBase):
    pass

class ProjectManager(ProjectManagerBase):
    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    project_id: str
    customer_name: str
    location: str
    project_manager_name: str
    project_type: str

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    class Config:
        from_attributes = True

class TimeEntryBase(BaseModel):
    week_number: int = Field(..., ge=1, le=53)
    month: str = Field(..., pattern=r'^(January|February|March|April|May|June|July|August|September|October|November|December)$')
    category: str
    subcategory: str
    customer_name: str
    project_id: str
    task_description: Optional[str] = None
    hours: float = Field(..., gt=0, le=24)

class TimeEntryCreate(TimeEntryBase):
    pass

class TimeEntry(TimeEntryBase):
    id: int

    class Config:
        from_attributes = True

class TimeEntryUpdate(BaseModel):
    week_number: Optional[int] = Field(None, ge=1, le=53)
    month: Optional[str] = Field(None, pattern=r'^(January|February|March|April|May|June|July|August|September|October|November|December)$')
    category: Optional[str] = None
    subcategory: Optional[str] = None
    customer_name: Optional[str] = None
    project_id: Optional[str] = None
    task_description: Optional[str] = None
    hours: Optional[float] = Field(None, gt=0, le=24)

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
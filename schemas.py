
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Customer schemas
class CustomerBase(BaseModel):
    name: str
    location: str

class CustomerCreate(CustomerBase):
    pass

class Customer(CustomerBase):
    class Config:
        from_attributes = True

# Project Manager schemas
class ProjectManagerBase(BaseModel):
    name: str
    email: str

class ProjectManagerCreate(ProjectManagerBase):
    pass

class ProjectManager(ProjectManagerBase):
    class Config:
        from_attributes = True

# Project schemas
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

# Time Entry schemas
class TimeEntryBase(BaseModel):
    week_number: int = Field(..., ge=1, le=53)
    month: str = Field(..., pattern=r'^(January|February|March|April|May|June|July|August|September|October|November|December)$')
    category: str
    subcategory: str
    customer: Optional[str] = None
    project: Optional[str] = None
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
    customer: Optional[str] = None
    project: Optional[str] = None
    task_description: Optional[str] = None
    hours: Optional[float] = Field(None, gt=0, le=24)

# Report schemas
class ReportEntry(BaseModel):
    total_hours: float
    category: str
    project: Optional[str]
    period: str

class WeeklyReport(BaseModel):
    entries: List[ReportEntry]
    total_hours: float
    week_number: int
    month: str

class MonthlyReport(BaseModel):
    entries: List[ReportEntry]
    total_hours: float
    month: str
    year: int

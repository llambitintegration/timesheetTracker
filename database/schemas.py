from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from models.timeEntry import TimeEntry as TimeEntryModel
from models.customerModel import Customer as CustomerModel
from models.projectModel import Project as ProjectModel
from models.projectManagerModel import ProjectManager as ProjectManagerModel

class BaseSchema(BaseModel):
    """Base schema with common fields"""
    id: Optional[int] = None  # ID field is optional in input, will be set by database
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Time Entry Schemas
class TimeEntryBase(BaseSchema):
    """Base schema for time entries"""
    category: str
    subcategory: str
    customer: Optional[str] = None
    project: Optional[str] = None
    task_description: Optional[str] = None
    hours: float = Field(default=0.0, ge=0, le=24)  # Default to 0, allow 0 hours
    date: date

class TimeEntryCreate(BaseModel):
    """Schema for creating time entries"""
    category: str
    subcategory: str
    customer: Optional[str] = None
    project: Optional[str] = None
    task_description: Optional[str] = None
    hours: float = Field(default=0.0, ge=0, le=24)  # Default to 0, allow 0 hours
    date: date  # Only required field for time calculations

    model_config = ConfigDict(from_attributes=True)

class TimeEntryUpdate(BaseSchema):
    """Schema for updating time entries"""
    category: Optional[str] = None
    subcategory: Optional[str] = None
    customer: Optional[str] = None
    project: Optional[str] = None
    task_description: Optional[str] = None
    hours: Optional[float] = Field(None, ge=0, le=24)
    date: Optional[date] = None

class TimeEntry(TimeEntryBase):
    """Schema for time entry responses"""
    week_number: int
    month: str

    class Config:
        orm_model = TimeEntryModel

# Time Summary Schemas
class DateRangeParams(BaseModel):
    """Schema for date range parameters"""
    start_date: date
    end_date: date

class TimeSummaryEntry(BaseModel):
    """Schema for time summary entries"""
    date: date
    total_hours: float
    entries: List[TimeEntry]

    model_config = ConfigDict(from_attributes=True)

class TimeSummary(BaseModel):
    """Schema for time summaries"""
    total_hours: float
    entries: List[TimeSummaryEntry]

    model_config = ConfigDict(from_attributes=True)

# Customer Schemas
class CustomerBase(BaseSchema):
    name: str
    contact_email: str
    industry: Optional[str] = None
    status: str = "active"
    address: Optional[str] = None
    phone: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseSchema):
    """Schema for updating customers"""
    name: Optional[str] = None
    contact_email: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive)$")
    address: Optional[str] = None
    phone: Optional[str] = None

class Customer(CustomerBase):
    class Config:
        orm_model = CustomerModel

# Project Manager Schemas
class ProjectManagerBase(BaseSchema):
    name: str
    email: str

class ProjectManagerCreate(ProjectManagerBase):
    pass

class ProjectManager(ProjectManagerBase):
    class Config:
        orm_model = ProjectManagerModel

# Project Schemas
class ProjectBase(BaseSchema):
    project_id: str
    name: str
    description: Optional[str] = None
    customer: str
    project_manager: str
    status: str = "active"

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    class Config:
        orm_model = ProjectModel


class ReportEntry(BaseModel):
    """Schema for report entries"""
    total_hours: float
    category: str
    project: str
    period: str

    model_config = ConfigDict(from_attributes=True)

class WeeklyReport(BaseModel):
    """Schema for weekly reports"""
    entries: List[ReportEntry]
    total_hours: float
    week_number: int
    month: str

    model_config = ConfigDict(from_attributes=True)

class MonthlyReport(BaseModel):
    """Schema for monthly reports"""
    entries: List[ReportEntry]
    total_hours: float
    month: int
    year: int

    model_config = ConfigDict(from_attributes=True)
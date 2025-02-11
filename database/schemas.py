from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
from models.timeEntry import TimeEntry as TimeEntryModel
from models.customerModel import Customer as CustomerModel
from models.projectModel import Project as ProjectModel
from models.projectManagerModel import ProjectManager as ProjectManagerModel

class BaseSchema(BaseModel):
    """Base schema with common fields"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

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
    hours: float = Field(default=0.0, ge=0, le=24)
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

    model_config = ConfigDict(from_attributes=True)

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

class CustomerBase(BaseSchema):
    name: str
    contact_email: str
    industry: Optional[str] = None
    status: str = "active"
    address: Optional[str] = None
    phone: Optional[str] = None

class CustomerCreate(BaseModel):
    """Schema for creating new customers"""
    name: str
    contact_email: str
    industry: Optional[str] = None
    status: str = "active"
    address: Optional[str] = None
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    def to_dict(self) -> dict:
        """Convert to dictionary for database operations"""
        return self.model_dump(exclude_unset=True)

class CustomerUpdate(BaseSchema):
    """Schema for updating customers"""
    name: Optional[str] = None
    contact_email: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive)$")
    address: Optional[str] = None
    phone: Optional[str] = None

class Customer(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

class ProjectManagerBase(BaseSchema):
    name: str
    email: str

class ProjectManagerCreate(BaseModel):
    """Schema for creating new project managers"""
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)

class ProjectManagerUpdate(BaseSchema):
    """Schema for updating project managers"""
    name: Optional[str] = None
    email: Optional[str] = None

class ProjectManager(ProjectManagerBase):
    model_config = ConfigDict(from_attributes=True)

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

class ProjectBase(BaseModel):
    """Base schema for projects"""
    project_id: str
    name: str
    description: Optional[str] = None
    customer: str = Field(..., description="Customer name, required for all projects")
    project_manager: str = Field(..., description="Project manager name, required for all projects")
    status: str = "active"

    model_config = ConfigDict(from_attributes=True)

class ProjectCreate(BaseModel):
    """Schema for creating new projects"""
    project_id: str
    name: str
    description: Optional[str] = None
    customer: Optional[str] = Field(default='Unassigned', description="Customer name")
    project_manager: Optional[str] = Field(default='-', description="Project manager name")
    status: str = "active"

    model_config = ConfigDict(from_attributes=True)

    def to_dict(self) -> dict:
        """Convert to dictionary for database operations"""
        return self.model_dump(exclude_unset=True)

class ProjectUpdate(BaseModel):
    """Schema for updating projects"""
    project_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    customer: Optional[str] = None
    project_manager: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive)$")

    model_config = ConfigDict(from_attributes=True)

class Project(ProjectBase):
    """Full project model with all fields"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
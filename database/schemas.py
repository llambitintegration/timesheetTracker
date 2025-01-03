
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
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

# Time Entry Schemas
class TimeEntryBase(BaseSchema):
    """Base schema for time entries"""
    week_number: int = Field(..., ge=1, le=53)
    month: str = Field(..., pattern=r'^(January|February|March|April|May|June|July|August|September|October|November|December)$')
    category: str
    subcategory: str
    customer: Optional[str] = None
    project: Optional[str] = None
    task_description: Optional[str] = None
    hours: float = Field(..., ge=0, le=24)

class TimeEntryCreate(TimeEntryBase):
    """Schema for creating time entries"""
    pass

class TimeEntryUpdate(BaseSchema):
    """Schema for updating time entries"""
    week_number: Optional[int] = Field(None, ge=1, le=53)
    month: Optional[str] = Field(None, pattern=r'^(January|February|March|April|May|June|July|August|September|October|November|December)$')
    category: Optional[str] = None
    subcategory: Optional[str] = None
    customer: Optional[str] = None
    project: Optional[str] = None
    task_description: Optional[str] = None
    hours: Optional[float] = Field(None, gt=0, le=24)

class TimeEntry(TimeEntryBase):
    """Schema for time entry responses"""
    class Config:
        orm_model = TimeEntryModel

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

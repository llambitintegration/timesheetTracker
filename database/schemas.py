
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class BaseSchema(BaseModel):
    """Base schema with common fields"""
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

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

class TimeEntry(TimeEntryBase):
    """Schema for time entry responses"""
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

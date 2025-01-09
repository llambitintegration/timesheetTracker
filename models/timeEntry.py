from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date
from sqlalchemy.sql import func
from models.baseModel import BaseModel

class TimeEntry(BaseModel):
    """Time entry model for tracking hours"""
    __tablename__ = "time_entries"

    week_number = Column(Integer, nullable=False)
    month = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=False)
    customer = Column(String, ForeignKey('customers.name', ondelete='SET NULL'), nullable=True, server_default='Unassigned')
    project = Column(String, ForeignKey('projects.project_id', ondelete='SET NULL'), nullable=True)
    task_description = Column(String, nullable=True)
    hours = Column(Float, nullable=False)
    date = Column(Date, nullable=False)  # Explicit date field for timesheet entries
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<TimeEntry(id={self.id}, date={self.date}, hours={self.hours}, project={self.project})>"
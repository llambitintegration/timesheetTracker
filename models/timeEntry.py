from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date
from sqlalchemy.sql import func
from models.baseModel import BaseModel
from datetime import datetime, date
from typing import Optional

class TimeEntry(BaseModel):
    """Time entry model for tracking hours"""
    __tablename__ = "time_entries"

    # These will be auto-calculated based on date
    week_number = Column(Integer, nullable=False)
    month = Column(String, nullable=False)

    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=False)
    customer = Column(String, ForeignKey('customers.name', ondelete='SET NULL'), nullable=True, server_default='Unassigned')
    project = Column(String, ForeignKey('projects.project_id', ondelete='SET NULL'), nullable=True)
    task_description = Column(String, nullable=True)
    hours = Column(Float, nullable=False, server_default='0')  # Default to 0
    date = Column(Date, nullable=False)  # Explicit date field for timesheet entries

    def __init__(self, **kwargs):
        # Calculate week_number and month from date if not provided
        if 'date' in kwargs:
            entry_date = kwargs['date']
            if isinstance(entry_date, str):
                entry_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
            if 'week_number' not in kwargs:
                kwargs['week_number'] = self.get_week_number(entry_date)
            if 'month' not in kwargs:
                kwargs['month'] = self.get_month_name(entry_date)

        # Set default hours if not provided
        if 'hours' not in kwargs:
            kwargs['hours'] = 0.0

        # Handle None or empty string values for customer and project
        if not kwargs.get('customer') or kwargs.get('customer') == '-':
            kwargs['customer'] = 'Unassigned'
        if not kwargs.get('project') or kwargs.get('project') == '-':
            kwargs['project'] = 'Unassigned'

        super().__init__(**kwargs)

    def __repr__(self):
        return f"<TimeEntry(id={self.id}, date={self.date}, hours={self.hours}, project={self.project})>"

    @staticmethod
    def get_week_number(entry_date: date) -> int:
        """Calculate ISO week number from date"""
        if isinstance(entry_date, str):
            entry_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
        return entry_date.isocalendar()[1]

    @staticmethod
    def get_month_name(entry_date: date) -> str:
        """Get month name from date"""
        if isinstance(entry_date, str):
            entry_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
        return entry_date.strftime('%B')
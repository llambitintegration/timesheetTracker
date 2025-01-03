
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from models.baseModel import BaseModel

class TimeEntry(BaseModel):
    """Time entry model for tracking hours"""
    __tablename__ = "time_entries"

    week_number = Column(Integer, nullable=False)
    month = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=False)
    customer = Column(String, ForeignKey('customers.name'), nullable=True)
    project = Column(String, ForeignKey('projects.project_id'), nullable=True)
    task_description = Column(String)
    hours = Column(Float, nullable=False)

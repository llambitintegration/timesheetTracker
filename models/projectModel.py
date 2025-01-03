
from sqlalchemy import Column, String, ForeignKey
from models.baseModel import BaseModel

class Project(BaseModel):
    """Project model for tracking customer projects"""
    __tablename__ = "projects"

    project_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    description = Column(String)
    customer = Column(String, ForeignKey('customers.name'), nullable=False)
    project_manager = Column(String, ForeignKey('project_managers.name'), nullable=False)
    status = Column(String, default='active')


from sqlalchemy import Column, String
from models.baseModel import BaseModel

class ProjectManager(BaseModel):
    """Project Manager model for tracking project managers"""
    __tablename__ = "project_managers"

    name = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)

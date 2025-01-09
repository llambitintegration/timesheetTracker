
from sqlalchemy import Column, String, ForeignKey
from models.baseModel import BaseModel

class Project(BaseModel):
    """Project model for tracking customer projects"""
    __tablename__ = "projects"

    project_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    customer = Column(String, ForeignKey('customers.name', ondelete='SET NULL'), nullable=True)
    project_manager = Column(String, ForeignKey('project_managers.name', ondelete='SET NULL'), nullable=True)
    status = Column(String, default='active')

    def __repr__(self):
        return f"<Project(id={self.id}, project_id={self.project_id}, name={self.name})>"

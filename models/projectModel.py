from sqlalchemy import Column, String, ForeignKey, text
from models.baseModel import BaseModel

class Project(BaseModel):
    """Project model for tracking customer projects"""
    __tablename__ = "projects"

    project_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    customer = Column(String, ForeignKey('customers.name', ondelete='SET NULL'), nullable=True)
    project_manager = Column(String, ForeignKey('project_managers.name', ondelete='SET NULL'), nullable=True, default='-')
    status = Column(String, nullable=False, server_default=text("'active'"), default='active')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.status is None:
            self.status = 'active'

    def __repr__(self):
        return f"<Project(id={self.id}, project_id={self.project_id}, name={self.name})>"
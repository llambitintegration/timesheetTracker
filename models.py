
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"
    
    name = Column(String, primary_key=True)
    location = Column(String, nullable=False)
    
    projects = relationship("Project", back_populates="customer")
    time_entries = relationship("TimeEntry", back_populates="customer_rel")

class ProjectManager(Base):
    __tablename__ = "project_managers"
    
    name = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    
    projects = relationship("Project", back_populates="project_manager")

class Project(Base):
    __tablename__ = "projects"
    
    project_id = Column(String, primary_key=True)
    customer_name = Column(String, ForeignKey('customers.name'), nullable=False)
    location = Column(String, nullable=False)
    project_manager_name = Column(String, ForeignKey('project_managers.name'), nullable=False)
    project_type = Column(String, nullable=False)
    
    customer = relationship("Customer", back_populates="projects")
    project_manager = relationship("ProjectManager", back_populates="projects")
    time_entries = relationship("TimeEntry", back_populates="project_rel")

class TimeEntry(Base):
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_number = Column(Integer, nullable=False)
    month = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=False)
    customer = Column(String, ForeignKey('customers.name'))
    project = Column(String, ForeignKey('projects.project_id'))
    task_description = Column(String)
    hours = Column(Float, nullable=False)

    customer_rel = relationship("Customer", back_populates="time_entries")
    project_rel = relationship("Project", back_populates="time_entries")

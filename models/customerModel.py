from sqlalchemy import Column, String
from models.baseModel import BaseModel

class Customer(BaseModel):
    """Customer model for tracking clients"""
    __tablename__ = "customers"

    name = Column(String, unique=True, nullable=False)
    contact_email = Column(String, unique=True)
    industry = Column(String)
    status = Column(String, default='active')
    address = Column(String)
    phone = Column(String)
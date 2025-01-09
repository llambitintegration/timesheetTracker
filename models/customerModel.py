from sqlalchemy import Column, String, text
from models.baseModel import BaseModel

class Customer(BaseModel):
    """Customer model for tracking clients"""
    __tablename__ = "customers"

    name = Column(String, unique=True, nullable=False)
    contact_email = Column(String, unique=True)
    industry = Column(String)
    status = Column(String, nullable=False, server_default=text("'active'"), default='active')
    address = Column(String)
    phone = Column(String)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.status is None:
            self.status = 'active'
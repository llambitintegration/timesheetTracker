import time
from datetime import datetime
from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.created_at = datetime.now()
        time.sleep(0.001)  # Ensure timestamps are different
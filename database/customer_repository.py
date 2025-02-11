
from typing import Optional
from sqlalchemy.orm import Session
from models.customerModel import Customer
from .base_repository import BaseRepository

class CustomerRepository(BaseRepository[Customer]):
    def __init__(self):
        super().__init__(Customer)

    def get_by_name(self, db: Session, name: str) -> Optional[Customer]:
        return db.query(self.model).filter(self.model.name == name).first()

    def get_by_id(self, db: Session, id: int) -> Optional[Customer]:
        return db.query(self.model).filter(self.model.id == id).first()

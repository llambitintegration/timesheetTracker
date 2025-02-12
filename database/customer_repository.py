from typing import Optional
from sqlalchemy.orm import Session
from models.customerModel import Customer
from .base_repository import BaseRepository
from utils.logger import Logger

logger = Logger().get_logger()

class CustomerRepository(BaseRepository[Customer]):
    def __init__(self):
        super().__init__(Customer)
        logger.debug("CustomerRepository initialized")

    def get_by_name(self, db: Session, name: str) -> Optional[Customer]:
        """Get a customer by name."""
        logger.debug(f"Fetching customer by name: {name}")
        return db.query(self.model).filter(self.model.name == name).first()

    def get_by_id(self, db: Session, id: int) -> Optional[Customer]:
        """Get a customer by ID."""
        logger.debug(f"Fetching customer by ID: {id}")
        return db.query(self.model).filter(self.model.id == id).first()

    def delete_by_name(self, db: Session, name: str) -> bool:
        """Delete a customer by name."""
        logger.debug(f"Attempting to delete customer by name: {name}")
        customer = self.get_by_name(db, name)
        if customer:
            db.delete(customer)
            db.commit()
            logger.info(f"Successfully deleted customer: {name}")
            return True
        logger.warning(f"Customer not found for deletion: {name}")
        return False

    def create(self, db: Session, data: dict) -> Customer:
        """Create a new customer with improved error handling."""
        logger.debug(f"Creating customer with data: {data}")
        try:
            db_customer = Customer(**data)
            db.add(db_customer)
            db.commit()
            db.refresh(db_customer)
            logger.info(f"Successfully created customer: {db_customer.name}")
            return db_customer
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            db.rollback()
            raise
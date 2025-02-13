from typing import Optional, Dict, Any, Union
import sqlalchemy as sa
from sqlalchemy.orm import Session
from models.customerModel import Customer
from models.projectModel import Project
from models.timeEntry import TimeEntry
from .base_repository import BaseRepository
from utils.logger import Logger
from database import schemas

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
        """Delete customer with cascade handling."""
        logger.debug(f"Attempting to delete customer by name: {name}")
        try:
            customer = self.get_by_name(db, name)
            if customer:
                # Update related projects and time entries to set customer to NULL
                db.query(Project).filter(
                    Project.customer == name
                ).update(
                    {Project.customer: None},
                    synchronize_session=False
                )
                db.query(TimeEntry).filter(
                    TimeEntry.customer == name
                ).update(
                    {TimeEntry.customer: None},
                    synchronize_session=False
                )

                db.delete(customer)
                db.commit()
                logger.info(f"Successfully deleted customer: {name}")
                return True
            logger.warning(f"Customer not found for deletion: {name}")
            return False
        except Exception as e:
            logger.error(f"Error in cascade delete: {str(e)}")
            db.rollback()
            raise

    def create(self, db: Session, data: Union[Dict[str, Any], schemas.CustomerCreate, Customer]) -> Customer:
        """Create with better error handling."""
        logger.debug(f"Creating customer with data: {data}")
        try:
            if isinstance(data, Customer):
                db_customer = data
            elif hasattr(data, 'model_dump'):
                customer_data = data.model_dump()
                db_customer = Customer(**customer_data)
            elif isinstance(data, dict):
                db_customer = Customer(**data)
            else:
                raise ValueError(f"Invalid data type for customer creation: {type(data)}")

            db.add(db_customer)
            db.commit()
            db.refresh(db_customer)
            logger.info(f"Successfully created customer: {db_customer.name}")
            return db_customer
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            db.rollback()
            raise

    def update(self, db: Session, item: Customer) -> Customer:
        """Update with cascade handling."""
        logger.debug(f"Updating customer: {item.name}")
        try:
            # Get the current customer to check for name changes
            current = self.get_by_id(db, item.id)
            if not current:
                raise ValueError(f"Customer with ID {item.id} not found")

            # Update related records with new customer name
            if current.name != item.name:
                db.query(Project).filter(
                    Project.customer == current.name
                ).update(
                    {Project.customer: item.name},
                    synchronize_session=False
                )
                db.query(TimeEntry).filter(
                    TimeEntry.customer == current.name
                ).update(
                    {TimeEntry.customer: item.name},
                    synchronize_session=False
                )

            # Perform the update
            db.merge(item)
            db.commit()
            db.refresh(item)
            logger.info(f"Successfully updated customer: {item.name}")
            return item
        except Exception as e:
            logger.error(f"Error updating customer: {str(e)}")
            db.rollback()
            raise
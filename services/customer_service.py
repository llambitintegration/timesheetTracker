from sqlalchemy.orm import Session
from typing import List, Optional
from database.customer_repository import CustomerRepository
from database import schemas
from models.customerModel import Customer
from utils.logger import Logger
from fastapi import HTTPException

logger = Logger().get_logger()

class CustomerService:
    def __init__(self, db: Session):
        self.db = db
        self.customer_repo = CustomerRepository()
        logger.debug("CustomerService initialized with database session")

    def create_customer(self, customer: schemas.CustomerCreate) -> Customer:
        """Create a new customer with validation."""
        try:
            logger.debug(f"Starting creation of customer with data: {customer.model_dump()}")

            # Check if customer already exists
            existing_customer = self.customer_repo.get_by_name(self.db, customer.name)
            if existing_customer:
                logger.warning(f"Customer with name {customer.name} already exists")
                raise HTTPException(
                    status_code=400,
                    detail=f"Customer with name {customer.name} already exists"
                )

            # Convert pydantic model to dict and create customer
            customer_dict = customer.model_dump()
            created_customer = self.customer_repo.create(self.db, customer_dict)

            logger.info(f"Successfully created customer: {created_customer.name}")
            return created_customer
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_customer(self, name: str) -> Optional[Customer]:
        """Retrieve a customer by name."""
        logger.debug(f"Attempting to fetch customer with name: {name}")
        customer = self.customer_repo.get_by_name(self.db, name)
        if not customer:
            logger.warning(f"No customer found with name: {name}")
            raise HTTPException(status_code=404, detail=f"Customer not found: {name}")
        logger.info(f"Found customer: {name}")
        return customer

    def get_all_customers(self, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Retrieve all customers with pagination."""
        logger.debug(f"Fetching customers with offset={skip}, limit={limit}")
        customers = self.customer_repo.get_all(self.db, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(customers)} customers")
        return customers

    def update_customer(self, name: str, customer_update: schemas.CustomerUpdate) -> Optional[Customer]:
        """Update an existing customer."""
        logger.debug(f"Attempting to update customer {name} with data: {customer_update.model_dump(exclude_unset=True)}")

        existing_customer = self.customer_repo.get_by_name(self.db, name)
        if not existing_customer:
            logger.warning(f"Customer not found: {name}")
            raise HTTPException(status_code=404, detail=f"Customer not found: {name}")

        try:
            # Update only provided fields
            update_data = customer_update.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(existing_customer, key, value)

            updated_customer = self.customer_repo.update(self.db, existing_customer)
            logger.info(f"Successfully updated customer: {name}")
            return updated_customer
        except Exception as e:
            logger.error(f"Error updating customer {name}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    def delete_customer(self, name: str) -> bool:
        """Delete a customer by name."""
        logger.debug(f"Attempting to delete customer with name: {name}")
        try:
            success = self.customer_repo.delete_by_name(self.db, name)
            if not success:
                logger.warning(f"Customer not found for deletion: {name}")
                raise HTTPException(status_code=404, detail=f"Customer not found: {name}")
            logger.info(f"Successfully deleted customer: {name}")
            return success
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting customer {name}: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
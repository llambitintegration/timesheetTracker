from sqlalchemy.orm import Session
from typing import List, Optional
from database.customer_repository import CustomerRepository
from database import schemas
from models.customerModel import Customer
from utils.logger import Logger

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
                raise ValueError(f"Customer with name {customer.name} already exists")

            # Convert pydantic model to dict and create customer, excluding ID and timestamps
            customer_data = customer.model_dump(exclude={'id', 'created_at', 'updated_at'})
            logger.debug("Adding customer to database session")
            created_customer = self.customer_repo.create(self.db, customer_data)

            logger.info(f"Successfully created customer: {created_customer.name}")
            return created_customer
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            self.db.rollback()
            raise

    def get_customer(self, name: str) -> Optional[Customer]:
        """Retrieve a customer by name."""
        logger.debug(f"Attempting to fetch customer with name: {name}")
        customer = self.customer_repo.get_by_name(self.db, name)
        if customer:
            logger.info(f"Found customer: {name}")
        else:
            logger.info(f"No customer found with name: {name}")
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
            return None

        try:
            # Exclude ID and timestamps from update data
            update_data = customer_update.model_dump(exclude={'id', 'created_at', 'updated_at'}, exclude_unset=True)
            for key, value in update_data.items():
                setattr(existing_customer, key, value)

            updated_customer = self.customer_repo.update(self.db, existing_customer)
            logger.info(f"Successfully updated customer: {name}")
            return updated_customer
        except Exception as e:
            logger.error(f"Error updating customer {name}: {str(e)}")
            self.db.rollback()
            raise
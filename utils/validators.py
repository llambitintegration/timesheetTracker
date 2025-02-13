"""Database validation utilities for CSV data"""
from typing import List, Dict, Optional, Tuple, Union
from sqlalchemy.orm import Session
from models import Customer, Project, ProjectManager
from utils.logger import Logger
from database.schemas import TimeEntryCreate
from sqlalchemy.exc import IntegrityError

logger = Logger().get_logger()

def normalize_customer_name(name: Optional[str]) -> Optional[str]:
    """Normalize customer name, handling empty and dash values"""
    if not name or str(name).strip() in ['-', '', 'None', 'null', 'NA']:
        return None
    return str(name).strip()

def normalize_project_id(project_id: Optional[str]) -> Optional[str]:
    """Normalize project ID for database lookup.
    Converts spaces and hyphens to underscores.
    Returns None if project_id is invalid."""
    if not project_id or str(project_id).strip() in ['-', '', 'None', 'null', 'NA']:
        logger.debug(f"Converting empty/invalid project ID to None")
        return None

    # Replace both hyphens and spaces with underscores
    normalized = str(project_id).strip()
    normalized = normalized.replace('-', '_').replace(' ', '_')
    return normalized

def normalize_project_manager(manager: Optional[str]) -> Optional[str]:
    """Normalize project manager name for database lookup."""
    if not manager or str(manager).strip() in ['-', '', 'None', 'null', 'NA']:
        return None
    return str(manager).strip()

def validate_database_references(
    db: Session,
    entries: List[TimeEntryCreate]
) -> Tuple[List[TimeEntryCreate], List[Dict]]:
    """
    Validate database references in time entries.
    Returns tuple of (valid_entries, validation_errors).
    """
    processed_entries = []
    validation_errors = []

    logger.debug("Starting database reference validation")

    for entry in entries:
        # Store original values for error messages
        original_customer = entry.customer
        original_project = entry.project
        has_validation_error = False

        # Normalize values
        normalized_customer = normalize_customer_name(entry.customer)
        normalized_project = normalize_project_id(entry.project)

        # Check customer existence if provided
        if normalized_customer:
            customer = db.query(Customer).filter(Customer.name == normalized_customer).first()
            if not customer:
                validation_errors.append({
                    'entry': entry.model_dump(),
                    'error': f"Customer '{original_customer}' not found in database",
                    'type': 'invalid_customer'
                })
                has_validation_error = True
                normalized_customer = None

        # Check project existence if provided
        if normalized_project:
            project = db.query(Project).filter(Project.project_id == normalized_project).first()
            if not project:
                validation_errors.append({
                    'entry': entry.model_dump(),
                    'error': f"Project '{original_project}' not found in database",
                    'type': 'invalid_project'
                })
                has_validation_error = True
                normalized_project = None
            elif project.customer and normalized_customer and project.customer != normalized_customer:
                validation_errors.append({
                    'entry': entry.model_dump(),
                    'error': f"Project '{original_project}' does not belong to customer '{original_customer}'",
                    'type': 'invalid_project_customer_relationship'
                })
                has_validation_error = True
                normalized_project = None
                normalized_customer = None

        # Update entry with normalized values
        entry.customer = normalized_customer
        entry.project = normalized_project
        processed_entries.append(entry)
        logger.debug(f"Processed entry: customer={entry.customer}, project={entry.project}")

    return processed_entries, validation_errors

def ensure_default_project_manager(db: Session):
    """Ensure default project manager exists."""
    pm_repo = ProjectManagerRepository()
    if not pm_repo.get_by_name(db, DEFAULT_PROJECT_MANAGER):
        pm = ProjectManagerCreate(
            name=DEFAULT_PROJECT_MANAGER, 
            email='unassigned@company.com'
        )
        pm_repo.create(db, pm.model_dump())

def ensure_default_customer(db: Session) -> Optional[Customer]:
    """Ensure default customer exists in database."""
    try:
        # Try to get either default customer or "-" customer
        default_customer = db.query(Customer).filter(
            Customer.name.in_([DEFAULT_CUSTOMER, "-"])
        ).first()

        if not default_customer:
            # Create both default entries to handle both cases
            default_customer = Customer(
                name=DEFAULT_CUSTOMER,
                contact_email="unassigned@company.com",
                status="active"
            )
            db.add(default_customer)

            dash_customer = Customer(
                name="-",
                contact_email="unassigned@company.com",
                status="active"
            )
            db.add(dash_customer)

            db.flush()
            logger.info("Created default customers")

        return default_customer
    except IntegrityError as e:
        logger.warning(f"Default customer exists: {str(e)}")
        db.rollback()
        return db.query(Customer).filter(
            Customer.name.in_([DEFAULT_CUSTOMER, "-"])
        ).first()
    except Exception as e:
        logger.error(f"Failed to create default customer: {str(e)}")
        db.rollback()
        return None

def ensure_default_project(db: Session) -> Optional[Project]:
    """Ensure default project exists in database."""
    try:
        default_project = db.query(Project).filter(Project.project_id == DEFAULT_PROJECT).first()
        if not default_project:
            default_project = Project(
                project_id=DEFAULT_PROJECT,
                name="Unassigned",
                customer=DEFAULT_CUSTOMER,
                description="Default project for unassigned entries",
                status="active"
            )
            db.add(default_project)
            db.flush()
            logger.info(f"Created default project: {DEFAULT_PROJECT}")
        return default_project
    except IntegrityError as e:
        logger.warning(f"Default project already exists: {str(e)}")
        db.rollback()
        return db.query(Project).filter(Project.project_id == DEFAULT_PROJECT).first()
    except Exception as e:
        logger.error(f"Failed to create default project: {str(e)}")
        db.rollback()
        return None
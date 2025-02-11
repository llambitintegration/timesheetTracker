"""Database validation utilities for CSV data"""
from typing import List, Dict, Optional, Tuple, Union
from sqlalchemy.orm import Session
from models import Customer, Project
from utils.logger import Logger
from database.schemas import TimeEntryCreate
from sqlalchemy.exc import IntegrityError

logger = Logger().get_logger()

# Default values for missing entries
DEFAULT_CUSTOMER = "Unassigned"
DEFAULT_PROJECT = "Unassigned"
DEFAULT_PROJECT_MANAGER = "Unassigned"

def normalize_customer_name(name: Optional[str]) -> Optional[str]:
    """Normalize customer name, handling empty and dash values"""
    if not name:
        return DEFAULT_CUSTOMER

    name = name.strip()
    if name == '-':
        return DEFAULT_CUSTOMER

    return name

def normalize_project_id(project_id: Optional[str]) -> str:
    """Normalize project ID for database lookup.
    Converts spaces and hyphens to underscores.
    Returns DEFAULT_PROJECT if project_id is invalid or not found."""
    if not project_id or str(project_id).strip() in ['-', '', 'None', 'null', 'NA']:
        logger.debug(f"Converting empty/invalid project ID to {DEFAULT_PROJECT}")
        return DEFAULT_PROJECT


def ensure_default_project_manager(db: Session) -> Optional[ProjectManager]:
    """Ensure default project manager exists in database."""
    try:
        default_pm = db.query(ProjectManager).filter(ProjectManager.name == DEFAULT_PROJECT_MANAGER).first()
        if not default_pm:
            default_pm = ProjectManager(
                name=DEFAULT_PROJECT_MANAGER,
                email="unassigned@example.com"
            )
            db.add(default_pm)
            db.flush()
            logger.info(f"Created default project manager: {DEFAULT_PROJECT_MANAGER}")
        return default_pm
    except Exception as e:
        logger.error(f"Failed to create default project manager: {str(e)}")
        db.rollback()
        return None

    # Replace both hyphens and spaces with underscores
    normalized = str(project_id).strip()
    normalized = normalized.replace('-', '_').replace(' ', '_')
    return normalized

def validate_database_references(
    db: Session,
    entries: List[TimeEntryCreate]
) -> Tuple[List[TimeEntryCreate], List[Dict]]:
    """
    Validate database references in time entries.
    Returns tuple of (valid_entries, validation_errors).
    On validation failure, defaults to Unassigned customer and project.
    """
    processed_entries = []
    validation_errors = []

    logger.debug("Starting database reference validation")

    for entry in entries:
        # Store original values for error messages
        original_customer = entry.customer
        original_project = entry.project
        has_validation_error = False

        # Check customer existence
        if entry.customer != DEFAULT_CUSTOMER:
            customer = db.query(Customer).filter(Customer.name == entry.customer).first()
            if not customer:
                validation_errors.append({
                    'entry': entry.dict(),
                    'error': f"Customer '{original_customer}' not found in database",
                    'type': 'invalid_customer'
                })
                has_validation_error = True

        # Check project existence
        if entry.project != DEFAULT_PROJECT:
            normalized_project_id = normalize_project_id(entry.project)
            project = db.query(Project).filter(Project.project_id == normalized_project_id).first()
            if not project:
                validation_errors.append({
                    'entry': entry.model_dump(),
                    'error': f"Project '{original_project}' not found in database",
                    'type': 'invalid_project'
                })
                has_validation_error = True
            elif project.customer != entry.customer:
                validation_errors.append({
                    'entry': entry.model_dump(),
                    'error': f"Project '{original_project}' does not belong to customer '{original_customer}'",
                    'type': 'invalid_project_customer_relationship'
                })
                has_validation_error = True

        # If any validation error occurred, use default values
        if has_validation_error:
            entry.customer = DEFAULT_CUSTOMER
            entry.project = DEFAULT_PROJECT
            logger.warning(f"Validation failed for entry. Using defaults: customer={DEFAULT_CUSTOMER}, project={DEFAULT_PROJECT}")

        processed_entries.append(entry)
        logger.debug(f"Processed entry: customer={entry.customer}, project={entry.project}")

    return processed_entries, validation_errors

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

def normalize_project_manager(manager: Optional[str]) -> str:
    """Normalize project manager name for database lookup."""
    if not manager or str(manager).strip() in ['-', '', 'None', 'null', 'NA']:
        return DEFAULT_PROJECT_MANAGER
    return str(manager).strip()
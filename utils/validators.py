"""Database validation utilities for CSV data"""
from typing import List, Dict, Optional, Tuple
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

def normalize_customer_name(name: str) -> str:
    """Normalize customer name for database lookup.
    Returns DEFAULT_CUSTOMER if name is invalid or not found."""
    if not name or str(name).strip() in ['-', '', 'None', 'null', 'NA']:
        logger.debug(f"Converting empty/invalid customer name to {DEFAULT_CUSTOMER}")
        return DEFAULT_CUSTOMER

    normalized = str(name).strip()
    logger.debug(f"Normalized customer name: {normalized}")
    return normalized

def normalize_project_id(project_id: str) -> str:
    """Normalize project ID for database lookup.
    Converts spaces and hyphens to underscores for consistent formatting.
    Returns DEFAULT_PROJECT if project_id is invalid or not found."""
    if not project_id or str(project_id).strip() in ['-', '', 'None', 'null', 'NA']:
        logger.debug(f"Converting empty/invalid project ID to {DEFAULT_PROJECT}")
        return DEFAULT_PROJECT

    # Replace both spaces and hyphens with underscores
    normalized = str(project_id).strip().replace('-', '_').replace(' ', '_')
    logger.debug(f"Normalized project ID: {normalized}")
    return normalized

def normalize_project_manager(manager: str) -> str:
    """Normalize project manager name for database lookup."""
    if not manager or str(manager).strip() in ['-', '', 'None', 'null', 'NA']:
        return DEFAULT_PROJECT_MANAGER
    return str(manager).strip()

def ensure_default_customer(db: Session) -> Optional[Customer]:
    """Ensure default customer exists in database."""
    try:
        default_customer = db.query(Customer).filter(Customer.name == DEFAULT_CUSTOMER).first()
        if not default_customer:
            default_customer = Customer(
                name=DEFAULT_CUSTOMER,
                contact_email="unassigned@company.com",
                status="active"
            )
            db.add(default_customer)
            db.flush()
            logger.info(f"Created default customer: {DEFAULT_CUSTOMER}")
        return default_customer
    except IntegrityError as e:
        logger.warning(f"Default customer already exists: {str(e)}")
        db.rollback()
        return db.query(Customer).filter(Customer.name == DEFAULT_CUSTOMER).first()
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

def validate_database_references(
    db: Session,
    entries: List[TimeEntryCreate]
) -> Tuple[List[TimeEntryCreate], List[Dict]]:
    """
    Validate database references in time entries.
    Returns tuple of (valid_entries, validation_errors)
    """
    processed_entries = []
    validation_errors = []

    # Get all unique customer names and project IDs
    customer_names = {normalize_customer_name(entry.customer) for entry in entries}
    project_ids = {normalize_project_id(entry.project) for entry in entries}

    # Query database for existing customers and projects
    existing_customers = {
        c.name: c for c in db.query(Customer).filter(Customer.name.in_(customer_names)).all()
    }
    existing_projects = {
        p.project_id: p for p in db.query(Project).filter(Project.project_id.in_(project_ids)).all()
    }

    logger.debug(f"Found {len(existing_customers)} existing customers and {len(existing_projects)} existing projects")

    # Ensure default entities exist
    default_customer = ensure_default_customer(db)
    if default_customer:
        existing_customers[DEFAULT_CUSTOMER] = default_customer

    default_project = ensure_default_project(db)
    if default_project:
        existing_projects[DEFAULT_PROJECT] = default_project

    try:
        db.commit()
    except Exception as e:
        logger.error(f"Error committing default entities: {str(e)}")
        db.rollback()

    for entry in entries:
        normalized_customer = normalize_customer_name(entry.customer)
        normalized_project = normalize_project_id(entry.project)
        original_customer = normalized_customer
        original_project = normalized_project

        # If customer doesn't exist, use default
        if normalized_customer not in existing_customers:
            validation_errors.append({
                'entry': entry.model_dump(),
                'error': f"Customer '{normalized_customer}' not found in database, using {DEFAULT_CUSTOMER}",
                'type': 'invalid_customer'
            })
            logger.warning(f"Customer '{normalized_customer}' not found, defaulting to {DEFAULT_CUSTOMER}")
            normalized_customer = DEFAULT_CUSTOMER
            normalized_project = DEFAULT_PROJECT  # Also default project when customer is invalid

        # If project doesn't exist or customer-project relationship is invalid, use defaults
        if normalized_project not in existing_projects:
            validation_errors.append({
                'entry': entry.model_dump(),
                'error': f"Project '{normalized_project}' not found in database, using {DEFAULT_PROJECT}",
                'type': 'invalid_project'
            })
            logger.warning(f"Project '{normalized_project}' not found, defaulting to {DEFAULT_PROJECT}")
            normalized_project = DEFAULT_PROJECT
            if normalized_customer != DEFAULT_CUSTOMER:
                normalized_customer = DEFAULT_CUSTOMER  # Also default customer when project is invalid
        elif normalized_project != DEFAULT_PROJECT and normalized_customer != DEFAULT_CUSTOMER:
            project = existing_projects[normalized_project]
            if project.customer != normalized_customer:
                validation_errors.append({
                    'entry': entry.model_dump(),
                    'error': f"Project '{original_project}' does not belong to customer '{original_customer}', using defaults",
                    'type': 'invalid_project_customer_relationship'
                })
                logger.warning(f"Invalid project-customer relationship: {original_project} - {original_customer}")
                normalized_customer = DEFAULT_CUSTOMER
                normalized_project = DEFAULT_PROJECT

        # Update entry with final values (original or default)
        entry.customer = normalized_customer
        entry.project = normalized_project
        processed_entries.append(entry)
        logger.debug(f"Processed entry: customer={normalized_customer}, project={normalized_project}")

    return processed_entries, validation_errors
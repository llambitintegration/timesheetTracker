"""Database validation utilities"""
from typing import List, Dict, Optional, Tuple, Union
from sqlalchemy.orm import Session
from models import Customer, Project
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
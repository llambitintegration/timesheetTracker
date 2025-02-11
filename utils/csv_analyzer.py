import pandas as pd
from typing import Dict, List, Optional
import logging
from datetime import datetime
from utils.utils import clean_numeric_value, clean_string_value, parse_date, validate_week_number, validate_month

logger = logging.getLogger(__name__)

DEFAULT_CUSTOMER = "Unassigned"
DEFAULT_PROJECT = "General"

def normalize_customer_name(name: str) -> str:
    """Normalize customer name"""
    if not name or str(name).strip() in ['', '-', 'None', 'null', 'NA']:
        return DEFAULT_CUSTOMER
    return str(name).strip().title()

def normalize_project_id(project_id: str) -> str:
    """Normalize project ID"""
    if not project_id or str(project_id).strip() in ['', '-', 'None', 'null', 'NA']:
        return DEFAULT_PROJECT
    return str(project_id).strip()

def analyze_timesheet_csv(file_path: str) -> Dict:
    """
    Analyze the timesheet CSV file to extract unique customers and their projects.
    """
    try:
        # Read CSV file
        df = pd.read_csv(file_path)

        # Get unique customers (excluding empty or '-' values)
        customers = set(df['Customer'].apply(normalize_customer_name))
        customers.discard(DEFAULT_CUSTOMER)

        # Get unique projects per customer
        customer_projects = {}
        for customer in customers:
            projects = df[df['Customer'].apply(normalize_customer_name) == customer]['Project'].unique()
            customer_projects[customer] = [normalize_project_id(p) for p in projects if pd.notna(p) and p != '-']

        return {
            'unique_customers': sorted(list(customers)),
            'customer_projects': customer_projects,
            'total_time_entries': len(df)
        }

    except Exception as e:
        logger.error(f"Error analyzing CSV file: {str(e)}")
        raise

def parse_raw_csv(file) -> Optional[pd.DataFrame]:
    """Parse raw CSV file into DataFrame without validation."""
    try:
        logger.info("Starting raw CSV parsing")
        df = pd.read_csv(
            file,
            keep_default_na=False,
            encoding='utf-8',
            skip_blank_lines=True,
            na_values=['#N/A', '-', ''],
            na_filter=True,
            on_bad_lines='skip'
        )
        # Remove any completely empty rows
        df = df.dropna(how='all')
        # Fill NA values with appropriate defaults
        df = df.fillna({
            'Customer': 'Unassigned',
            'Project': 'Unassigned',
            'Task Description': ''
        })
        logger.debug(f"Successfully read CSV with {len(df.columns)} columns")
        return df
    except UnicodeDecodeError:
        try:
            logger.warning("UTF-8 encoding failed, attempting with ISO-8859-1")
            df = pd.read_csv(file, keep_default_na=False, encoding='ISO-8859-1')
            logger.debug(f"Successfully read CSV with ISO-8859-1 encoding")
            return df
        except Exception as e:
            logger.error(f"Failed to parse CSV with ISO-8859-1 encoding: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Failed to parse CSV: {str(e)}")
        return None

def get_time_entries(file_path: str) -> List[Dict]:
    """
    Convert CSV rows to time entry dictionaries.
    """
    try:
        df = pd.read_csv(file_path)

        entries = []
        for _, row in df.iterrows():
            if pd.notna(row.get('Hours')) and float(row['Hours']) > 0:
                entry = {
                    'date': parse_date(row['Date']),
                    'customer': normalize_customer_name(row.get('Customer')),
                    'project': normalize_project_id(row.get('Project')),
                    'category': clean_string_value(row.get('Category'), "Other"),
                    'subcategory': clean_string_value(row.get('Subcategory'), "General"),
                    'task_description': clean_string_value(row.get('Task Description')),
                    'hours': clean_numeric_value(row['Hours']),
                    'week_number': validate_week_number(row.get('Week Number')),
                    'month': validate_month(row.get('Month'))
                }
                entries.append(entry)

        return entries

    except Exception as e:
        logger.error(f"Error processing time entries from CSV: {str(e)}")
        raise
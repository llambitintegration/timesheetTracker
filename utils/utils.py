import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import calendar
from utils.logger import Logger

logger = Logger().get_logger()

def clean_numeric_value(value, default=0):
    """Clean and validate numeric values."""
    if pd.isna(value) or value == '':
        return default
    try:
        return float(value) if isinstance(value, (int, float, str)) else default
    except (ValueError, TypeError):
        return default

def clean_string_value(value, field_type=None):
    """Clean and standardize string values"""
    if pd.isna(value) or value is None or str(value).strip() in ['', '-', 'None', 'null', 'NA']:
        return ""
    value = str(value).strip()
    if field_type == "category":
        return value.title()
    return value

def parse_date(date_value) -> datetime.date:
    """Parse and validate date values."""
    if pd.isna(date_value) or date_value == '':
        return datetime.now().date()
    try:
        if isinstance(date_value, datetime):
            return date_value.date()
        elif isinstance(date_value, str):
            for fmt in ['%m/%d/%y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(date_value, fmt).date()
                except ValueError:
                    continue
            return pd.to_datetime(date_value).date()
        raise ValueError(f"Could not parse date: {date_value}")
    except Exception as e:
        logger.warning(f"Error parsing date '{date_value}': {str(e)}")
        return datetime.now().date()

def validate_week_number(week_number):
    """Validate week number is between 1 and 53."""
    try:
        week = int(week_number)
        if 1 <= week <= 53:
            return week
    except (ValueError, TypeError):
        pass
    current_week = datetime.now().isocalendar()[1]
    return current_week

def validate_month(month):
    """Validate month name."""
    if pd.isna(month) or month == '':
        return calendar.month_name[datetime.now().month]

    try:
        month_str = str(month).strip().capitalize()
        if month_str in calendar.month_name:
            return month_str
    except (ValueError, TypeError):
        pass
    return calendar.month_name[datetime.now().month]

def parse_raw_csv(file) -> Optional[pd.DataFrame]:
    """Parse raw CSV file into DataFrame without validation."""
    try:
        logger.info("Starting raw CSV parsing")
        df = pd.read_csv(file, keep_default_na=False, encoding='utf-8')
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

def validate_csv_structure(df: pd.DataFrame) -> bool:
    """Validate CSV structure and required columns."""
    required_columns = ['Week Number', 'Hours', 'Customer', 'Project', 'Date']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        error_msg = f"Missing required columns: {', '.join(missing_columns)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    return True

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the DataFrame before processing."""
    logger.debug("Starting DataFrame cleaning")
    df = df.dropna(how='all')  # Drop rows that are all NA
    df = df.reset_index(drop=True)
    logger.debug(f"Cleaned DataFrame has {len(df)} rows")
    return df

# Added import for schemas -  assuming a schemas module exists.  Adjust as needed.
import schemas # Placeholder - Replace with actual import path

DEFAULT_CUSTOMER = "Default Customer" # Added default values
DEFAULT_PROJECT = "Default Project"

def parse_csv(file) -> List:
    """Parse CSV file with enhanced validation and normalization."""
    logger.info("Starting CSV parsing process")

    df = parse_raw_csv(file)
    if df is None:
        logger.error("Failed to parse CSV file")
        return []

    try:
        validate_csv_structure(df)
    except ValueError as e:
        logger.error(f"CSV structure validation failed: {str(e)}")
        raise

    df = clean_dataframe(df)

    if df.empty:
        logger.warning("No valid entries found in CSV file")
        return []

    entries = []
    logger.info(f"Processing {len(df)} rows from CSV file")

    for index, row in df.iterrows():
        try:
            # Validate hours first as it's critical
            hours = clean_numeric_value(row.get('Hours', 0))
            if hours <= 0 or hours > 24:
                logger.warning(f"Skipping row {index + 1} due to invalid hours: {hours}")
                continue

            # Process customer and project with proper field type handling
            raw_customer = str(row.get('Customer', '')).strip()
            raw_project = str(row.get('Project', '')).strip()

            # Check for various validation issues
            has_validation_issues = (
                'Project' in raw_customer or  # Customer name contains 'Project'
                'NonExistent' in raw_project or  # Project contains 'NonExistent'
                raw_customer in ['', '-', 'None', 'null', 'NA'] or  # Invalid customer
                raw_project in ['', '-', 'None', 'null', 'NA'] or  # Invalid project
                raw_customer == DEFAULT_CUSTOMER or  # Already default customer
                raw_project == DEFAULT_PROJECT  # Already default project
            )

            if has_validation_issues:
                logger.debug(f"Validation issues detected in row {index + 1}, using defaults")
                customer = DEFAULT_CUSTOMER
                project = DEFAULT_PROJECT
            else:
                customer = clean_string_value(raw_customer)
                project = clean_string_value(raw_project)

            logger.debug(f"Processed row {index + 1} - customer: {customer}, project: {project}")

            entry = schemas.TimeEntryCreate(
                week_number=validate_week_number(row.get('Week Number')),
                month=validate_month(row.get('Month')),
                category=clean_string_value(row.get('Category'), "category"), # Added field_type
                subcategory=clean_string_value(row.get('Subcategory'), "category"), # Added field_type
                customer=customer,
                project=project,
                task_description=clean_string_value(row.get('Task Description')),
                hours=hours,
                date=parse_date(row.get('Date'))
            )
            entries.append(entry)
            logger.debug(f"Successfully processed row {index + 1}")

        except Exception as e:
            logger.error(f"Error processing row {index + 1}: {str(e)}")
            continue

    logger.info(f"Successfully processed {len(entries)} valid entries from CSV")
    return entries

def parse_excel(file) -> List:
    """Parse Excel file with enhanced date handling."""
    logger.info("Starting Excel parsing")
    logger.debug("Reading Excel file into pandas DataFrame")

    df = pd.read_excel(file, parse_dates=['Date'])
    df.to_csv('temp.csv', index=False)
    with open('temp.csv', 'r') as csv_file:
        return parse_csv(csv_file)
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
        return datetime.now().date()  # Correct returned value type
    try:
        if isinstance(date_value, datetime):
            return date_value.date()  # Correct usage of .date() method
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
    """Parse raw CSV file into DataFrame with enhanced delimiter and quote handling."""
    try:
        logger.info("Starting raw CSV parsing")
        # Try tab delimiter first with more robust error handling
        try:
            df = pd.read_csv(
                file,
                keep_default_na=False,
                encoding='utf-8',
                sep='\t',  # Use tab delimiter
                quoting=3,  # QUOTE_NONE - disable special handling of quote chars
                engine='python',  # Use python engine for better error handling
                on_bad_lines='warn'  # Warn about problematic lines instead of failing
            )
            if len(df.columns) > 1:  # Verify we got multiple columns
                logger.debug(f"Successfully read tab-delimited file with {len(df.columns)} columns")
                return df
            else:
                logger.warning("Tab delimiter resulted in single column, trying comma delimiter")
                raise ValueError("Single column result indicates incorrect delimiter")
        except Exception as tab_error:
            logger.warning(f"Failed to parse with tab delimiter: {str(tab_error)}")
            # Reset file pointer for next attempt
            file.seek(0)
            # Fallback to comma delimiter with quote handling
            df = pd.read_csv(
                file,
                keep_default_na=False,
                encoding='utf-8',
                quoting=1,  # QUOTE_MINIMAL - quote fields only when needed
                quotechar='"',
                engine='python',
                on_bad_lines='warn'
            )
            logger.debug(f"Successfully read CSV with comma delimiter")
            return df
    except Exception as e:
        logger.error(f"Failed to parse CSV: {str(e)}")
        return None

def validate_csv_structure(df: pd.DataFrame) -> bool:
    """Validate CSV structure and required columns."""
    required_columns = [
        'Date', 'Week Day', 'Week Number', 'Month', 'Category', 
        'Subcategory', 'Customer', 'Project', 'Task Description', 'Hours'
    ]
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

from database import schemas

DEFAULT_CUSTOMER = "Default Customer"
DEFAULT_PROJECT = "Default Project"

def parse_csv(file) -> List:
    """Parse CSV file with enhanced validation and normalization."""
    logger.info("Starting CSV parsing process")

    try:
        # First try reading with tab delimiter
        df = pd.read_csv(
            file,
            sep='\t',
            keep_default_na=False,
            encoding='utf-8',
            quoting=3,  # QUOTE_NONE
            engine='python'
        )

        # Verify required columns
        required_columns = [
            'Date', 'Week Day', 'Week Number', 'Month', 'Category', 
            'Subcategory', 'Customer', 'Project', 'Task Description', 'Hours'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            logger.error(f"Missing required columns: {', '.join(missing_columns)}")
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        df = clean_dataframe(df)

        if df.empty:
            logger.warning("No valid entries found in CSV file")
            return []

        entries = []
        logger.info(f"Processing {len(df)} rows from CSV file")

        for index, row in df.iterrows():
            try:
                # Process date field
                date_str = str(row.get('Date', ''))

                # Validate hours first as it's critical
                hours = clean_numeric_value(row.get('Hours', 0))
                if hours <= 0 or hours > 24:
                    logger.warning(f"Skipping row {index + 1} due to invalid hours: {hours}")
                    continue

                # Handle special cases for customer and project
                customer = clean_string_value(row.get('Customer', ''))
                project = clean_string_value(row.get('Project', ''))

                # Convert '-' to empty string for customer and project
                if customer == '-':
                    customer = ''
                if project == '-':
                    project = ''

                entry = schemas.TimeEntryCreate(
                    week_number=validate_week_number(row.get('Week Number')),
                    month=validate_month(row.get('Month')),
                    category=clean_string_value(row.get('Category'), "category"),
                    subcategory=clean_string_value(row.get('Subcategory'), "category"),
                    customer=customer or "Unassigned",  # Default to "Unassigned" if empty
                    project=project or "Unassigned",    # Default to "Unassigned" if empty
                    task_description=clean_string_value(row.get('Task Description')),
                    hours=hours,
                    date=parse_date(date_str)
                )
                entries.append(entry)
                logger.debug(f"Successfully processed row {index + 1}")

            except Exception as e:
                logger.error(f"Error processing row {index + 1}: {str(e)}")
                continue

        logger.info(f"Successfully processed {len(entries)} valid entries from CSV")
        return entries

    except Exception as e:
        logger.error(f"Failed to parse CSV: {str(e)}")
        raise ValueError(f"Failed to parse file: {str(e)}")

def parse_excel(file) -> List:
    """Parse Excel file with enhanced date handling."""
    logger.info("Starting Excel parsing")
    logger.debug("Reading Excel file into pandas DataFrame")

    df = pd.read_excel(file, parse_dates=['Date'])
    df.to_csv('temp.csv', index=False)
    with open('temp.csv', 'r') as csv_file:
        return parse_csv(csv_file)
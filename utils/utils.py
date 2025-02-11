import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import calendar
from utils.logger import Logger

logger = Logger().get_logger()

def clean_numeric_value(value, default=0):
    """Clean and validate numeric values."""
    if pd.isna(value) or value == '' or value is None:
        return default
    try:
        cleaned = float(str(value).replace(',', '').strip())
        return cleaned if 0 <= cleaned <= 24 else default
    except (ValueError, TypeError, AttributeError):
        return default

def clean_string_value(value, field_type=None):
    """Clean and standardize string values"""
    if pd.isna(value) or value is None or str(value).strip() in ['', '-', 'None', 'null', 'NA']:
        return ""
    cleaned = str(value).strip()
    return cleaned.title() if field_type == "category" else cleaned

def parse_date(date_value) -> date:
    """Parse and validate date values."""
    if pd.isna(date_value) or date_value == '' or date_value is None:
        return datetime.now().date()

    try:
        if isinstance(date_value, datetime):
            return date_value.date()
        elif isinstance(date_value, date):
            return date_value
        elif isinstance(date_value, str):
            date_str = date_value.strip()
            for fmt in ['%m/%d/%y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return pd.to_datetime(date_str).date()
        raise ValueError(f"Could not parse date: {date_value}")
    except Exception as e:
        logger.warning(f"Error parsing date '{date_value}': {str(e)}")
        return datetime.now().date()

def validate_week_number(week_number) -> int:
    """Validate week number is between 1 and 53."""
    try:
        week = int(float(str(week_number).strip()))
        return week if 1 <= week <= 53 else datetime.now().isocalendar()[1]
    except (ValueError, TypeError, AttributeError):
        return datetime.now().isocalendar()[1]

def validate_month(month) -> str:
    """Validate month name."""
    if pd.isna(month) or not month:
        return calendar.month_name[datetime.now().month]

    try:
        month_str = str(month).strip().title()
        if month_str in calendar.month_name:
            return month_str
        # Try converting month number to name
        month_num = int(month_str)
        if 1 <= month_num <= 12:
            return calendar.month_name[month_num]
    except (ValueError, TypeError, AttributeError):
        pass
    return calendar.month_name[datetime.now().month]

def parse_raw_csv(file) -> Optional[pd.DataFrame]:
    """Parse raw CSV file into DataFrame with enhanced error handling."""
    encodings = ['utf-8', 'iso-8859-1', 'cp1252']

    for encoding in encodings:
        try:
            file.seek(0)
            df = pd.read_csv(
                file,
                keep_default_na=False,
                encoding=encoding,
                sep='\t',
                quoting=3,
                engine='python',
                on_bad_lines='warn'
            )
            if len(df.columns) > 1:
                logger.debug(f"Successfully read file with {encoding} encoding")
                return df

            # Try comma delimiter
            file.seek(0)
            df = pd.read_csv(
                file,
                keep_default_na=False,
                encoding=encoding,
                quoting=1,
                engine='python',
                on_bad_lines='warn'
            )
            if len(df.columns) > 1:
                logger.debug(f"Successfully read CSV with comma delimiter")
                return df
        except Exception as e:
            logger.warning(f"Failed with {encoding} encoding: {str(e)}")
            continue

    logger.error("Failed to parse CSV with all attempted encodings")
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
    df = df.dropna(how='all')
    df = df.reset_index(drop=True)
    logger.debug(f"Cleaned DataFrame has {len(df)} rows")
    return df

def parse_csv(file) -> List:
    """Parse CSV file with enhanced validation."""
    logger.info("Starting CSV parsing process")

    try:
        df = parse_raw_csv(file)
        if df is None:
            raise ValueError("Failed to parse CSV file")

        validate_csv_structure(df)
        df = clean_dataframe(df)

        if df.empty:
            logger.warning("No valid entries found in CSV file")
            return []

        from database import schemas
        entries = []
        logger.info(f"Processing {len(df)} rows from CSV file")

        for index, row in df.iterrows():
            try:
                hours = clean_numeric_value(row.get('Hours', 0))
                if hours <= 0 or hours > 24:
                    logger.warning(f"Skipping row {index + 1} due to invalid hours: {hours}")
                    continue

                customer = clean_string_value(row.get('Customer', ''))
                project = clean_string_value(row.get('Project', ''))

                entry = schemas.TimeEntryCreate(
                    date=parse_date(row.get('Date')),
                    week_number=validate_week_number(row.get('Week Number')),
                    month=validate_month(row.get('Month')),
                    category=clean_string_value(row.get('Category'), "category"),
                    subcategory=clean_string_value(row.get('Subcategory'), "category"),
                    customer=customer or "Unassigned",
                    project=project or "Unassigned",
                    task_description=clean_string_value(row.get('Task Description')),
                    hours=hours
                )
                entries.append(entry)
                logger.debug(f"Successfully processed row {index + 1}")

            except Exception as e:
                logger.error(f"Error processing row {index + 1}: {str(e)}")
                continue

        logger.info(f"Successfully processed {len(entries)} valid entries")
        return entries

    except Exception as e:
        logger.error(f"Failed to parse CSV: {str(e)}")
        raise ValueError(f"Failed to parse file: {str(e)}")

def parse_excel(file) -> List:
    """Parse Excel file."""
    logger.info("Starting Excel parsing")
    df = pd.read_excel(file, parse_dates=['Date'])
    df.to_csv('temp.csv', index=False)
    with open('temp.csv', 'r') as csv_file:
        return parse_csv(csv_file)
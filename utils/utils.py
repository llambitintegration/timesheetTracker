import pandas as pd
from typing import List
from database import schemas
from datetime import datetime
from utils.logger import Logger
import calendar

logger = Logger().get_logger()

def clean_numeric_value(value, default=0):
    """Clean and validate numeric values."""
    if pd.isna(value) or value == '':
        return default
    try:
        return float(value) if isinstance(value, (int, float, str)) else default
    except (ValueError, TypeError):
        return default

def clean_string_value(value, default=""):
    """Clean and validate string values."""
    if pd.isna(value) or value == '':
        return default
    return str(value).strip()

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

def parse_csv(file) -> List[schemas.TimeEntryCreate]:
    """Parse CSV file with enhanced data cleaning and validation."""
    logger.info("Starting CSV parsing")
    logger.debug("Reading CSV file into pandas DataFrame")

    # Read the file content and create DataFrame
    df = pd.read_csv(file, keep_default_na=False)
    df = df.dropna(how='all')  # Remove rows that are all empty
    df = df.reset_index(drop=True)

    if df.empty:
        logger.error("Empty CSV file received")
        raise ValueError("Empty CSV file")

    entries = []
    logger.info(f"Processing {len(df)} rows from CSV file")

    required_columns = ['Week Number', 'Hours', 'Customer', 'Project']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

    for index, row in df.iterrows():
        logger.debug(f"Processing row {index + 1}/{len(df)}")

        try:
            # Clean and validate data
            hours = clean_numeric_value(row.get('Hours', 0))
            week_number = validate_week_number(row.get('Week Number'))
            month = validate_month(row.get('Month'))
            customer = row.get('Customer', '').strip()
            
            if hours <= 0:
                logger.warning(f"Skipping row {index + 1} due to invalid hours: {hours}")
                continue
                
            # Replace empty or dash customer with None
            if not customer or customer == '-':
                customer = None

            entry = schemas.TimeEntryCreate(
                week_number=week_number,
                month=month,
                category=clean_string_value(row.get('Category'), "Other"),
                subcategory=clean_string_value(row.get('Subcategory'), "General"),
                customer=clean_string_value(row.get('Customer')),
                project=clean_string_value(row.get('Project')),
                task_description=clean_string_value(row.get('Task Description')),
                hours=hours
            )
            entries.append(entry)
            logger.debug(f"Successfully processed row {index + 1}")
        except Exception as e:
            logger.error(f"Error processing row {index + 1}: {str(e)}")
            continue

    if not entries:
        raise ValueError("No valid entries found after processing")

    logger.info(f"Successfully created {len(entries)} time entries from CSV")
    logger.debug(f"Total hours recorded: {sum(entry.hours for entry in entries)}")
    return entries

def parse_excel(file) -> List[schemas.TimeEntryCreate]:
    """Parse Excel file using the same validation as CSV."""
    logger.info("Starting Excel parsing")
    logger.debug("Reading Excel file into pandas DataFrame")
    df = pd.read_excel(file)

    # Convert Excel to CSV format and use the same parsing logic
    df.to_csv('temp.csv', index=False)
    with open('temp.csv', 'r') as csv_file:
        return parse_csv(csv_file)
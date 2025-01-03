
import pandas as pd
from typing import List
from database import schemas
from datetime import datetime
from utils.logger import Logger
import csv

logger = Logger().get_logger()

def parse_csv(file) -> List[schemas.TimeEntryCreate]:
    logger.info("Starting CSV parsing")
    logger.debug("Reading CSV file into pandas DataFrame")
    
    # Read the file content and create DataFrame, dropping empty rows
    df = pd.read_csv(file, keep_default_na=False)
    df = df.dropna(how='all')  # Remove rows that are all empty
    df = df.reset_index(drop=True)  # Reset index after dropping rows
    
    if df.empty:
        logger.error("Empty CSV file received")
        raise ValueError("Empty CSV file")
        
    entries = []
    logger.info(f"Processing {len(df)} rows from CSV file")

    for index, row in df.iterrows():
        logger.debug(f"Processing row {index + 1}/{len(df)}")
        
        # Skip empty rows
        if pd.isna(row['Week Number']) or pd.isna(row['Hours']):
            logger.warning(f"Skipping row {index + 1} due to missing required fields")
            continue

        try:
            logger.debug(f"Creating TimeEntryCreate object for row {index + 1}")
            # Handle empty or invalid hours values
            try:
                hours = float(row['Hours']) if row['Hours'] != '' else 0.0
            except (ValueError, TypeError):
                logger.warning(f"Invalid hours value in row {index + 1}, setting to 0")
                hours = 0.0

            # Handle empty or invalid week numbers
            try:
                week_number = int(row['Week Number']) if row['Week Number'] != '' else 0
            except (ValueError, TypeError):
                logger.warning(f"Invalid week number in row {index + 1}, setting to 0")
                week_number = 0
                
            entry = schemas.TimeEntryCreate(
                week_number=week_number,
                month=str(row['Month']),
                category=str(row['Category']) if not pd.isna(row['Category']) else "Other",
                subcategory=str(row['Subcategory']) if not pd.isna(row['Subcategory']) else "General",
                customer=str(row['Customer']) if not pd.isna(row['Customer']) else None,
                project=str(row['Project']) if not pd.isna(row['Project']) else None,
                task_description=str(row['Task Description']) if not pd.isna(row['Task Description']) else None,
                hours=hours
            )
            entries.append(entry)
            logger.debug(f"Successfully processed row {index + 1}")
        except Exception as e:
            logger.error(f"Error processing row {index + 1}: {str(e)}")
            raise

    logger.info(f"Successfully created {len(entries)} time entries from CSV")
    logger.debug(f"Total hours recorded: {sum(entry.hours for entry in entries)}")
    return entries
    
    # Use pandas to read from the string buffer
    import io
    df = pd.read_csv(io.StringIO(content))
    
    if df.empty:
        logger.error("Empty CSV file received")
        raise ValueError("Empty CSV file")
        
    entries = []
    logger.info(f"Processing {len(df)} rows from CSV file")

    for index, row in df.iterrows():
        logger.debug(f"Processing row {index + 1}/{len(df)}")
        
        # Skip empty rows
        if pd.isna(row['Week Number']) or pd.isna(row['Hours']):
            logger.warning(f"Skipping row {index + 1} due to missing required fields")
            continue

        try:
            logger.debug(f"Creating TimeEntryCreate object for row {index + 1}")
            # Handle empty or invalid hours values
            try:
                hours = float(row['Hours']) if row['Hours'] != '' else 0.0
            except (ValueError, TypeError):
                logger.warning(f"Invalid hours value in row {index + 1}, setting to 0")
                hours = 0.0

            # Handle empty or invalid week numbers
            try:
                week_number = int(row['Week Number']) if row['Week Number'] != '' else 0
            except (ValueError, TypeError):
                logger.warning(f"Invalid week number in row {index + 1}, setting to 0")
                week_number = 0
                
            entry = schemas.TimeEntryCreate(
                week_number=week_number,
                month=str(row['Month']),
                category=str(row['Category']) if not pd.isna(row['Category']) else "Other",
                subcategory=str(row['Subcategory']) if not pd.isna(row['Subcategory']) else "General",
                customer=str(row['Customer']) if not pd.isna(row['Customer']) else None,
                project=str(row['Project']) if not pd.isna(row['Project']) else None,
                task_description=str(row['Task Description']) if not pd.isna(row['Task Description']) else None,
                hours=hours
            )
            entries.append(entry)
            logger.debug(f"Successfully processed row {index + 1}")
        except Exception as e:
            logger.error(f"Error processing row {index + 1}: {str(e)}")
            raise

    logger.info(f"Successfully created {len(entries)} time entries from CSV")
    logger.debug(f"Total hours recorded: {sum(entry.hours for entry in entries)}")
    return entries

def parse_excel(file) -> List[schemas.TimeEntryCreate]:
    logger.info("Starting Excel parsing")
    logger.debug("Reading Excel file into pandas DataFrame")
    df = pd.read_excel(file.file)
    
    entries = []
    logger.info(f"Processing {len(df)} rows from Excel file")

    for index, row in df.iterrows():
        logger.debug(f"Processing row {index + 1}/{len(df)}")
        
        # Skip empty rows
        if pd.isna(row['Week Number']) or pd.isna(row['Hours']):
            logger.warning(f"Skipping row {index + 1} due to missing required fields")
            continue

        try:
            logger.debug(f"Creating TimeEntryCreate object for row {index + 1}")
            # Handle empty or invalid hours values
            try:
                hours = float(row['Hours']) if row['Hours'] != '' else 0.0
            except (ValueError, TypeError):
                logger.warning(f"Invalid hours value in row {index + 1}, setting to 0")
                hours = 0.0

            # Handle empty or invalid week numbers
            try:
                week_number = int(row['Week Number']) if row['Week Number'] != '' else 0
            except (ValueError, TypeError):
                logger.warning(f"Invalid week number in row {index + 1}, setting to 0")
                week_number = 0
                
            entry = schemas.TimeEntryCreate(
                week_number=week_number,
                month=str(row['Month']),
                category=str(row['Category']) if not pd.isna(row['Category']) else "Other",
                subcategory=str(row['Subcategory']) if not pd.isna(row['Subcategory']) else "General",
                customer=str(row['Customer']) if not pd.isna(row['Customer']) else None,
                project=str(row['Project']) if not pd.isna(row['Project']) else None,
                task_description=str(row['Task Description']) if not pd.isna(row['Task Description']) else None,
                hours=hours
            )
            entries.append(entry)
            logger.debug(f"Successfully processed row {index + 1}")
        except Exception as e:
            logger.error(f"Error processing row {index + 1}: {str(e)}")
            raise

    logger.info(f"Successfully created {len(entries)} time entries from Excel")
    logger.debug(f"Total hours recorded: {sum(entry.hours for entry in entries)}")
    return entries

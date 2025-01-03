
import pandas as pd
from typing import List
from database import schemas
from datetime import datetime
from utils.logger import Logger

logger = Logger().get_logger()

def parse_csv(file) -> List[schemas.TimeEntryCreate]:
    logger.info(f"Starting CSV parsing for file: {file.filename}")
    logger.debug("Reading CSV file into pandas DataFrame")
    df = pd.read_csv(file)
    
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
            entry = schemas.TimeEntryCreate(
                week_number=int(row['Week Number']),
                month=str(row['Month']),
                category=str(row['Category']) if not pd.isna(row['Category']) else "Other",
                subcategory=str(row['Subcategory']) if not pd.isna(row['Subcategory']) else "General",
                customer=str(row['Customer']) if not pd.isna(row['Customer']) else None,
                project=str(row['Project']) if not pd.isna(row['Project']) else None,
                task_description=str(row['Task Description']) if not pd.isna(row['Task Description']) else None,
                hours=float(row['Hours'])
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
    logger.info(f"Starting Excel parsing for file: {file.filename}")
    logger.debug("Reading Excel file into pandas DataFrame")
    df = pd.read_excel(file)
    
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
            entry = schemas.TimeEntryCreate(
                week_number=int(row['Week Number']),
                month=str(row['Month']),
                category=str(row['Category']) if not pd.isna(row['Category']) else "Other",
                subcategory=str(row['Subcategory']) if not pd.isna(row['Subcategory']) else "General",
                customer=str(row['Customer']) if not pd.isna(row['Customer']) else None,
                project=str(row['Project']) if not pd.isna(row['Project']) else None,
                task_description=str(row['Task Description']) if not pd.isna(row['Task Description']) else None,
                hours=float(row['Hours'])
            )
            entries.append(entry)
            logger.debug(f"Successfully processed row {index + 1}")
        except Exception as e:
            logger.error(f"Error processing row {index + 1}: {str(e)}")
            raise

    logger.info(f"Successfully created {len(entries)} time entries from Excel")
    logger.debug(f"Total hours recorded: {sum(entry.hours for entry in entries)}")
    return entries

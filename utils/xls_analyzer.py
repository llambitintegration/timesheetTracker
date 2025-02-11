from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
from io import BytesIO
from utils.logger import Logger
from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT

logger = Logger().get_logger()

class XLSAnalyzer:
    REQUIRED_COLUMNS = {
        'Week Number', 'Month', 'Category', 'Subcategory',
        'Customer', 'Project', 'Task Description', 'Hours', 'Date'
    }

    @staticmethod
    def read_excel(file_contents: bytes) -> List[Dict[str, Any]]:
        """Read Excel file and return list of dictionaries with data."""
        try:
            logger.debug("Starting Excel file analysis")

            # Read Excel file
            df = pd.read_excel(
                BytesIO(file_contents),
                sheet_name=0
            )

            # Verify all required columns exist
            missing_columns = XLSAnalyzer.REQUIRED_COLUMNS - set(df.columns)
            if missing_columns:
                # Add missing columns with default values
                for col in missing_columns:
                    if col == 'Week Number':
                        df[col] = 0
                    elif col == 'Hours':
                        df[col] = 0.0
                    elif col == 'Customer' or col == 'Project':
                        df[col] = '-'
                    else:
                        df[col] = ''

            # Drop rows where all elements are NaN
            df = df.dropna(how='all')

            # Fill missing values with appropriate defaults
            df = df.fillna({
                'Week Number': 0,
                'Month': '',
                'Category': 'Other',
                'Subcategory': 'General',
                'Customer': '-',
                'Project': '-',
                'Task Description': '',
                'Hours': 0.0
            })

            # Convert date column to datetime
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

            # Convert Week Number to integer
            df['Week Number'] = pd.to_numeric(df['Week Number'], errors='coerce').fillna(0).astype('Int64')

            # Convert to records
            records = []
            for _, row in df.iterrows():
                record = {
                    'Week Number': int(row['Week Number']),
                    'Month': str(row['Month']),
                    'Category': str(row['Category']),
                    'Subcategory': str(row['Subcategory']),
                    'Customer': DEFAULT_CUSTOMER if row['Customer'] in ['-', '', None] else str(row['Customer']),
                    'Project': DEFAULT_PROJECT if row['Project'] in ['-', '', None] else str(row['Project']),
                    'Task Description': str(row['Task Description']),
                    'Hours': float(row['Hours']),
                    'Date': row['Date'].strftime('%Y-%m-%d') if pd.notnull(row['Date']) else None
                }
                if record['Date'] is not None:  # Only include records with valid dates
                    records.append(record)

            logger.info(f"Successfully parsed {len(records)} records from Excel file")
            return records

        except Exception as e:
            logger.error(f"Error parsing Excel file: {str(e)}")
            raise ValueError(f"Failed to parse Excel file: {str(e)}")
from typing import List, Dict, Any, Tuple
import pandas as pd
from datetime import datetime
from io import BytesIO
from utils.logger import Logger
from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT
from tqdm import tqdm

logger = Logger().get_logger()

class XLSAnalyzer:
    REQUIRED_COLUMNS = {
        'Week Number', 'Month', 'Category', 'Subcategory',
        'Customer', 'Project', 'Task Description', 'Hours', 'Date'
    }

    @staticmethod
    def read_excel(file_contents: bytes, chunk_size: int = 1000) -> Tuple[List[Dict[str, Any]], int]:
        """Read Excel file and return list of dictionaries with data and total rows."""
        try:
            logger.debug("Starting Excel file analysis")

            # Read Excel file efficiently
            df = pd.read_excel(
                BytesIO(file_contents),
                sheet_name=0,
                dtype={
                    'Week Number': 'Int64',
                    'Month': 'str',
                    'Category': 'str',
                    'Subcategory': 'str',
                    'Customer': 'str',
                    'Project': 'str',
                    'Task Description': 'str',
                    'Hours': 'float64',
                    'Date': 'datetime64[ns]'
                }
            )

            total_rows = len(df)
            logger.info(f"Found {total_rows} rows in Excel file")

            # Verify all required columns exist
            missing_columns = XLSAnalyzer.REQUIRED_COLUMNS - set(df.columns)
            if missing_columns:
                for col in missing_columns:
                    if col == 'Week Number':
                        df[col] = 0
                    elif col == 'Hours':
                        df[col] = 0.0
                    elif col == 'Customer' or col == 'Project':
                        df[col] = '-'
                    else:
                        df[col] = ''

            # Process data efficiently
            df = df.dropna(how='all')

            # Fill missing values vectorized
            default_values = {
                'Week Number': 0,
                'Month': '',
                'Category': 'Other',
                'Subcategory': 'General',
                'Customer': '-',
                'Project': '-',
                'Task Description': '',
                'Hours': 0.0
            }
            df = df.fillna(default_values)

            # Convert date column to datetime efficiently
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

            # Process only valid dates
            df = df.dropna(subset=['Date'])

            # Vectorized operations for data cleaning
            df['Customer'] = df['Customer'].apply(
                lambda x: DEFAULT_CUSTOMER if str(x).strip() in ['-', '', 'nan', 'None'] else str(x)
            )
            df['Project'] = df['Project'].apply(
                lambda x: DEFAULT_PROJECT if str(x).strip() in ['-', '', 'nan', 'None'] else str(x)
            )

            # Convert to records efficiently
            records = []
            for chunk_start in range(0, len(df), chunk_size):
                chunk = df.iloc[chunk_start:chunk_start + chunk_size]
                chunk_records = chunk.to_dict('records')

                for record in chunk_records:
                    processed_record = {
                        'Week Number': int(record['Week Number']),
                        'Month': str(record['Month']),
                        'Category': str(record['Category']),
                        'Subcategory': str(record['Subcategory']),
                        'Customer': record['Customer'],
                        'Project': record['Project'],
                        'Task Description': str(record['Task Description']),
                        'Hours': float(record['Hours']),
                        'Date': record['Date'].strftime('%Y-%m-%d')
                    }
                    records.append(processed_record)

            logger.info(f"Successfully processed {len(records)} records from Excel file")
            return records, total_rows

        except Exception as e:
            logger.error(f"Error parsing Excel file: {str(e)}")
            raise ValueError(f"Failed to parse Excel file: {str(e)}")
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
from io import BytesIO
from utils.logger import Logger
from tqdm import tqdm

logger = Logger().get_logger()

class XLSAnalyzer:
    REQUIRED_COLUMNS = {
        'Week Number', 'Month', 'Category', 'Subcategory',
        'Customer', 'Project', 'Task Description', 'Hours', 'Date'
    }

    @staticmethod
    def clean_string_column(series: pd.Series) -> pd.Series:
        """Clean string columns efficiently using vectorized operations."""
        return series.fillna(None).astype(str).apply(
            lambda x: None if x.strip() in ['-', '', 'nan', 'None', 'null'] else x.strip()
        )

    @staticmethod
    def read_excel(file_contents: bytes, chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """Read Excel file and return list of dictionaries with data."""
        try:
            logger.debug("Starting Excel file analysis")

            if not file_contents:
                raise ValueError("Empty file contents provided")

            # Read Excel file efficiently with specified data types
            df = pd.read_excel(
                BytesIO(file_contents),
                sheet_name=0,
                dtype={
                    'Week Number': 'object',  # Changed from Int64 to handle invalid data
                    'Month': 'str',
                    'Category': 'str',
                    'Subcategory': 'str',
                    'Customer': 'str',
                    'Project': 'str',
                    'Task Description': 'str',
                    'Hours': 'object',  # Changed from float64 to handle invalid data
                    'Date': 'datetime64[ns]'
                },
                na_values=['', '-', 'NA', 'N/A', '#N/A'],
                keep_default_na=True
            )

            # Verify all required columns exist
            missing_columns = XLSAnalyzer.REQUIRED_COLUMNS - set(df.columns)
            if missing_columns:
                for col in missing_columns:
                    if col == 'Week Number':
                        df[col] = 0
                    elif col == 'Hours':
                        df[col] = 0.0
                    else:
                        df[col] = None

            # Drop completely empty rows
            df = df.dropna(how='all')

            # Clean string columns using vectorized operations
            string_columns = ['Month', 'Category', 'Subcategory', 'Customer', 'Project', 'Task Description']
            for col in string_columns:
                df[col] = XLSAnalyzer.clean_string_column(df[col])

            # Handle numeric columns with more robust error handling
            df['Week Number'] = pd.to_numeric(df['Week Number'], errors='coerce').fillna(0).astype(int)
            df['Hours'] = pd.to_numeric(df['Hours'], errors='coerce').fillna(0.0).astype(float)

            # Convert date column to datetime efficiently
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

            # Drop rows with invalid dates
            df = df.dropna(subset=['Date'])

            # Process records in chunks efficiently
            records = []
            for chunk_start in range(0, len(df), chunk_size):
                chunk = df.iloc[chunk_start:chunk_start + chunk_size]
                chunk_records = chunk.to_dict('records')

                for record in chunk_records:
                    processed_record = {
                        'Week Number': int(record['Week Number']),
                        'Month': str(record['Month'] if pd.notna(record['Month']) else ''),
                        'Category': str(record['Category'] or 'Other'),
                        'Subcategory': str(record['Subcategory'] or 'General'),
                        'Customer': record['Customer'] if pd.notna(record['Customer']) else None,
                        'Project': record['Project'] if pd.notna(record['Project']) else None,
                        'Task Description': str(record['Task Description'] or ''),
                        'Hours': float(record['Hours']),
                        'Date': record['Date'].strftime('%Y-%m-%d')
                    }
                    records.append(processed_record)

                logger.debug(f"Processed chunk {chunk_start//chunk_size + 1}, records: {len(records)}")

            logger.info(f"Successfully processed {len(records)} records from Excel file")
            return records

        except Exception as e:
            logger.error(f"Error parsing Excel file: {str(e)}")
            raise ValueError(f"Failed to parse Excel file: {str(e)}")
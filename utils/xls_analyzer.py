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
        try:
            # Convert NaN to empty string first, then process
            str_series = series.fillna('')
            # Convert to string and clean
            cleaned = str_series.astype(str).apply(
                lambda x: None if x.strip() in ['-', '', 'nan', 'None', 'null'] else x.strip()
            )
            return cleaned
        except Exception as e:
            logger.error(f"Error cleaning string column: {str(e)}")
            return series

    @staticmethod
    def read_excel(file_contents: bytes, chunk_size: int = 1000) -> List[Dict[str, Any]]:
        """Read Excel file and return list of dictionaries with data."""
        try:
            logger.debug("Starting Excel file analysis")

            if not file_contents:
                raise ValueError("Empty file contents provided")

            # Read Excel file with explicit data types
            df = pd.read_excel(
                BytesIO(file_contents),
                sheet_name=0,
                dtype={
                    'Week Number': 'object',
                    'Month': 'str',
                    'Category': 'str',
                    'Subcategory': 'str',
                    'Customer': 'str',
                    'Project': 'str',
                    'Task Description': 'str',
                    'Hours': 'float',
                    'Date': 'datetime64[ns]'
                },
                na_values=['', '-', 'NA', 'N/A', '#N/A'],
                keep_default_na=True
            )

            # Handle missing columns with defaults
            missing_columns = XLSAnalyzer.REQUIRED_COLUMNS - set(df.columns)
            for col in missing_columns:
                if col == 'Week Number':
                    df[col] = 0
                elif col == 'Hours':
                    df[col] = 0.0
                else:
                    df[col] = ''

            # Drop empty rows
            df = df.dropna(how='all')

            # Clean string columns
            string_columns = ['Month', 'Category', 'Subcategory', 'Customer', 'Project', 'Task Description']
            for col in string_columns:
                if col in df.columns:
                    df[col] = XLSAnalyzer.clean_string_column(df[col])

            # Convert numeric columns safely
            try:
                df['Week Number'] = pd.to_numeric(df['Week Number'], errors='coerce').fillna(0).astype(int)
            except Exception:
                df['Week Number'] = 0

            try:
                df['Hours'] = pd.to_numeric(df['Hours'], errors='coerce').fillna(0.0).astype(float)
            except Exception:
                df['Hours'] = 0.0

            # Ensure date column is properly formatted
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.dropna(subset=['Date'])

            # Process records
            records = []
            for chunk_start in range(0, len(df), chunk_size):
                chunk = df.iloc[chunk_start:chunk_start + chunk_size]
                chunk_records = chunk.to_dict('records')

                for record in chunk_records:
                    processed_record = {
                        'Week Number': int(record['Week Number']),
                        'Month': str(record.get('Month', '')),
                        'Category': str(record.get('Category', 'Other')),
                        'Subcategory': str(record.get('Subcategory', 'General')),
                        'Customer': record.get('Customer') if pd.notna(record.get('Customer')) else None,
                        'Project': record.get('Project') if pd.notna(record.get('Project')) else None,
                        'Task Description': str(record.get('Task Description', '')),
                        'Hours': float(record['Hours']),
                        'Date': record['Date'].strftime('%Y-%m-%d')
                    }
                    records.append(processed_record)

            logger.info(f"Successfully processed {len(records)} records from Excel file")
            return records

        except Exception as e:
            logger.error(f"Error parsing Excel file: {str(e)}")
            raise ValueError(f"Failed to parse Excel file: {str(e)}")
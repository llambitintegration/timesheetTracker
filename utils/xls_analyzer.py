from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
from io import BytesIO
from utils.logger import Logger
from utils.validators import DEFAULT_CUSTOMER, DEFAULT_PROJECT

logger = Logger().get_logger()

class XLSAnalyzer:
    @staticmethod
    def read_excel(file_contents: bytes) -> List[Dict[str, Any]]:
        """Read Excel file and return list of dictionaries with data."""
        try:
            # Read first sheet from Excel file
            df = pd.read_excel(
                BytesIO(file_contents),
                sheet_name=0,
                dtype={
                    'Week Number': 'Int64',
                    'Month': str,
                    'Category': str,
                    'Subcategory': str,
                    'Customer': str,
                    'Project': str,
                    'Task Description': str
                }
            )

            # Drop rows where all elements are NaN
            df = df.dropna(how='all')

            # Convert date column to datetime
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

            # Fill NaN values with appropriate defaults
            # Convert Week Number to numeric, replacing non-numeric with 0
            df['Week Number'] = pd.to_numeric(df['Week Number'], errors='coerce').fillna(0).astype('Int64')

            # Replace NaN and dash values with None for customer and project
            df['Customer'] = df['Customer'].replace({'-': None, 'nan': None}).fillna(None)
            df['Project'] = df['Project'].replace({'-': None, 'nan': None}).fillna(None)

            # Fill missing values appropriately
            df['Task Description'] = df['Task Description'].fillna('')
            df['Month'] = df['Month'].fillna('')
            df['Category'] = df['Category'].fillna('Other')
            df['Subcategory'] = df['Subcategory'].fillna('Other')
            df['Hours'] = df['Hours'].fillna(0.0)

            # Convert DataFrame to list of dictionaries
            records = df.to_dict('records')

            logger.info(f"Successfully parsed {len(records)} records from Excel file")
            return records

        except Exception as e:
            logger.error(f"Error parsing Excel file: {str(e)}")
            raise ValueError(f"Failed to parse Excel file: {str(e)}")
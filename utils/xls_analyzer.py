
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime
from io import BytesIO
from utils.logger import Logger

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
            
            # Set default values for missing columns
            required_columns = ['Week Number', 'Month', 'Category', 'Subcategory', 
                              'Customer', 'Project', 'Task Description', 'Date']
            for col in required_columns:
                if col not in df.columns:
                    if col == 'Date':
                        df[col] = pd.Timestamp.now().date()
                    else:
                        df[col] = '-'

            # Drop rows where all elements are NaN
            df = df.dropna(how='all')
            
            # Convert date column to datetime
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

            # Fill NaN values with appropriate defaults
            # Convert Week Number to numeric, replacing non-numeric with 0
            df['Week Number'] = pd.to_numeric(df['Week Number'], errors='coerce').fillna(0).astype('Int64')
            
            # First replace dashes with nan
            df = df.replace({'-': pd.NA})
            
            # Then fill remaining NaN values with appropriate defaults
            df['Customer'] = df['Customer'].fillna('-')
            df['Project'] = df['Project'].fillna('-')
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

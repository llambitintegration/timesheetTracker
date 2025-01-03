import pandas as pd
from typing import List
import schemas
import calendar
from datetime import datetime

def parse_excel(file) -> List[schemas.TimeEntryCreate]:
    df = pd.read_excel(file)
    entries = []

    required_columns = ['week_number', 'month', 'category', 'subcategory', 'customer_name', 'project_id', 'task_description', 'hours']
    if not all(col in df.columns for col in required_columns):
        raise ValueError("Missing required columns in the Excel file")

    for _, row in df.iterrows():
        entry = schemas.TimeEntryCreate(
            week_number=int(row['week_number']),
            month=str(row['month']),
            category=str(row['category']),
            subcategory=str(row['subcategory']),
            customer_name=str(row['customer_name']),
            project_id=str(row['project_id']),
            task_description=str(row.get('task_description', '')),
            hours=float(row['hours'])
        )
        entries.append(entry)
    return entries

def parse_csv(file) -> List[schemas.TimeEntryCreate]:
    df = pd.read_csv(file)
    entries = []

    required_columns = ['week_number', 'month', 'category', 'subcategory', 'customer_name', 'project_id', 'task_description', 'hours']
    if not all(col in df.columns for col in required_columns):
        raise ValueError("Missing required columns in the CSV file")

    for _, row in df.iterrows():
        entry = schemas.TimeEntryCreate(
            week_number=int(row['week_number']),
            month=str(row['month']),
            category=str(row['category']),
            subcategory=str(row['subcategory']),
            customer_name=str(row['customer_name']),
            project_id=str(row['project_id']),
            task_description=str(row.get('task_description', '')),
            hours=float(row['hours'])
        )
        entries.append(entry)
    return entries
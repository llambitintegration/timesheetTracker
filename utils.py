import pandas as pd
from typing import List
import schemas

def parse_excel(file) -> List[schemas.TimeEntryCreate]:
    df = pd.read_excel(file)
    entries = []

    required_columns = ['employee_id', 'project', 'task', 'hours', 'date']
    if not all(col in df.columns for col in required_columns):
        raise ValueError("Missing required columns in the Excel file")

    for _, row in df.iterrows():
        entry = schemas.TimeEntryCreate(
            employee_id=str(row['employee_id']),
            project=str(row['project']),
            task=str(row['task']),
            hours=float(row['hours']),
            date=pd.to_datetime(row['date']),
            description=str(row.get('description', ''))
        )
        entries.append(entry)
    return entries

def parse_csv(file) -> List[schemas.TimeEntryCreate]:
    df = pd.read_csv(file)
    entries = []

    required_columns = ['employee_id', 'project', 'task', 'hours', 'date']
    if not all(col in df.columns for col in required_columns):
        raise ValueError("Missing required columns in the CSV file")

    for _, row in df.iterrows():
        entry = schemas.TimeEntryCreate(
            employee_id=str(row['employee_id']),
            project=str(row['project']),
            task=str(row['task']),
            hours=float(row['hours']),
            date=pd.to_datetime(row['date']),
            description=str(row.get('description', ''))
        )
        entries.append(entry)
    return entries
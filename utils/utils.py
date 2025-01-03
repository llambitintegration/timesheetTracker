import pandas as pd
from typing import List
from database import schemas
from datetime import datetime

def parse_csv(file) -> List[schemas.TimeEntryCreate]:
    df = pd.read_csv(file)
    entries = []

    for _, row in df.iterrows():
        # Skip empty rows
        if pd.isna(row['Week Number']) or pd.isna(row['Hours']):
            continue

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
    return entries

def parse_excel(file) -> List[schemas.TimeEntryCreate]:
    df = pd.read_excel(file)
    entries = []

    for _, row in df.iterrows():
        # Skip empty rows
        if pd.isna(row['Week Number']) or pd.isna(row['Hours']):
            continue

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
    return entries
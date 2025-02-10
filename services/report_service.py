
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta
import calendar
from database import schemas
from models.timeEntry import TimeEntry
from models.projectModel import Project
from utils.logger import Logger

logger = Logger().get_logger()

class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def get_weekly_report(self, date: Optional[datetime] = None, project_id: Optional[str] = None) -> schemas.WeeklyReport:
        if date is None:
            date = datetime.now()

        week_start = date - timedelta(days=date.weekday())
        week_end = week_start + timedelta(days=6)

        query = self._build_report_query(week_start.date(), week_end.date(), project_id)
        results = query.all()
        entries = self._create_report_entries(results, f"{week_start.date()} to {week_end.date()}")
        
        return schemas.WeeklyReport(
            entries=entries,
            total_hours=sum(entry.total_hours for entry in entries),
            week_number=week_start.isocalendar()[1],
            month=calendar.month_name[week_start.month]
        )

    def get_monthly_report(self, year: int, month: int, project_id: Optional[str] = None) -> schemas.MonthlyReport:
        _, last_day = calendar.monthrange(year, month)
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, last_day).date()

        query = self._build_report_query(start_date, end_date, project_id)
        results = query.all()
        entries = self._create_report_entries(results, f"{year}-{month:02d}")

        return schemas.MonthlyReport(
            entries=entries,
            total_hours=sum(entry.total_hours for entry in entries),
            month=month,
            year=year
        )

    def _build_report_query(self, start_date, end_date, project_id=None):
        query = self.db.query(
            Project.project_id,
            Project.customer,
            func.sum(TimeEntry.hours).label('total_hours')
        ).join(
            TimeEntry,
            TimeEntry.project == Project.project_id
        ).filter(
            TimeEntry.date >= start_date,
            TimeEntry.date <= end_date
        ).group_by(
            Project.project_id,
            Project.customer
        )

        if project_id:
            query = query.filter(Project.project_id == project_id)

        return query

    def _create_report_entries(self, results, period):
        return [
            schemas.ReportEntry(
                total_hours=float(r.total_hours or 0),
                category=r.customer or "Unassigned",
                project=r.project_id,
                period=period
            )
            for r in results
        ]

from datetime import datetime, timedelta
from typing import Optional

class WeeklyReportWindow:
    def __init__(self, start: datetime, end: datetime, week: int, year: int):
        self.start = start
        self.end = end
        self.week = week
        self.year = year


def get_iso_week(date: datetime) -> int:
    """
    ISO week number
    Monday-based week (ISO-8601)
    """
    return date.isocalendar().week


def get_weekly_report_window_from_monday(monday: datetime) -> WeeklyReportWindow:
    """
    Weekly report window (Tue → next Mon)
    Anchored from the Monday of the current week
    """
    start = monday + timedelta(days=1)  # Tuesday
    end = monday + timedelta(days=7)    # next Monday
    
    iso = monday.isocalendar()
    week = iso.week
    year = iso.year
    
    return WeeklyReportWindow(start, end, week, year)


def get_current_weekly_report_window(today: Optional[datetime] = None) -> WeeklyReportWindow:
    """
    Get the weekly report window for the CURRENT reporting period.
    Window runs Tuesday -> next Monday anchored to the Monday of current week.
    """
    if today is None:
        today = datetime.now()
    
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)

    # Align with frontend logic: find Monday of current week first.
    # Python weekday: Monday=0 ... Sunday=6
    monday = today - timedelta(days=today.weekday())
    return get_weekly_report_window_from_monday(monday)


def format_weekly_report_window(window: WeeklyReportWindow) -> str:
    """
    Format window for display in UI
    Example: Week 9 (Feb 17 - Feb 23) - 2026
    """
    start_str = window.start.strftime("%b %-d")  # Feb 17
    end_str = window.end.strftime("%b %-d")      # Feb 23
    return f"Week {window.week} ({start_str} - {end_str}) - {window.year}"

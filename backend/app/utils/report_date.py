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
    Matches frontend getISOWeek() exactly
    """
    # Create a copy and set to midnight
    tmp = date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # JavaScript: tmp.setDate(tmp.getDate() + 3 - ((tmp.getDay() + 6) % 7))
    # Convert Python weekday (0=Monday, 6=Sunday) to JS weekday (0=Sunday, 6=Saturday)
    js_day = (tmp.weekday() + 1) % 7  # Now 0=Sunday, 1=Monday, ..., 6=Saturday
    
    # Thursday in current week decides the year
    days_to_thursday = 3 - ((js_day + 6) % 7)
    thursday = tmp + timedelta(days=days_to_thursday)
    
    # Week 1 contains January 4th
    week1 = datetime(thursday.year, 1, 4)
    week1 = week1.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate days difference
    days_diff = (thursday - week1).days
    
    # JavaScript: ((week1.getDay() + 6) % 7)
    week1_js_day = (week1.weekday() + 1) % 7
    
    # Final calculation
    week_num = 1 + round((days_diff - 3 + week1_js_day) / 7)
    
    return week_num


def get_weekly_report_window_from_monday(monday: datetime) -> WeeklyReportWindow:
    """
    Weekly report window (Tue → next Mon)
    Anchored from the Monday of the current week
    """
    start = monday + timedelta(days=1)  # Tuesday
    end = monday + timedelta(days=7)    # next Monday
    
    week = get_iso_week(monday)  # ISO week based on Monday
    year = monday.year
    
    return WeeklyReportWindow(start, end, week, year)


def get_current_weekly_report_window(today: Optional[datetime] = None) -> WeeklyReportWindow:
    """
    Get the weekly report window for the FORECAST PERIOD
    Forecast runs Tuesday → next Monday
    Week number is based on the START of forecast (Tuesday)
    """
    if today is None:
        today = datetime.now()
    
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Find the upcoming Tuesday (forecast start)
    days_to_tuesday = (1 - today.weekday()) % 7  # Tuesday = 1 in Python
    if days_to_tuesday == 0:
        days_to_tuesday = 7  # If today is Tuesday, forecast starts today
    
    forecast_start = today + timedelta(days=days_to_tuesday)
    
    # Forecast ends next Monday (6 days later)
    forecast_end = forecast_start + timedelta(days=6)
    
    # Week number based on forecast start (Tuesday)
    week = forecast_start.isocalendar()[1]
    year = forecast_start.year
    
    return WeeklyReportWindow(forecast_start, forecast_end, week, year)


def format_weekly_report_window(window: WeeklyReportWindow) -> str:
    """
    Format window for display in UI
    Example: Week 9 (Feb 17 - Feb 23) - 2026
    """
    start_str = window.start.strftime("%b %-d")  # Feb 17
    end_str = window.end.strftime("%b %-d")      # Feb 23
    return f"Week {window.week} ({start_str} - {end_str}) - {window.year}"

"""
Utility functions for PDF generation.
"""

from typing import List, Tuple
from datetime import datetime
from reportlab.lib.units import cm


def format_date(date_str: str, format: str = "%B %d, %Y") -> str:
    """Format ISO date string to readable format."""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime(format)
    except (ValueError, AttributeError):
        return date_str


def format_temperature(temp: float, unit: str = "°C") -> str:
    """Format temperature value."""
    return f"{temp:.1f}{unit}"


def format_rainfall(rainfall: float, unit: str = "mm") -> str:
    """Format rainfall value."""
    return f"{rainfall:.1f} {unit}"


def format_wind_speed(speed: float, unit: str = "km/h") -> str:
    """Format wind speed value."""
    return f"{speed:.1f} {unit}"


def format_percentage(value: float) -> str:
    """Format percentage value."""
    return f"{value:.1f}%"


def split_text_into_lines(text: str, max_width: float, font_size: int, font_name: str = "Helvetica") -> List[str]:
    """
    Split text into lines that fit within max_width.
    
    This is a simple implementation. For more complex text wrapping,
    consider using reportlab's Paragraph class.
    """
    # Approximate character width (this is a rough estimate)
    # For Helvetica at 10pt, average char width is about 0.6 * font_size
    avg_char_width = font_size * 0.6
    max_chars_per_line = int(max_width / avg_char_width)
    
    words = text.split()
    lines = []
    current_line = []
    current_length = 0
    
    for word in words:
        word_length = len(word) + 1  # +1 for space
        if current_length + word_length <= max_chars_per_line:
            current_line.append(word)
            current_length += word_length
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = word_length
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return lines


def calculate_table_column_widths(num_columns: int, total_width: float, 
                                   header_widths: List[float] = None) -> List[float]:
    """
    Calculate column widths for a table.
    
    Args:
        num_columns: Number of columns
        total_width: Total available width
        header_widths: Optional list of relative widths (will be normalized)
    
    Returns:
        List of column widths
    """
    if header_widths and len(header_widths) == num_columns:
        # Normalize relative widths
        total_relative = sum(header_widths)
        return [total_width * (w / total_relative) for w in header_widths]
    else:
        # Equal widths
        return [total_width / num_columns] * num_columns


def get_risk_level_color(risk_level: str) -> str:
    """Get color hex code for risk level."""
    colors = {
        "low": "#10b981",      # Green
        "moderate": "#f59e0b",  # Orange
        "high": "#ef4444",      # Red
    }
    return colors.get(risk_level.lower(), "#6b7280")  # Default gray


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max_length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_week_period(start_date: str, end_date: str) -> str:
    """Format week period string."""
    start = format_date(start_date, "%B %d")
    end = format_date(end_date, "%B %d, %Y")
    return f"{start} - {end}"


def validate_image_path(image_path: str) -> bool:
    """Validate that image path exists (basic check)."""
    import os
    return os.path.exists(image_path) if image_path else False

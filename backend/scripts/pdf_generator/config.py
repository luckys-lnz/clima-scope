"""
PDF Generation Configuration

Defines fonts, colors, page sizes, and styling for PDF reports.
"""

from dataclasses import dataclass
from typing import Literal
from reportlab.lib import colors
from reportlab.lib.units import cm, inch
from reportlab.lib.pagesizes import A4, letter


@dataclass
class ReportConfig:
    """Configuration for PDF report generation."""
    
    # Page settings
    page_size: Literal["A4", "Letter"] = "A4"
    margin_top: float = 2.5  # cm
    margin_bottom: float = 2.5  # cm
    margin_left: float = 2.0  # cm
    margin_right: float = 2.0  # cm
    
    # Language
    language: Literal["en", "sw"] = "en"
    
    # Content options
    include_observations: bool = False
    include_historical_comparison: bool = False
    include_extended_outlook: bool = False
    
    # Color scheme
    color_scheme: Literal["standard", "colorblind-friendly"] = "standard"
    
    # Map resolution
    map_resolution: int = 300  # DPI
    
    @property
    def page_dimensions(self):
        """Get page dimensions in points."""
        if self.page_size == "A4":
            return A4
        return letter
    
    @property
    def page_width(self):
        """Get page width in points."""
        return self.page_dimensions[0]
    
    @property
    def page_height(self):
        """Get page height in points."""
        return self.page_dimensions[1]
    
    @property
    def content_width(self):
        """Get content width in points."""
        return self.page_width - (self.margin_left + self.margin_right) * cm
    
    @property
    def content_height(self):
        """Get content height in points."""
        return self.page_height - (self.margin_top + self.margin_bottom) * cm


class Colors:
    """Color palette for reports."""
    
    # Primary colors
    PRIMARY = colors.HexColor("#1e40af")  # Blue
    SECONDARY = colors.HexColor("#059669")  # Green
    ACCENT = colors.HexColor("#dc2626")  # Red
    
    # Text colors
    TEXT_PRIMARY = colors.HexColor("#1f2937")  # Dark gray
    TEXT_SECONDARY = colors.HexColor("#6b7280")  # Medium gray
    TEXT_LIGHT = colors.HexColor("#9ca3af")  # Light gray
    
    # Background colors
    BG_LIGHT = colors.HexColor("#f9fafb")  # Very light gray
    BG_SECTION = colors.HexColor("#ffffff")  # White
    
    # Rainfall colors (gradient)
    RAINFALL_LOW = colors.HexColor("#e0f2fe")  # Light blue
    RAINFALL_MEDIUM = colors.HexColor("#38bdf8")  # Medium blue
    RAINFALL_HIGH = colors.HexColor("#0284c7")  # Dark blue
    RAINFALL_EXTREME = colors.HexColor("#0c4a6e")  # Very dark blue
    
    # Temperature colors (gradient)
    TEMP_COOL = colors.HexColor("#3b82f6")  # Blue
    TEMP_MODERATE = colors.HexColor("#10b981")  # Green
    TEMP_WARM = colors.HexColor("#f59e0b")  # Orange
    TEMP_HOT = colors.HexColor("#ef4444")  # Red
    
    # Wind colors (gradient)
    WIND_CALM = colors.HexColor("#f3f4f6")  # Light gray
    WIND_LIGHT = colors.HexColor("#dbeafe")  # Light blue
    WIND_MODERATE = colors.HexColor("#60a5fa")  # Medium blue
    WIND_STRONG = colors.HexColor("#2563eb")  # Dark blue
    WIND_EXTREME = colors.HexColor("#1e3a8a")  # Very dark blue
    
    # Status colors
    SUCCESS = colors.HexColor("#10b981")  # Green
    WARNING = colors.HexColor("#f59e0b")  # Orange
    ERROR = colors.HexColor("#ef4444")  # Red
    INFO = colors.HexColor("#3b82f6")  # Blue


class Fonts:
    """Font definitions for reports."""
    
    # Font families
    FAMILY_SANS = "Helvetica"
    FAMILY_SERIF = "Times-Roman"
    FAMILY_MONO = "Courier"
    
    # Heading sizes
    H1_SIZE = 24
    H2_SIZE = 18
    H3_SIZE = 14
    H4_SIZE = 12
    
    # Body text
    BODY_SIZE = 10
    SMALL_SIZE = 8
    TINY_SIZE = 7
    
    # Table text
    TABLE_HEADER_SIZE = 10
    TABLE_CELL_SIZE = 9


class Spacing:
    """Spacing constants."""
    
    # Vertical spacing
    SECTION_SPACING = 0.5  # cm
    PARAGRAPH_SPACING = 0.3  # cm
    LINE_SPACING = 0.2  # cm
    
    # Horizontal spacing
    COLUMN_GAP = 0.5  # cm
    INDENT = 0.5  # cm

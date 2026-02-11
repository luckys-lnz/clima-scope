"""
PDF Generator Module for Clima-scope

Standalone PDF report generation from structured weather data.
Includes AI-powered report generation capabilities.
"""

from .pdf_builder import PDFReportBuilder
from .enhanced_pdf_builder import EnhancedPDFBuilder
from .models import CompleteWeatherReport, ReportGenerationConfig
from .config import ReportConfig
from .ai_service import AIService, AIProvider
from .report_generator import ReportGenerator

__version__ = "0.2.0"
__all__ = [
    "PDFReportBuilder",
    "EnhancedPDFBuilder",
    "CompleteWeatherReport",
    "ReportGenerationConfig",
    "ReportConfig",
    "AIService",
    "AIProvider",
    "ReportGenerator",
]

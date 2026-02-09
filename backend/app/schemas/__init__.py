"""
Pydantic Schemas

Request and response schemas for API endpoints.
"""

from .common import HealthResponse, ErrorResponse, MessageResponse, PaginationParams
from .county import (
    CountyBase,
    CountyCreate,
    CountyUpdate,
    CountyResponse,
    CountyListResponse,
    CountyDetailResponse,
)
from .report import (
    WeatherReportBase,
    WeatherReportCreate,
    WeatherReportUpdate,
    WeatherReportResponse,
    WeatherReportListResponse,
    CompleteReportResponse,
    CompleteReportDetailResponse,
    GenerateCompleteReportRequest,
    GenerateCompleteReportResponse,
    GeneratePDFWithOptionsRequest,
    GeneratePDFWithOptionsResponse,
)
from .pdf import (
    PDFReportResponse,
    PDFReportListResponse,
    GeneratePDFRequest,
    GeneratePDFResponse,
    GeneratePDFFromRawRequest,
)

__all__ = [
    # Common
    "HealthResponse",
    "ErrorResponse",
    "MessageResponse",
    "PaginationParams",
    # County
    "CountyBase",
    "CountyCreate",
    "CountyUpdate",
    "CountyResponse",
    "CountyListResponse",
    "CountyDetailResponse",
    # Report
    "WeatherReportBase",
    "WeatherReportCreate",
    "WeatherReportUpdate",
    "WeatherReportResponse",
    "WeatherReportListResponse",
    "CompleteReportResponse",
    "CompleteReportDetailResponse",
    "GenerateCompleteReportRequest",
    "GenerateCompleteReportResponse",
    "GeneratePDFWithOptionsRequest",
    "GeneratePDFWithOptionsResponse",
    # PDF
    "PDFReportResponse",
    "PDFReportListResponse",
    "GeneratePDFRequest",
    "GeneratePDFResponse",
    "GeneratePDFFromRawRequest",
]

"""
Pydantic Schemas

Request and response schemas for API endpoints.
"""

from .common import HealthResponse, ErrorResponse, MessageResponse, PaginationParams
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
from .upload import UploadResponse

__all__ = [
    # Common
    "HealthResponse",
    "ErrorResponse",
    "MessageResponse",
    "PaginationParams",
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
    # Upload
    "UploadResponse",
]

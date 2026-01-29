"""
PDF Schemas

Pydantic schemas for PDF-related requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PDFReportResponse(BaseModel):
    """Schema for PDF report response."""
    id: int
    complete_report_id: int
    file_path: str
    file_name: str
    file_size_bytes: Optional[int] = None
    generated_at: datetime
    generation_duration_seconds: Optional[int] = None
    is_available: str
    download_count: int
    last_downloaded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PDFReportListResponse(BaseModel):
    """Schema for list of PDF reports."""
    pdfs: list[PDFReportResponse]
    total: int
    page: int = 1
    page_size: int = 50


class GeneratePDFRequest(BaseModel):
    """Schema for generating a PDF from complete report."""
    complete_report_id: int = Field(..., description="ID of the CompleteReport")
    output_path: Optional[str] = Field(None, description="Custom output path (optional)")


class GeneratePDFResponse(BaseModel):
    """Schema for generate PDF response."""
    pdf_report: PDFReportResponse
    message: str = "PDF generated successfully"


class GeneratePDFFromRawRequest(BaseModel):
    """Schema for generating PDF directly from raw weather data."""
    weather_report_id: int = Field(..., description="ID of the WeatherReport")
    output_path: Optional[str] = Field(None, description="Custom output path (optional)")

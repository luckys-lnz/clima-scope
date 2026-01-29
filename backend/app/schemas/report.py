"""
Report Schemas

Pydantic schemas for weather report requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class WeatherReportBase(BaseModel):
    """Base weather report schema."""
    county_id: str = Field(..., min_length=2, max_length=2, description="KNBS county code")
    period_start: datetime = Field(..., description="Report period start date")
    period_end: datetime = Field(..., description="Report period end date")
    week_number: Optional[int] = Field(None, ge=1, le=53, description="ISO week number")
    year: int = Field(..., ge=2000, le=2100, description="Year")


class WeatherReportCreate(WeatherReportBase):
    """Schema for creating a weather report."""
    raw_data: Dict[str, Any] = Field(..., description="Complete CountyWeatherReport JSON")
    schema_version: str = Field(default="1.0", description="Schema version")


class WeatherReportUpdate(BaseModel):
    """Schema for updating a weather report."""
    raw_data: Optional[Dict[str, Any]] = None
    processed: Optional[bool] = None
    processing_error: Optional[str] = None


class WeatherReportResponse(WeatherReportBase):
    """Schema for weather report response."""
    id: int
    schema_version: str
    model_run_timestamp: Optional[datetime] = None
    data_source: Optional[str] = None
    quality_overall: Optional[str] = None
    quality_missing_data_percent: Optional[int] = None
    quality_spatial_coverage_percent: Optional[int] = None
    processed: bool
    processing_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WeatherReportListResponse(BaseModel):
    """Schema for list of weather reports."""
    reports: list[WeatherReportResponse]
    total: int
    page: int = 1
    page_size: int = 50


class CompleteReportResponse(BaseModel):
    """Schema for complete report response."""
    id: int
    weather_report_id: int
    county_id: str
    period_start: datetime
    period_end: datetime
    week_number: Optional[int] = None
    year: int
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    generated_at: datetime
    generation_duration_seconds: Optional[int] = None
    is_published: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CompleteReportDetailResponse(CompleteReportResponse):
    """Schema for detailed complete report with full data."""
    report_data: Dict[str, Any] = Field(..., description="Complete CompleteWeatherReport JSON")


class GenerateCompleteReportRequest(BaseModel):
    """Schema for generating a complete report from weather report."""
    weather_report_id: int = Field(..., description="ID of the source WeatherReport")
    force_regenerate: bool = Field(default=False, description="Regenerate even if already exists")


class GenerateCompleteReportResponse(BaseModel):
    """Schema for generate complete report response."""
    complete_report: CompleteReportDetailResponse
    message: str = "Complete report generated successfully"

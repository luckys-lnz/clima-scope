"""
County Schemas

Pydantic schemas for county-related requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CountyBase(BaseModel):
    """Base county schema with common fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Official county name")
    region: Optional[str] = Field(None, max_length=50, description="Region name")
    notes: Optional[str] = Field(None, description="Additional notes or metadata")


class CountyCreate(CountyBase):
    """Schema for creating a county."""
    id: str = Field(..., min_length=2, max_length=2, description="KNBS county code (2-digit)")


class CountyUpdate(BaseModel):
    """
    Schema for updating a county.
    
    Note: Counties are reference data. Only metadata (notes) can be updated.
    Name, region, and ID are fixed and cannot be changed.
    """
    notes: Optional[str] = Field(None, description="Additional notes or metadata (only field that can be updated)")


class CountyResponse(CountyBase):
    """Schema for county response."""
    id: str = Field(..., description="KNBS county code")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CountyListResponse(BaseModel):
    """Schema for list of counties."""
    counties: list[CountyResponse]
    total: int


class CountyDetailResponse(CountyResponse):
    """Schema for detailed county response with relationships."""
    ward_count: Optional[int] = Field(None, description="Number of wards in county")
    report_count: Optional[int] = Field(None, description="Number of weather reports for county")

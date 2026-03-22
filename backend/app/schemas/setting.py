from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional, Any, Dict
from datetime import datetime


class SharedFileResponse(BaseModel):
    id: UUID
    file_name: str
    file_type: str
    upload_date: datetime
    file_path: Optional[str] = None


class UserSettingsResponse(BaseModel):
    pdf_template_id: Optional[UUID]
    selected_template: Optional[SharedFileResponse] = None
    show_constituencies: bool = True
    show_wards: bool = True
    show_constituency_labels: bool = True
    show_ward_labels: bool = True
    constituency_label_font_size: int = 12
    ward_label_font_size: int = 12
    constituency_border_color: str = "#1e293b"
    constituency_border_width: float = 1.2
    constituency_border_style: str = "solid"
    ward_border_color: str = "#2563eb"
    ward_border_width: float = 0.9
    ward_border_style: str = "dashed"


class SettingsResponse(BaseModel):
    shapefile_name: str
    shapefile_path: str
    templates: List[SharedFileResponse]
    user_settings: UserSettingsResponse


class MapPreviewLabel(BaseModel):
    name: str
    lon: float
    lat: float
    type: Optional[str] = None


class MapPreviewResponse(BaseModel):
    county: str
    bbox: List[float]
    county_geometry: Dict[str, Any]
    constituency_boundaries: Optional[Dict[str, Any]] = None
    ward_boundaries: Optional[Dict[str, Any]] = None
    labels: List[MapPreviewLabel] = []


class UpdateSettingsRequest(BaseModel):
    pdf_template_id: Optional[UUID] = None
    show_constituencies: Optional[bool] = None
    show_wards: Optional[bool] = None
    show_constituency_labels: Optional[bool] = None
    show_ward_labels: Optional[bool] = None
    constituency_label_font_size: Optional[int] = Field(default=None, ge=6, le=48)
    ward_label_font_size: Optional[int] = Field(default=None, ge=6, le=48)
    constituency_border_color: Optional[str] = None
    constituency_border_width: Optional[float] = None
    constituency_border_style: Optional[str] = None
    ward_border_color: Optional[str] = None
    ward_border_width: Optional[float] = None
    ward_border_style: Optional[str] = None

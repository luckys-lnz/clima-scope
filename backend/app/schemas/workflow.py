from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import List, Optional, Dict, Any


# ============================================
# Report Period Schema
# ============================================
class ReportPeriod(BaseModel):
    start: str  # ISO format date
    end: str    # ISO format date


# ============================================
# Validation Request Schema
# ============================================
class ValidationRequest(BaseModel):
    report_week: int
    report_year: int
    report_start_at: str
    report_end_at: str


# ============================================
# Validation Response Schema
# ============================================
class ValidationResponse(BaseModel):
    observation_found: bool
    shapefile_found: bool
    variables: List[str]
    observation_file: str
    shapefile: str
    report_week: int
    report_year: int
    report_period: ReportPeriod
    column_count: int
    row_count: int


# ============================================
# MAP GENERATION SCHEMAS
# ============================================

class MapGenerationRequest(BaseModel):
    """Request to generate maps for selected variables"""
    county: str
    variables: List[str]
    report_week: int
    report_year: int
    report_start_at: str
    report_end_at: str


class MapOutput(BaseModel):
    """Single map output"""
    variable: str
    map_url: str
    thumbnail_url: Optional[str] = None


class MapGenerationResponse(BaseModel):
    """Response after generating maps"""
    outputs: List[MapOutput]
    workflow_status_id: Optional[int] = None


# ============================================
# Generated Maps Schema (for database records)
# ============================================
class GeneratedMap(BaseModel):
    """Record of a generated map in the database"""
    id: Optional[str] = None
    user_id: str
    workflow_status_id: int
    variable: str
    map_url: str
    storage_path: str
    report_week: int
    report_year: int
    file_size: Optional[int] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ============================================
# Workflow Status Schema (UPDATED)
# ============================================
class WorkflowStatus(BaseModel):
    id: int  # Changed from str to int to match database
    user_id: str
    report_week: int
    report_year: int
    report_start_at: date
    report_end_at: date
    
    # Workflow steps
    uploaded: bool = False
    validated: bool = False
    variables_found: List[str] = Field(default_factory=list)
    maps_generated: bool = False
    report_generated: bool = False
    completed: bool = False
    
    # File references
    observation_file_id: Optional[str] = None
    shapefile_id: Optional[str] = None
    generated_report_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# Workflow Update Schema
# ============================================
class WorkflowUpdate(BaseModel):
    validated: Optional[bool] = None
    variables_found: Optional[List[str]] = None
    maps_generated: Optional[bool] = None
    report_generated: Optional[bool] = None
    completed: Optional[bool] = None
    observation_file_id: Optional[str] = None
    shapefile_id: Optional[str] = None
    generated_report_id: Optional[str] = None


# ============================================
# Variable Detection Schema
# ============================================
class VariableDetection(BaseModel):
    name: str
    detected: bool
    aliases_matched: List[str] = Field(default_factory=list)
    column_name: Optional[str] = None


# ============================================
# Detailed Validation Response (for debugging)
# ============================================
class DetailedValidationResponse(ValidationResponse):
    file_columns: List[str] = Field(default_factory=list)
    variable_detection: List[VariableDetection] = Field(default_factory=list)
    file_size_kb: Optional[float] = None
    shapefile_details: Optional[Dict[str, Any]] = None


# ============================================
# Report Generation (Step 4)
# ============================================


class ReportGenerationRequest(BaseModel):
    """Request payload for generating the final weekly PDF report."""

    county_name: str
    week_number: int
    year: int
    report_start_at: str
    report_end_at: str
    variables: List[str] = Field(default_factory=list)


class ReportGenerationResponse(BaseModel):
    """Response returned after generating the final report."""

    pdf_url: str
    filename: str
    report_week: int
    report_year: int
    stage_statuses: List[Dict[str, str]] = Field(default_factory=list)

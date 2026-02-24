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
# Workflow Status Schema
# ============================================
class WorkflowStatus(BaseModel):
    id: str
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

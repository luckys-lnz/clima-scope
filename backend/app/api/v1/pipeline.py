"""
Pipeline API Endpoints

Endpoints for orchestrating the full weather report generation pipeline.
Combines: JSON validation → AI narratives → Map integration → PDF generation
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from ...services.pipeline import PipelineService, PipelineStatus, PipelineError
from ...database import get_db
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Dependency to get pipeline service
_pipeline_service = None

def get_pipeline_service() -> PipelineService:
    """Dependency to get pipeline service singleton."""
    global _pipeline_service
    if _pipeline_service is None:
        _pipeline_service = PipelineService()
    return _pipeline_service


# Request/Response Models

class ProcessRequest(BaseModel):
    """Request to process a weather report through the full pipeline."""
    county_id: str = Field(..., description="KNBS county code (2-digit)")
    period_start: str = Field(..., description="Period start date (YYYY-MM-DD)")
    period_end: str = Field(..., description="Period end date (YYYY-MM-DD)")
    raw_data: dict = Field(..., description="Raw weather data JSON")
    async_mode: bool = Field(True, description="Run in background (recommended for production)")
    
    class Config:
        schema_extra = {
            "example": {
                "county_id": "31",
                "period_start": "2026-01-27",
                "period_end": "2026-02-02",
                "raw_data": {
                    "schema_version": "1.0",
                    "county_id": "31",
                    "county_name": "Nairobi",
                    "period": {"start": "2026-01-27", "end": "2026-02-02"},
                    "variables": {
                        "temperature": {"weekly": {"mean": 21.5, "max": 26.8, "min": 14.2}},
                        "rainfall": {"weekly": {"total": 28.7, "max_intensity": 12.5}},
                        "wind": {"weekly": {"mean_speed": 13.5, "max_gust": 28.3, "dominant_direction": "NE"}}
                    },
                    "metadata": {
                        "data_source": "GFS",
                        "model_run": "2026-01-27T00:00:00Z",
                        "generated": "2026-01-27T03:15:00Z",
                        "aggregation_method": "point-in-polygon",
                        "grid_resolution": "0.25°",
                        "grid_points_used": 46
                    }
                },
                "async_mode": True
            }
        }


class PipelineResponse(BaseModel):
    """Response for pipeline execution."""
    pipeline_id: str
    status: str
    current_stage: str
    progress: int
    estimated_completion: Optional[str] = None
    error: Optional[str] = None


# Endpoints

@router.post("/process", status_code=status.HTTP_202_ACCEPTED, tags=["pipeline"])
async def process_report(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    pipeline_service: PipelineService = Depends(get_pipeline_service),
    db: Session = Depends(get_db)
):
    """
    Process a weather report through the full pipeline.
    
    **Pipeline Stages**:
    1. Validate input JSON against schema
    2. Generate AI-powered narratives
    3. Check for/await map images
    4. Generate PDF with embedded maps
    5. Store artifacts in database
    6. Return report IDs
    
    **Modes**:
    - `async_mode=true` (recommended): Returns immediately, process runs in background
    - `async_mode=false`: Waits for completion (may timeout on slow operations)
    
    **Progress Tracking**:
    Use `GET /api/v1/pipeline/{pipeline_id}/status` to check progress.
    
    Returns:
        Pipeline execution details with pipeline_id for tracking
    """
    try:
        # Create pipeline execution
        execution = pipeline_service.create_pipeline(
            county_id=request.county_id,
            period_start=request.period_start,
            period_end=request.period_end,
            raw_data=request.raw_data
        )
        
        if request.async_mode:
            # Run in background
            background_tasks.add_task(pipeline_service.execute_pipeline, execution.pipeline_id)
            
            return {
                "message": "Pipeline started in background",
                "pipeline_id": execution.pipeline_id,
                "status": execution.status.value,
                "current_stage": execution.current_stage.value,
                "progress": execution.progress,
                "estimated_completion": "30-60 seconds",
                "tracking_url": f"/api/v1/pipeline/{execution.pipeline_id}/status"
            }
        else:
            # Run synchronously (blocking)
            await pipeline_service.execute_pipeline(execution.pipeline_id)
            
            return {
                "message": "Pipeline completed",
                "pipeline_id": execution.pipeline_id,
                "status": execution.status.value,
                "current_stage": execution.current_stage.value,
                "progress": execution.progress,
                "artifacts": {
                    "weather_report_id": execution.weather_report_id,
                    "pdf_report_id": execution.pdf_report_id
                }
            }
            
    except PipelineError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error("pipeline_api_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start pipeline: {str(e)}"
        )


@router.get("/{pipeline_id}/status", tags=["pipeline"])
async def get_pipeline_status(
    pipeline_id: str,
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """
    Get the current status of a pipeline execution.
    
    **Status Values**:
    - `pending`: Pipeline created, not yet started
    - `running`: Currently executing
    - `completed`: Successfully completed
    - `failed`: Execution failed (check error field)
    - `cancelled`: Execution was cancelled
    
    **Progress**: 0-100 percentage complete
    
    Returns:
        Pipeline execution status with progress and artifacts
    """
    execution = pipeline_service.get_pipeline(pipeline_id)
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline not found: {pipeline_id}"
        )
    
    return execution.to_dict()


@router.post("/{pipeline_id}/cancel", tags=["pipeline"])
async def cancel_pipeline(
    pipeline_id: str,
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """
    Cancel a running pipeline execution.
    
    Note: Cancellation is best-effort. Some stages may complete before cancellation takes effect.
    
    Returns:
        Confirmation message
    """
    success = pipeline_service.cancel_pipeline(pipeline_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline not found or already completed: {pipeline_id}"
        )
    
    return {
        "message": "Pipeline cancelled",
        "pipeline_id": pipeline_id
    }


@router.get("/history", tags=["pipeline"])
async def list_pipeline_history(
    county_id: Optional[str] = Query(None, description="Filter by county"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """
    List pipeline execution history.
    
    Useful for:
    - Monitoring recent processing jobs
    - Debugging failed pipelines
    - Auditing report generation
    
    Returns:
        List of pipeline executions (most recent first)
    """
    try:
        # Parse status enum if provided
        status_enum = None
        if status:
            try:
                status_enum = PipelineStatus(status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status: {status}. Valid values: pending, running, completed, failed, cancelled"
                )
        
        pipelines = pipeline_service.list_pipelines(
            county_id=county_id,
            status=status_enum
        )
        
        # Apply limit
        pipelines = pipelines[:limit]
        
        return {
            "total": len(pipelines),
            "limit": limit,
            "filters": {
                "county_id": county_id,
                "status": status
            },
            "pipelines": [p.to_dict() for p in pipelines]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_pipelines_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list pipelines: {str(e)}"
        )

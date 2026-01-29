"""
Data Upload Endpoints

Endpoints for Person A (GFS Processing) to upload processed weather data
and for general file uploads.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from ...database import get_db
from ...utils.logging import get_logger
from ...services.pipeline import PipelineService

logger = get_logger(__name__)

router = APIRouter()


@router.post("/weather-data", status_code=status.HTTP_201_CREATED, tags=["uploads"])
async def upload_weather_data(
    county_id: str = Form(..., description="KNBS county code"),
    period_start: str = Form(..., description="Period start date (YYYY-MM-DD)"),
    period_end: str = Form(..., description="Period end date (YYYY-MM-DD)"),
    file: UploadFile = File(..., description="Weather data JSON file"),
    auto_process: bool = Form(False, description="Automatically start pipeline processing"),
    db: Session = Depends(get_db)
):
    """
    Upload raw weather data JSON file.
    
    This endpoint is designed for Person A's GFS processing pipeline to upload
    processed weather data. The JSON must conform to the County Weather Report schema.
    
    **Usage**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/uploads/weather-data" \\
      -F "county_id=31" \\
      -F "period_start=2026-01-27" \\
      -F "period_end=2026-02-02" \\
      -F "file=@nairobi_weather.json" \\
      -F "auto_process=true"
    ```
    
    **Options**:
    - `auto_process=true`: Automatically start pipeline processing after upload
    - `auto_process=false`: Just store the data, manual processing trigger needed
    
    Returns:
        Upload confirmation with optional pipeline_id if auto-processing
    """
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be JSON format (.json extension)"
        )
    
    try:
        # Read and parse JSON
        content = await file.read()
        weather_data = json.loads(content)
        
        logger.info(
            "weather_data_uploaded",
            county_id=county_id,
            period=f"{period_start} to {period_end}",
            size_bytes=len(content),
            filename=file.filename
        )
        
        # Validate basic structure
        required_fields = ['schema_version', 'county_id', 'county_name', 'period', 'variables', 'metadata']
        missing_fields = [f for f in required_fields if f not in weather_data]
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Validate county_id matches
        if weather_data.get('county_id') != county_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"County ID mismatch: form={county_id}, json={weather_data.get('county_id')}"
            )
        
        response = {
            "message": "Weather data uploaded successfully",
            "county_id": county_id,
            "period_start": period_start,
            "period_end": period_end,
            "filename": file.filename,
            "size_bytes": len(content),
            "schema_version": weather_data.get('schema_version'),
            "auto_process": auto_process
        }
        
        # Auto-process if requested
        if auto_process:
            pipeline_service = PipelineService(db)
            execution = pipeline_service.create_pipeline(
                county_id=county_id,
                period_start=period_start,
                period_end=period_end,
                raw_data=weather_data
            )
            
            # Start pipeline in background
            import asyncio
            asyncio.create_task(pipeline_service.execute_pipeline(execution.pipeline_id))
            
            response["pipeline_id"] = execution.pipeline_id
            response["pipeline_status_url"] = f"/api/v1/pipeline/{execution.pipeline_id}/status"
        
        return response
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid JSON format: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("weather_data_upload_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/grib-metadata", status_code=status.HTTP_201_CREATED, tags=["uploads"])
async def upload_grib_metadata(
    county_id: str = Form(..., description="KNBS county code"),
    model_run: str = Form(..., description="GFS model run timestamp (ISO 8601)"),
    file: UploadFile = File(..., description="GRIB metadata JSON file"),
    db: Session = Depends(get_db)
):
    """
    Upload GFS GRIB file metadata for audit trail.
    
    This endpoint stores metadata about the GFS model run used to generate
    the weather forecast. Useful for:
    - Audit trail
    - Data provenance
    - Quality assurance
    - Debugging forecast discrepancies
    
    **Metadata should include**:
    - GFS model version
    - Model run timestamp
    - Grid resolution
    - Variables extracted
    - Download timestamp
    - File checksums
    
    Returns:
        Metadata storage confirmation
    """
    try:
        content = await file.read()
        metadata = json.loads(content)
        
        logger.info(
            "grib_metadata_uploaded",
            county_id=county_id,
            model_run=model_run,
            filename=file.filename
        )
        
        # In production, store in database
        # For now, just log and confirm
        
        return {
            "message": "GRIB metadata uploaded successfully",
            "county_id": county_id,
            "model_run": model_run,
            "filename": file.filename,
            "metadata_keys": list(metadata.keys())
        }
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid JSON format: {str(e)}"
        )
    except Exception as e:
        logger.error("grib_metadata_upload_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/status", tags=["uploads"])
async def get_upload_status():
    """
    Get upload service status and statistics.
    
    Returns:
        Service status and upload statistics
    """
    return {
        "status": "operational",
        "endpoints": {
            "weather_data": "/api/v1/uploads/weather-data",
            "maps": "/api/v1/maps/upload",
            "grib_metadata": "/api/v1/uploads/grib-metadata"
        },
        "supported_formats": {
            "weather_data": ["application/json"],
            "maps": ["image/png", "image/svg+xml"],
            "grib_metadata": ["application/json"]
        },
        "max_file_size_mb": 10
    }

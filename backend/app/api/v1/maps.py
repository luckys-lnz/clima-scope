"""
Map Management API Endpoints

Endpoints for uploading, retrieving, and managing weather map images.
These endpoints are designed for Person A (GFS processing) to upload generated maps
and for the PDF generation service to retrieve them.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from ...services.map_storage import (
    MapStorageService,
    MapVariable,
    MapFormat,
    MapStorageError,
    MapMetadata
)
from ...database import get_db
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_map_storage() -> MapStorageService:
    """Dependency to get map storage service."""
    return MapStorageService()


@router.post("/upload", status_code=status.HTTP_201_CREATED, tags=["maps"])
async def upload_map(
    county_id: str = Form(..., description="KNBS county code (2-digit)"),
    variable: MapVariable = Form(..., description="Weather variable"),
    period_start: str = Form(..., description="Period start date (YYYY-MM-DD)"),
    period_end: str = Form(..., description="Period end date (YYYY-MM-DD)"),
    file: UploadFile = File(..., description="Map image file"),
    format: MapFormat = Form(MapFormat.PNG, description="Image format"),
    resolution_dpi: int = Form(300, description="Image resolution in DPI"),
    width_px: int = Form(1200, description="Image width in pixels"),
    height_px: int = Form(900, description="Image height in pixels"),
    overwrite: bool = Form(False, description="Overwrite existing map"),
    map_storage: MapStorageService = Depends(get_map_storage)
):
    """
    Upload a weather map image.
    
    This endpoint is used by Person A's geospatial processing pipeline to upload
    generated map images for counties.
    
    **Expected Usage**:
    ```bash
    curl -X POST "http://localhost:8000/api/v1/maps/upload" \\
      -F "county_id=31" \\
      -F "variable=rainfall" \\
      -F "period_start=2026-01-27" \\
      -F "period_end=2026-02-02" \\
      -F "file=@nairobi_rainfall.png"
    ```
    
    Returns:
        Metadata for the uploaded map
    """
    # Validate county_id format
    if not county_id.isdigit() or len(county_id) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="County ID must be a 2-digit string (e.g., '31')"
        )
    
    # Validate period format
    try:
        datetime.fromisoformat(period_start)
        datetime.fromisoformat(period_end)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period dates must be in ISO format (YYYY-MM-DD)"
        )
    
    # Save uploaded file temporarily
    temp_dir = Path("/tmp/clima-scope-maps")
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / f"{county_id}_{variable}_{datetime.now().timestamp()}.{format.value}"
    
    try:
        # Write uploaded file
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(
            "map_uploaded",
            county_id=county_id,
            variable=variable.value,
            size_bytes=len(content)
        )
        
        # Store map using map storage service
        metadata = map_storage.store_map(
            source_file=temp_file,
            county_id=county_id,
            variable=variable,
            period_start=period_start,
            period_end=period_end,
            format=format,
            metadata={
                "resolution_dpi": resolution_dpi,
                "width_px": width_px,
                "height_px": height_px
            },
            overwrite=overwrite
        )
        
        return {
            "message": "Map uploaded successfully",
            "map": metadata.to_dict()
        }
        
    except MapStorageError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store map: {str(e)}"
        )
    finally:
        # Clean up temp file
        if temp_file.exists():
            temp_file.unlink()


@router.get("/{county_id}", tags=["maps"])
async def list_county_maps(
    county_id: str,
    variable: Optional[MapVariable] = Query(None, description="Filter by variable"),
    year: Optional[int] = Query(None, description="Filter by year"),
    week: Optional[int] = Query(None, ge=1, le=53, description="Filter by ISO week number"),
    map_storage: MapStorageService = Depends(get_map_storage)
):
    """
    List all maps for a specific county.
    
    Optionally filter by variable, year, and week.
    
    Returns:
        List of map metadata objects
    """
    try:
        maps = map_storage.list_maps(
            county_id=county_id,
            variable=variable,
            year=year,
            week=week
        )
        
        return {
            "county_id": county_id,
            "total": len(maps),
            "maps": [m.to_dict() for m in maps]
        }
    except Exception as e:
        logger.error("list_maps_failed", county_id=county_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list maps: {str(e)}"
        )


@router.get("/{county_id}/{variable}", tags=["maps"])
async def get_map_for_period(
    county_id: str,
    variable: MapVariable,
    period_start: str = Query(..., description="Period start date (YYYY-MM-DD)"),
    period_end: str = Query(..., description="Period end date (YYYY-MM-DD)"),
    format: MapFormat = Query(MapFormat.PNG, description="Image format"),
    map_storage: MapStorageService = Depends(get_map_storage)
):
    """
    Get map metadata for a specific county, variable, and period.
    
    Use `/download` endpoint to retrieve the actual image file.
    
    Returns:
        Map metadata or 404 if not found
    """
    metadata = map_storage.get_map(
        county_id=county_id,
        variable=variable,
        period_start=period_start,
        period_end=period_end,
        format=format
    )
    
    if not metadata:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Map not found for {county_id}/{variable}/{period_start}/{period_end}"
        )
    
    return metadata.to_dict()


@router.get("/{county_id}/{variable}/download", tags=["maps"])
async def download_map(
    county_id: str,
    variable: MapVariable,
    period_start: str = Query(..., description="Period start date (YYYY-MM-DD)"),
    period_end: str = Query(..., description="Period end date (YYYY-MM-DD)"),
    format: MapFormat = Query(MapFormat.PNG, description="Image format"),
    map_storage: MapStorageService = Depends(get_map_storage)
):
    """
    Download the actual map image file.
    
    Returns:
        Image file (PNG, SVG, or JPEG)
    """
    metadata = map_storage.get_map(
        county_id=county_id,
        variable=variable,
        period_start=period_start,
        period_end=period_end,
        format=format
    )
    
    if not metadata or not metadata.file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Map file not found for {county_id}/{variable}/{period_start}/{period_end}"
        )
    
    # Determine media type
    media_type_map = {
        MapFormat.PNG: "image/png",
        MapFormat.SVG: "image/svg+xml",
        MapFormat.JPEG: "image/jpeg"
    }
    
    return FileResponse(
        path=metadata.file_path,
        media_type=media_type_map.get(format, "application/octet-stream"),
        filename=metadata.file_path.name
    )


@router.get("/{county_id}/report-maps", tags=["maps"])
async def get_report_maps(
    county_id: str,
    period_start: str = Query(..., description="Period start date (YYYY-MM-DD)"),
    period_end: str = Query(..., description="Period end date (YYYY-MM-DD)"),
    map_storage: MapStorageService = Depends(get_map_storage)
):
    """
    Get all maps (rainfall, temperature, wind) for a report period.
    
    This is a convenience endpoint for PDF generation to retrieve all maps
    needed for a complete report in one request.
    
    Returns:
        Dict with rainfall, temperature, and wind map metadata
        (null values if maps not available)
    """
    try:
        maps = map_storage.get_maps_for_report(
            county_id=county_id,
            period_start=period_start,
            period_end=period_end
        )
        
        return {
            "county_id": county_id,
            "period_start": period_start,
            "period_end": period_end,
            "maps": {
                "rainfall": maps["rainfall"].to_dict() if maps["rainfall"] else None,
                "temperature": maps["temperature"].to_dict() if maps["temperature"] else None,
                "wind": maps["wind"].to_dict() if maps["wind"] else None
            }
        }
    except Exception as e:
        logger.error("get_report_maps_failed", county_id=county_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report maps: {str(e)}"
        )


@router.delete("/{county_id}/{variable}", status_code=status.HTTP_204_NO_CONTENT, tags=["maps"])
async def delete_map(
    county_id: str,
    variable: MapVariable,
    period_start: str = Query(..., description="Period start date (YYYY-MM-DD)"),
    period_end: str = Query(..., description="Period end date (YYYY-MM-DD)"),
    format: MapFormat = Query(MapFormat.PNG, description="Image format"),
    map_storage: MapStorageService = Depends(get_map_storage)
):
    """
    Delete a map image and its metadata.
    
    Returns:
        204 No Content on success
        404 if map not found
    """
    deleted = map_storage.delete_map(
        county_id=county_id,
        variable=variable,
        period_start=period_start,
        period_end=period_end,
        format=format
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Map not found for {county_id}/{variable}/{period_start}/{period_end}"
        )
    
    logger.info(
        "map_deleted",
        county_id=county_id,
        variable=variable.value,
        period_start=period_start,
        period_end=period_end
    )
    
    return {"message": "Map deleted successfully"}

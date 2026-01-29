"""
County Management Endpoints

Endpoints for accessing county reference data.

Note: Counties are reference data with fixed KNBS codes. They cannot be created
or deleted via the API. Use the seed script (scripts/seed_counties.py) to populate
counties in the database. Only metadata (notes) can be updated.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from ...schemas import (
    CountyUpdate,
    CountyResponse,
    CountyListResponse,
    CountyDetailResponse,
)
from ...database import get_db
from ...models import County
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("", response_model=CountyListResponse, tags=["counties"])
async def list_counties(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search by name or region"),
    db: Session = Depends(get_db),
):
    """
    List all counties (reference data).
    
    Counties are fixed administrative divisions in Kenya with official KNBS codes.
    Supports pagination and optional search by name or region.
    """
    query = db.query(County)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search.lower()}%"
        query = query.filter(
            func.lower(County.name).like(search_term) |
            func.lower(County.region).like(search_term)
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    counties = query.offset(skip).limit(limit).all()
    
    logger.info("counties_listed", total=total, returned=len(counties))
    
    return CountyListResponse(
        counties=[CountyResponse.from_orm(c) for c in counties],
        total=total,
    )


@router.get("/{county_id}", response_model=CountyDetailResponse, tags=["counties"])
async def get_county(
    county_id: str,
    db: Session = Depends(get_db),
):
    """
    Get a specific county by ID (KNBS code).
    
    Counties are reference data with fixed 2-digit KNBS codes (01-47).
    """
    county = db.query(County).filter(County.id == county_id).first()
    
    if not county:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"County with ID '{county_id}' not found"
        )
    
    # Get related counts
    ward_count = len(county.wards) if county.wards else 0
    report_count = len(county.weather_reports) if county.weather_reports else 0
    
    logger.info("county_retrieved", county_id=county_id)
    
    response = CountyDetailResponse.from_orm(county)
    response.ward_count = ward_count
    response.report_count = report_count
    
    return response


@router.patch("/{county_id}", response_model=CountyResponse, tags=["counties"])
async def update_county_notes(
    county_id: str,
    county_data: CountyUpdate,
    db: Session = Depends(get_db),
):
    """
    Update county metadata (notes only).
    
    Counties are reference data with fixed KNBS codes, names, and regions.
    Only the notes field can be updated for administrative purposes.
    """
    county = db.query(County).filter(County.id == county_id).first()
    
    if not county:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"County with ID '{county_id}' not found"
        )
    
    # Only allow notes updates
    update_data = county_data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update. Only 'notes' field can be updated."
        )
    
    # Ensure only notes is being updated
    if "notes" not in update_data or len(update_data) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only the 'notes' field can be updated. Counties are reference data with fixed codes, names, and regions."
        )
    
    # Update notes
    county.notes = update_data.get("notes")
    
    db.commit()
    db.refresh(county)
    
    logger.info("county_notes_updated", county_id=county_id)
    
    return CountyResponse.from_orm(county)

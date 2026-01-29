"""
Weather Report Endpoints

Endpoints for managing weather reports and generating complete reports.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional
from datetime import datetime

from ...schemas import (
    WeatherReportCreate,
    WeatherReportUpdate,
    WeatherReportResponse,
    WeatherReportListResponse,
    CompleteReportResponse,
    CompleteReportDetailResponse,
    GenerateCompleteReportRequest,
    GenerateCompleteReportResponse,
    MessageResponse,
)
from ...database import get_db
from ...models import WeatherReport, CompleteReport, County
from ...services import PDFService, PDFServiceError
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/weather", response_model=WeatherReportListResponse, tags=["reports"])
async def list_weather_reports(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    county_id: Optional[str] = Query(None, description="Filter by county ID"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Filter by year"),
    week_number: Optional[int] = Query(None, ge=1, le=53, description="Filter by week number"),
    processed: Optional[bool] = Query(None, description="Filter by processing status"),
    db: Session = Depends(get_db),
):
    """
    List all weather reports.
    
    Supports pagination and filtering by county, year, week, and processing status.
    """
    query = db.query(WeatherReport)
    
    # Apply filters
    if county_id:
        query = query.filter(WeatherReport.county_id == county_id)
    if year:
        query = query.filter(WeatherReport.year == year)
    if week_number:
        query = query.filter(WeatherReport.week_number == week_number)
    if processed is not None:
        query = query.filter(WeatherReport.processed == processed)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering (newest first)
    reports = query.order_by(WeatherReport.created_at.desc()).offset(skip).limit(limit).all()
    
    logger.info("weather_reports_listed", total=total, returned=len(reports))
    
    return WeatherReportListResponse(
        reports=[WeatherReportResponse.from_orm(r) for r in reports],
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
    )


@router.get("/weather/{report_id}", response_model=WeatherReportResponse, tags=["reports"])
async def get_weather_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific weather report by ID.
    """
    report = db.query(WeatherReport).filter(WeatherReport.id == report_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weather report with ID '{report_id}' not found"
        )
    
    logger.info("weather_report_retrieved", report_id=report_id)
    
    return WeatherReportResponse.from_orm(report)


@router.post("/weather", response_model=WeatherReportResponse, status_code=status.HTTP_201_CREATED, tags=["reports"])
async def create_weather_report(
    report_data: WeatherReportCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new weather report.
    
    Validates that the county exists before creating the report.
    """
    # Verify county exists
    county = db.query(County).filter(County.id == report_data.county_id).first()
    if not county:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"County with ID '{report_data.county_id}' not found"
        )
    
    # Extract metadata from raw_data if available
    raw_data = report_data.raw_data
    metadata = raw_data.get("metadata", {})
    model_run = metadata.get("model_run_timestamp")
    data_source = metadata.get("data_source")
    
    quality_flags = raw_data.get("quality_flags", {})
    
    # Create weather report
    report = WeatherReport(
        county_id=report_data.county_id,
        period_start=report_data.period_start,
        period_end=report_data.period_end,
        week_number=report_data.week_number,
        year=report_data.year,
        raw_data=raw_data,
        schema_version=report_data.schema_version,
        model_run_timestamp=datetime.fromisoformat(model_run.replace("Z", "+00:00")) if model_run else None,
        data_source=data_source,
        quality_overall=quality_flags.get("overall_quality"),
        quality_missing_data_percent=quality_flags.get("missing_data_percent"),
        quality_spatial_coverage_percent=quality_flags.get("spatial_coverage_percent"),
        processed=False,
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    logger.info("weather_report_created", report_id=report.id, county_id=report_data.county_id)
    
    return WeatherReportResponse.from_orm(report)


@router.put("/weather/{report_id}", response_model=WeatherReportResponse, tags=["reports"])
async def update_weather_report(
    report_id: int,
    report_data: WeatherReportUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing weather report.
    """
    report = db.query(WeatherReport).filter(WeatherReport.id == report_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weather report with ID '{report_id}' not found"
        )
    
    # Update fields
    update_data = report_data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    for field, value in update_data.items():
        setattr(report, field, value)
    
    db.commit()
    db.refresh(report)
    
    logger.info("weather_report_updated", report_id=report_id)
    
    return WeatherReportResponse.from_orm(report)


@router.delete("/weather/{report_id}", response_model=MessageResponse, tags=["reports"])
async def delete_weather_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a weather report.
    
    Note: This will cascade delete the associated complete report if it exists.
    """
    report = db.query(WeatherReport).filter(WeatherReport.id == report_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weather report with ID '{report_id}' not found"
        )
    
    db.delete(report)
    db.commit()
    
    logger.info("weather_report_deleted", report_id=report_id)
    
    return MessageResponse(message=f"Weather report '{report_id}' deleted successfully")


@router.get("/complete", response_model=list[CompleteReportResponse], tags=["reports"])
async def list_complete_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    county_id: Optional[str] = Query(None),
    is_published: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """
    List all complete reports.
    """
    query = db.query(CompleteReport)
    
    if county_id:
        query = query.filter(CompleteReport.county_id == county_id)
    if is_published is not None:
        query = query.filter(CompleteReport.is_published == is_published)
    
    reports = query.order_by(CompleteReport.created_at.desc()).offset(skip).limit(limit).all()
    
    return [CompleteReportResponse.from_orm(r) for r in reports]


@router.get("/complete/{report_id}", response_model=CompleteReportDetailResponse, tags=["reports"])
async def get_complete_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific complete report by ID with full report data.
    """
    report = db.query(CompleteReport).filter(CompleteReport.id == report_id).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complete report with ID '{report_id}' not found"
        )
    
    return CompleteReportDetailResponse.from_orm(report)


@router.post("/complete/generate", response_model=GenerateCompleteReportResponse, status_code=status.HTTP_201_CREATED, tags=["reports"])
async def generate_complete_report(
    request: GenerateCompleteReportRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a complete report from a weather report using AI.
    
    This endpoint uses the PDF service to generate a CompleteWeatherReport
    with AI-generated narratives from the raw weather data.
    """
    # Get weather report
    weather_report = db.query(WeatherReport).filter(
        WeatherReport.id == request.weather_report_id
    ).first()
    
    if not weather_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Weather report with ID '{request.weather_report_id}' not found"
        )
    
    # Check if complete report already exists
    existing = db.query(CompleteReport).filter(
        CompleteReport.weather_report_id == request.weather_report_id
    ).first()
    
    if existing and not request.force_regenerate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Complete report already exists for weather report {request.weather_report_id}. Use force_regenerate=true to regenerate."
        )
    
    # Initialize PDF service
    try:
        pdf_service = PDFService()
    except PDFServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PDF service unavailable: {str(e)}"
        )
    
    # Generate complete report
    import time
    start_time = time.time()
    
    try:
        raw_data = weather_report.get_raw_data()
        complete_report_data = pdf_service.generate_complete_report(raw_data)
        
        generation_duration = int(time.time() - start_time)
        
        # Create or update CompleteReport record
        if existing:
            existing.report_data = complete_report_data
            existing.generated_at = datetime.utcnow()
            existing.generation_duration_seconds = generation_duration
            db.commit()
            db.refresh(existing)
            complete_report = existing
        else:
            complete_report = CompleteReport(
                weather_report_id=weather_report.id,
                county_id=weather_report.county_id,
                period_start=weather_report.period_start,
                period_end=weather_report.period_end,
                week_number=weather_report.week_number,
                year=weather_report.year,
                report_data=complete_report_data,
                ai_provider=pdf_service.report_generator.ai_service.provider.value,
                ai_model=getattr(pdf_service.report_generator.ai_service, "_model", None),
                generated_at=datetime.utcnow(),
                generation_duration_seconds=generation_duration,
                is_published=False,
            )
            db.add(complete_report)
            db.commit()
            db.refresh(complete_report)
        
        # Mark weather report as processed
        weather_report.processed = True
        weather_report.processing_error = None
        db.commit()
        
        logger.info(
            "complete_report_generated",
            report_id=complete_report.id,
            weather_report_id=request.weather_report_id,
            duration=generation_duration,
        )
        
        return GenerateCompleteReportResponse(
            complete_report=CompleteReportDetailResponse.from_orm(complete_report),
            message="Complete report generated successfully"
        )
        
    except Exception as e:
        # Mark weather report with error
        weather_report.processing_error = str(e)
        db.commit()
        
        logger.error(
            "complete_report_generation_failed",
            weather_report_id=request.weather_report_id,
            error=str(e),
            exc_info=True,
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate complete report: {str(e)}"
        )

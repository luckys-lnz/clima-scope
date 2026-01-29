"""
PDF Generation Endpoints

Endpoints for generating and managing PDF reports.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from typing import Optional
from datetime import datetime

from ...schemas import (
    PDFReportResponse,
    PDFReportListResponse,
    GeneratePDFRequest,
    GeneratePDFResponse,
    GeneratePDFFromRawRequest,
    MessageResponse,
)
from ...database import get_db
from ...models import CompleteReport, PDFReport, WeatherReport
from ...services import PDFService, PDFServiceError
from ...config import settings
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("", response_model=PDFReportListResponse, tags=["pdf"])
async def list_pdf_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    complete_report_id: Optional[int] = Query(None, description="Filter by complete report ID"),
    db: Session = Depends(get_db),
):
    """
    List all PDF reports.
    """
    query = db.query(PDFReport)
    
    if complete_report_id:
        query = query.filter(PDFReport.complete_report_id == complete_report_id)
    
    total = query.count()
    pdfs = query.order_by(PDFReport.created_at.desc()).offset(skip).limit(limit).all()
    
    return PDFReportListResponse(
        pdfs=[PDFReportResponse.from_orm(p) for p in pdfs],
        total=total,
        page=(skip // limit) + 1,
        page_size=limit,
    )


@router.get("/{pdf_id}", response_model=PDFReportResponse, tags=["pdf"])
async def get_pdf_report(
    pdf_id: int,
    db: Session = Depends(get_db),
):
    """
    Get PDF report metadata by ID.
    """
    pdf_report = db.query(PDFReport).filter(PDFReport.id == pdf_id).first()
    
    if not pdf_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF report with ID '{pdf_id}' not found"
        )
    
    return PDFReportResponse.from_orm(pdf_report)


@router.get("/{pdf_id}/download", tags=["pdf"])
async def download_pdf(
    pdf_id: int,
    db: Session = Depends(get_db),
):
    """
    Download a PDF file by ID.
    """
    pdf_report = db.query(PDFReport).filter(PDFReport.id == pdf_id).first()
    
    if not pdf_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF report with ID '{pdf_id}' not found"
        )
    
    # Check if file exists
    file_path = Path(pdf_report.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF file not found at path: {pdf_report.file_path}"
        )
    
    # Update download statistics
    pdf_report.download_count += 1
    pdf_report.last_downloaded_at = datetime.utcnow()
    db.commit()
    
    logger.info("pdf_downloaded", pdf_id=pdf_id, file_name=pdf_report.file_name)
    
    return FileResponse(
        path=str(file_path),
        filename=pdf_report.file_name,
        media_type="application/pdf",
    )


@router.post("/generate", response_model=GeneratePDFResponse, status_code=status.HTTP_201_CREATED, tags=["pdf"])
async def generate_pdf(
    request: GeneratePDFRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a PDF from a complete report.
    """
    # Get complete report
    complete_report = db.query(CompleteReport).filter(
        CompleteReport.id == request.complete_report_id
    ).first()
    
    if not complete_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complete report with ID '{request.complete_report_id}' not found"
        )
    
    # Initialize PDF service
    try:
        pdf_service = PDFService()
    except PDFServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PDF service unavailable: {str(e)}"
        )
    
    # Generate PDF
    import time
    start_time = time.time()
    
    try:
        report_data = complete_report.get_report_data()
        pdf_path = pdf_service.generate_pdf(report_data, request.output_path)
        
        generation_duration = int(time.time() - start_time)
        
        # Get file size
        file_path_obj = Path(pdf_path)
        file_size = file_path_obj.stat().st_size if file_path_obj.exists() else None
        
        # Create PDFReport record
        pdf_report = PDFReport(
            complete_report_id=complete_report.id,
            file_path=pdf_path,
            file_name=file_path_obj.name,
            file_size_bytes=file_size,
            generated_at=datetime.utcnow(),
            generation_duration_seconds=generation_duration,
            is_available="available",
            download_count=0,
        )
        
        db.add(pdf_report)
        db.commit()
        db.refresh(pdf_report)
        
        logger.info(
            "pdf_generated",
            pdf_id=pdf_report.id,
            complete_report_id=request.complete_report_id,
            file_path=pdf_path,
            duration=generation_duration,
        )
        
        return GeneratePDFResponse(
            pdf_report=PDFReportResponse.from_orm(pdf_report),
            message="PDF generated successfully"
        )
        
    except Exception as e:
        logger.error(
            "pdf_generation_failed",
            complete_report_id=request.complete_report_id,
            error=str(e),
            exc_info=True,
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.post("/generate-from-raw", response_model=GeneratePDFResponse, status_code=status.HTTP_201_CREATED, tags=["pdf"])
async def generate_pdf_from_raw(
    request: GeneratePDFFromRawRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a PDF directly from a weather report.
    
    This endpoint will:
    1. Generate a complete report from the raw weather data (if not already exists)
    2. Generate a PDF from the complete report
    
    This is a convenience endpoint that combines both operations.
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
    
    # Initialize PDF service
    try:
        pdf_service = PDFService()
    except PDFServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PDF service unavailable: {str(e)}"
        )
    
    # Check if complete report exists, if not generate it
    complete_report = db.query(CompleteReport).filter(
        CompleteReport.weather_report_id == request.weather_report_id
    ).first()
    
    import time
    start_time = time.time()
    
    try:
        if not complete_report:
            # Generate complete report first
            raw_data = weather_report.get_raw_data()
            complete_report_data = pdf_service.generate_complete_report(raw_data)
            
            # Create CompleteReport record
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
                is_published=False,
            )
            db.add(complete_report)
            db.commit()
            db.refresh(complete_report)
            
            # Mark weather report as processed
            weather_report.processed = True
            weather_report.processing_error = None
            db.commit()
        
        # Generate PDF
        report_data = complete_report.get_report_data()
        pdf_path = pdf_service.generate_pdf(report_data, request.output_path)
        
        generation_duration = int(time.time() - start_time)
        
        # Get file size
        file_path_obj = Path(pdf_path)
        file_size = file_path_obj.stat().st_size if file_path_obj.exists() else None
        
        # Create PDFReport record
        pdf_report = PDFReport(
            complete_report_id=complete_report.id,
            file_path=pdf_path,
            file_name=file_path_obj.name,
            file_size_bytes=file_size,
            generated_at=datetime.utcnow(),
            generation_duration_seconds=generation_duration,
            is_available="available",
            download_count=0,
        )
        
        db.add(pdf_report)
        db.commit()
        db.refresh(pdf_report)
        
        logger.info(
            "pdf_generated_from_raw",
            pdf_id=pdf_report.id,
            weather_report_id=request.weather_report_id,
            duration=generation_duration,
        )
        
        return GeneratePDFResponse(
            pdf_report=PDFReportResponse.from_orm(pdf_report),
            message="PDF generated successfully from raw weather data"
        )
        
    except Exception as e:
        # Mark weather report with error
        weather_report.processing_error = str(e)
        db.commit()
        
        logger.error(
            "pdf_generation_from_raw_failed",
            weather_report_id=request.weather_report_id,
            error=str(e),
            exc_info=True,
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.delete("/{pdf_id}", response_model=MessageResponse, tags=["pdf"])
async def delete_pdf(
    pdf_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a PDF report and optionally the file.
    
    Note: This only removes the database record. The actual file is not deleted
    to allow for recovery if needed.
    """
    pdf_report = db.query(PDFReport).filter(PDFReport.id == pdf_id).first()
    
    if not pdf_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF report with ID '{pdf_id}' not found"
        )
    
    # Mark as deleted instead of actually deleting
    pdf_report.is_available = "deleted"
    db.commit()
    
    logger.info("pdf_marked_deleted", pdf_id=pdf_id)
    
    return MessageResponse(message=f"PDF report '{pdf_id}' marked as deleted")

"""
Health Check Endpoint

Provides health status and system information.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...schemas import HealthResponse
from ...database import get_db
from ...config import settings
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=HealthResponse, tags=["health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns the status of the API, database connection, and PDF generator.
    """
    # Check database connection
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        database_status = "disconnected"
    
    # Check PDF generator availability
    try:
        from ...services import PDFService
        pdf_service_available = PDFService.is_available()
        pdf_generator_status = "available" if pdf_service_available else "unavailable"
    except Exception as e:
        logger.warning("pdf_generator_check_failed", error=str(e))
        pdf_generator_status = "unknown"
    
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        database=database_status,
        pdf_generator=pdf_generator_status,
    )

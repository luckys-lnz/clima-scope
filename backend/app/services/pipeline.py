"""
Processing Pipeline Service

Orchestrates the full weather report generation pipeline:
1. Validate input JSON
2. Generate AI narratives  
3. Request maps from geospatial service
4. Assemble PDF with maps
5. Store artifacts
6. Notify completion

This is the core orchestration layer that ties together all Person B's services.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from sqlalchemy.orm import Session
from fastapi import Depends
import uuid

from ..utils.logging import get_logger
from .map_storage import MapStorageService, MapVariable
from ..schemas.report import WeatherReportCreate
from ..models import WeatherReport, CompleteReport, PDFReport, County
from ..database import SessionLocal

logger = get_logger(__name__)


class PipelineStage(str, Enum):
    """Pipeline processing stages."""
    VALIDATING = "validating"
    GENERATING_NARRATIVES = "generating_narratives"
    AWAITING_MAPS = "awaiting_maps"
    GENERATING_PDF = "generating_pdf"
    STORING_ARTIFACTS = "storing_artifacts"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass


class PipelineExecution:
    """Represents a single pipeline execution."""
    
    def __init__(
        self,
        pipeline_id: str,
        county_id: str,
        period_start: str,
        period_end: str,
        raw_data: Dict[str, Any]
    ):
        self.pipeline_id = pipeline_id
        self.county_id = county_id
        self.period_start = period_start
        self.period_end = period_end
        self.raw_data = raw_data
        
        self.status = PipelineStatus.PENDING
        self.current_stage = PipelineStage.VALIDATING
        self.progress = 0  # 0-100
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
        
        # Output artifacts
        self.weather_report_id: Optional[int] = None
        self.complete_report_id: Optional[int] = None
        self.pdf_report_id: Optional[int] = None
        
        # Stage tracking
        self.stages_completed: List[str] = []
        self.current_stage_started_at: Optional[datetime] = None
    
    def start(self):
        """Mark pipeline as started."""
        self.status = PipelineStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.progress = 0
        logger.info("pipeline_started", pipeline_id=self.pipeline_id, county_id=self.county_id)
    
    def update_stage(self, stage: PipelineStage, progress: int):
        """Update current stage and progress."""
        if self.current_stage != PipelineStage.FAILED:
            self.stages_completed.append(self.current_stage.value)
        
        self.current_stage = stage
        self.current_stage_started_at = datetime.utcnow()
        self.progress = progress
        
        logger.info(
            "pipeline_stage_updated",
            pipeline_id=self.pipeline_id,
            stage=stage.value,
            progress=progress
        )
    
    def complete(self):
        """Mark pipeline as completed."""
        self.status = PipelineStatus.COMPLETED
        self.current_stage = PipelineStage.COMPLETED
        self.progress = 100
        self.completed_at = datetime.utcnow()
        
        duration = (self.completed_at - self.started_at).total_seconds()
        logger.info(
            "pipeline_completed",
            pipeline_id=self.pipeline_id,
            duration_seconds=duration,
            weather_report_id=self.weather_report_id,
            pdf_report_id=self.pdf_report_id
        )
    
    def fail(self, error: str):
        """Mark pipeline as failed."""
        self.status = PipelineStatus.FAILED
        self.current_stage = PipelineStage.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()
        
        logger.error(
            "pipeline_failed",
            pipeline_id=self.pipeline_id,
            error=error,
            stage=self.current_stage.value
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "pipeline_id": self.pipeline_id,
            "county_id": self.county_id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "status": self.status.value,
            "current_stage": self.current_stage.value,
            "progress": self.progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "artifacts": {
                "weather_report_id": self.weather_report_id,
                "complete_report_id": self.complete_report_id,
                "pdf_report_id": self.pdf_report_id
            },
            "stages_completed": self.stages_completed
        }


class PipelineService:
    """Service for orchestrating report generation pipelines."""
    
    def __init__(self):
        """Initialize pipeline service."""
        self.map_storage = MapStorageService()
        
        # In-memory store for active pipelines
        # In production, this would be Redis or database
        self.active_pipelines: Dict[str, PipelineExecution] = {}
    
    def create_pipeline(
        self,
        county_id: str,
        period_start: str,
        period_end: str,
        raw_data: Dict[str, Any]
    ) -> PipelineExecution:
        """
        Create a new pipeline execution.
        
        Args:
            county_id: KNBS county code
            period_start: Period start date
            period_end: Period end date
            raw_data: Raw weather data JSON
            
        Returns:
            PipelineExecution object
        """
        pipeline_id = str(uuid.uuid4())
        
        execution = PipelineExecution(
            pipeline_id=pipeline_id,
            county_id=county_id,
            period_start=period_start,
            period_end=period_end,
            raw_data=raw_data
        )
        
        self.active_pipelines[pipeline_id] = execution
        
        logger.info(
            "pipeline_created",
            pipeline_id=pipeline_id,
            county_id=county_id,
            period=f"{period_start} to {period_end}"
        )
        
        return execution
    
    def get_pipeline(self, pipeline_id: str) -> Optional[PipelineExecution]:
        """Get pipeline execution by ID."""
        return self.active_pipelines.get(pipeline_id)
    
    async def execute_pipeline(self, pipeline_id: str) -> PipelineExecution:
        """
        Execute the full report generation pipeline.
        
        This is the main orchestration method that runs all stages.
        
        Args:
            pipeline_id: Pipeline execution ID
            
        Returns:
            Completed PipelineExecution
            
        Raises:
            PipelineError: If pipeline fails
        """
        execution = self.get_pipeline(pipeline_id)
        if not execution:
            raise PipelineError(f"Pipeline not found: {pipeline_id}")
        
        execution.start()
        
        try:
            # Stage 1: Validate Input (0-10%)
            execution.update_stage(PipelineStage.VALIDATING, 5)
            await self._validate_input(execution)
            execution.update_stage(PipelineStage.VALIDATING, 10)
            
            # Stage 2: Generate AI Narratives (10-40%)
            execution.update_stage(PipelineStage.GENERATING_NARRATIVES, 15)
            await self._generate_narratives(execution)
            execution.update_stage(PipelineStage.GENERATING_NARRATIVES, 40)
            
            # Stage 3: Check for Maps (40-50%)
            execution.update_stage(PipelineStage.AWAITING_MAPS, 45)
            maps_available = await self._check_maps(execution)
            execution.update_stage(PipelineStage.AWAITING_MAPS, 50)
            
            # Stage 4: Generate PDF (50-80%)
            execution.update_stage(PipelineStage.GENERATING_PDF, 55)
            await self._generate_pdf(execution, maps_available)
            execution.update_stage(PipelineStage.GENERATING_PDF, 80)
            
            # Stage 5: Store Artifacts (80-100%)
            execution.update_stage(PipelineStage.STORING_ARTIFACTS, 85)
            await self._store_artifacts(execution)
            execution.update_stage(PipelineStage.STORING_ARTIFACTS, 95)
            
            # Complete
            execution.complete()
            
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            execution.fail(error_msg)
            raise PipelineError(error_msg) from e
        
        return execution
    
    async def _validate_input(self, execution: PipelineExecution):
        """Validate input JSON against schema."""
        try:
            # Basic validation
            required_fields = ['county_id', 'county_name', 'period', 'variables', 'metadata']
            for field in required_fields:
                if field not in execution.raw_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate county exists
            db = SessionLocal()
            try:
                county = db.query(County).filter(County.id == execution.county_id).first()
                if not county:
                    raise ValueError(f"County not found: {execution.county_id}")
            finally:
                db.close()
            
            logger.info("pipeline_validation_passed", pipeline_id=execution.pipeline_id)
            
        except Exception as e:
            logger.error("pipeline_validation_failed", pipeline_id=execution.pipeline_id, error=str(e))
            raise
    
    async def _generate_narratives(self, execution: PipelineExecution):
        """Generate AI-powered narratives from raw data."""
        # Placeholder: In production, this would call the AI service
        # For now, we'll use the raw data as-is
        
        try:
            # Create weather report in database
            db = SessionLocal()
            try:
                weather_report = WeatherReport(
                    county_id=execution.county_id,
                    period_start=execution.period_start,
                    period_end=execution.period_end,
                    raw_data=json.dumps(execution.raw_data),
                    status="processed"
                )
                db.add(weather_report)
                db.commit()
                db.refresh(weather_report)
                
                execution.weather_report_id = weather_report.id
                
                logger.info(
                    "narratives_generated",
                    pipeline_id=execution.pipeline_id,
                    weather_report_id=weather_report.id
                )
            finally:
                db.close()
            
            # Simulate AI processing time
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error("narrative_generation_failed", pipeline_id=execution.pipeline_id, error=str(e))
            raise
    
    async def _check_maps(self, execution: PipelineExecution) -> Dict[str, bool]:
        """Check if maps are available for this report."""
        maps_status = {}
        
        for variable in [MapVariable.RAINFALL, MapVariable.TEMPERATURE, MapVariable.WIND]:
            map_meta = self.map_storage.get_map(
                county_id=execution.county_id,
                variable=variable,
                period_start=execution.period_start,
                period_end=execution.period_end
            )
            maps_status[variable.value] = map_meta is not None
        
        logger.info(
            "maps_checked",
            pipeline_id=execution.pipeline_id,
            maps_status=maps_status
        )
        
        return maps_status
    
    async def _generate_pdf(self, execution: PipelineExecution, maps_available: Dict[str, bool]):
        """Generate PDF report."""
        try:
            # Placeholder: In production, this would call the PDF service
            # For now, just log that we would generate it
            
            logger.info(
                "pdf_generation_initiated",
                pipeline_id=execution.pipeline_id,
                maps_available=maps_available,
                weather_report_id=execution.weather_report_id
            )
            
            # Simulate PDF generation time
            await asyncio.sleep(1.0)
            
            # In production, we'd create a PDFReport entry here
            # For now, just mark as complete
            execution.pdf_report_id = execution.weather_report_id  # Placeholder
            
        except Exception as e:
            logger.error("pdf_generation_failed", pipeline_id=execution.pipeline_id, error=str(e))
            raise
    
    async def _store_artifacts(self, execution: PipelineExecution):
        """Store final artifacts and metadata."""
        try:
            # Placeholder: Store references, update database status, etc.
            logger.info(
                "artifacts_stored",
                pipeline_id=execution.pipeline_id,
                weather_report_id=execution.weather_report_id,
                pdf_report_id=execution.pdf_report_id
            )
            
        except Exception as e:
            logger.error("artifact_storage_failed", pipeline_id=execution.pipeline_id, error=str(e))
            raise
    
    def cancel_pipeline(self, pipeline_id: str) -> bool:
        """
        Cancel a running pipeline.
        
        Args:
            pipeline_id: Pipeline to cancel
            
        Returns:
            True if cancelled, False if not found or already completed
        """
        execution = self.get_pipeline(pipeline_id)
        if not execution:
            return False
        
        if execution.status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED]:
            return False
        
        execution.status = PipelineStatus.CANCELLED
        execution.completed_at = datetime.utcnow()
        
        logger.info("pipeline_cancelled", pipeline_id=pipeline_id)
        
        return True
    
    def list_pipelines(
        self,
        county_id: Optional[str] = None,
        status: Optional[PipelineStatus] = None
    ) -> List[PipelineExecution]:
        """
        List pipeline executions with optional filters.
        
        Args:
            county_id: Filter by county
            status: Filter by status
            
        Returns:
            List of PipelineExecution objects
        """
        pipelines = list(self.active_pipelines.values())
        
        if county_id:
            pipelines = [p for p in pipelines if p.county_id == county_id]
        
        if status:
            pipelines = [p for p in pipelines if p.status == status]
        
        # Sort by started_at (most recent first)
        pipelines.sort(key=lambda p: p.started_at or datetime.min, reverse=True)
        
        return pipelines


def get_pipeline_service(db: Session = Depends(lambda: next(iter([None])))) -> PipelineService:
    """
    Dependency injection helper for PipelineService.
    
    Note: This function is meant to be used with FastAPI's Depends(), but
    the database session must be provided by the endpoint itself due to
    circular import issues.
    
    Usage in endpoints:
        db: Session = Depends(get_db)
        pipeline_service: PipelineService = Depends(lambda: PipelineService(db))
    
    Or simpler, just instantiate directly in the endpoint:
        db: Session = Depends(get_db)
        service = Pipeline Service(db)
    
    Args:
        db: Database session (automatically injected by FastAPI)
        
    Returns:
        Initialized PipelineService instance
    """
    # Import get_db here to avoid circular imports at module level
    from ..database import get_db
    if db is None:
        db = next(get_db())
    return PipelineService(db)

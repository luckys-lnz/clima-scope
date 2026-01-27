"""
PDF Service

Service layer for PDF generation using the pdf_generator package.
Handles integration with AI services and report generation.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from ..config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Try to import pdf_generator
try:
    from pdf_generator.report_generator import ReportGenerator
    from pdf_generator.enhanced_pdf_builder import EnhancedPDFBuilder
    from pdf_generator.ai_service import AIProvider
    PDF_GENERATOR_AVAILABLE = True
except ImportError:
    # Fallback: add to path if not installed as package
    pdf_gen_path = Path(__file__).parent.parent.parent.parent / "pdf_generator"
    if pdf_gen_path.exists():
        sys.path.insert(0, str(pdf_gen_path))
        try:
            from pdf_generator.report_generator import ReportGenerator
            from pdf_generator.enhanced_pdf_builder import EnhancedPDFBuilder
            from pdf_generator.ai_service import AIProvider
            PDF_GENERATOR_AVAILABLE = True
            logger.info("pdf_generator_loaded_from_path", path=str(pdf_gen_path))
        except ImportError as e:
            PDF_GENERATOR_AVAILABLE = False
            logger.error("pdf_generator_import_failed", path=str(pdf_gen_path), error=str(e))
    else:
        PDF_GENERATOR_AVAILABLE = False
        logger.error("pdf_generator_path_not_found", expected_path=str(pdf_gen_path))


class PDFServiceError(Exception):
    """Base exception for PDF service errors."""
    pass


class PDFService:
    """Service for generating PDF reports."""
    
    def __init__(self):
        """Initialize PDF service."""
        if not PDF_GENERATOR_AVAILABLE:
            raise PDFServiceError(
                "PDF generator not available. "
                "Make sure pdf_generator is installed or accessible. "
                f"Expected path: {Path(__file__).parent.parent.parent.parent / 'pdf_generator'}"
            )
        
        # Determine AI provider
        provider_str = settings.AI_PROVIDER.lower()
        if provider_str == "anthropic":
            provider = AIProvider.ANTHROPIC
            api_key = settings.ANTHROPIC_API_KEY
        else:
            provider = AIProvider.OPENAI
            api_key = settings.OPENAI_API_KEY
        
        # Initialize report generator
        try:
            self.report_generator = ReportGenerator(
                ai_provider=provider,
                api_key=api_key if api_key else None
            )
            logger.info(
                "pdf_service_initialized",
                provider=provider.value,
                has_api_key=bool(api_key)
            )
        except Exception as e:
            logger.error("pdf_service_init_failed", error=str(e), exc_info=True)
            raise PDFServiceError(f"Failed to initialize PDF service: {str(e)}") from e
    
    def generate_complete_report(self, raw_weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete weather report from raw data.
        
        Args:
            raw_weather_data: Raw CountyWeatherReport JSON data
            
        Returns:
            CompleteWeatherReport dictionary
            
        Raises:
            PDFServiceError: If report generation fails
        """
        county_name = raw_weather_data.get("county_name", "Unknown")
        logger.info("generating_complete_report", county=county_name)
        
        try:
            report = self.report_generator.generate_complete_report(raw_weather_data)
            logger.info("report_generated_successfully", county=county_name)
            return report
        except Exception as e:
            logger.error(
                "report_generation_failed",
                county=county_name,
                error=str(e),
                exc_info=True
            )
            raise PDFServiceError(f"Failed to generate report: {str(e)}") from e
    
    def generate_pdf(
        self,
        report_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate PDF from complete report data.
        
        Args:
            report_data: CompleteWeatherReport dictionary
            output_path: Optional output path (defaults to PDF_STORAGE_PATH)
            
        Returns:
            Path to generated PDF file
            
        Raises:
            PDFServiceError: If PDF generation fails
        """
        if output_path is None:
            # Generate default path
            county_code = (
                report_data.get("cover_page", {})
                .get("county", {})
                .get("code", "unknown")
            )
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{county_code}_{timestamp}.pdf"
            output_path = str(Path(settings.PDF_STORAGE_PATH) / filename)
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("generating_pdf", output_path=output_path)
        
        try:
            builder = EnhancedPDFBuilder(report_data)
            pdf_path = builder.generate(output_path)
            logger.info("pdf_generated_successfully", path=pdf_path)
            return pdf_path
        except Exception as e:
            logger.error(
                "pdf_generation_failed",
                output_path=output_path,
                error=str(e),
                exc_info=True
            )
            raise PDFServiceError(f"Failed to generate PDF: {str(e)}") from e
    
    def generate_report_and_pdf(
        self,
        raw_weather_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete report and PDF in one call.
        
        This is a convenience method that combines report generation
        and PDF creation in a single operation.
        
        Args:
            raw_weather_data: Raw CountyWeatherReport JSON data
            output_path: Optional PDF output path
            
        Returns:
            Dictionary with:
            - 'report': CompleteWeatherReport dictionary
            - 'pdf_path': Path to generated PDF file
            
        Raises:
            PDFServiceError: If generation fails at any step
        """
        county_name = raw_weather_data.get("county_name", "Unknown")
        logger.info("generating_report_and_pdf", county=county_name)
        
        try:
            # Generate report
            report = self.generate_complete_report(raw_weather_data)
            
            # Generate PDF
            pdf_path = self.generate_pdf(report, output_path)
            
            result = {
                "report": report,
                "pdf_path": pdf_path
            }
            
            logger.info(
                "report_and_pdf_generated",
                county=county_name,
                pdf_path=pdf_path
            )
            
            return result
        except PDFServiceError:
            # Re-raise PDF service errors as-is
            raise
        except Exception as e:
            logger.error(
                "report_and_pdf_generation_failed",
                county=county_name,
                error=str(e),
                exc_info=True
            )
            raise PDFServiceError(
                f"Failed to generate report and PDF: {str(e)}"
            ) from e
    
    @staticmethod
    def is_available() -> bool:
        """
        Check if PDF generator is available.
        
        Returns:
            True if pdf_generator can be imported, False otherwise
        """
        return PDF_GENERATOR_AVAILABLE

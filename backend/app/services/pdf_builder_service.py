"""
PDF Builder Service

Generates PDFs directly from complete report data without AI dependencies.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any, Optional

from ..config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


def _ensure_pdf_generator_path() -> None:
    pdf_path = Path(settings.PDF_GENERATOR_PATH)
    if pdf_path.exists() and str(pdf_path) not in sys.path:
        sys.path.insert(0, str(pdf_path))
        logger.info("pdf_generator_path_added", path=str(pdf_path))


def generate_pdf_from_report(
    report_data: Dict[str, Any],
    output_path: Optional[str] = None,
) -> str:
    """Generate a PDF from a complete report payload."""
    _ensure_pdf_generator_path()

    try:
        from pdf_generator.enhanced_pdf_builder import EnhancedPDFBuilder
    except Exception as exc:
        logger.error("pdf_generator_import_failed", error=str(exc), exc_info=True)
        raise

    if output_path is None:
        output_path = str(Path(settings.PDF_STORAGE_PATH) / "report.pdf")

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    builder = EnhancedPDFBuilder(report_data)
    pdf_path = builder.generate(output_path)
    logger.info("pdf_generated", path=pdf_path)
    return pdf_path


"""
Report Generation Routes

Endpoints for generating PDF reports from UI selections.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

from ...config import settings
from ...schemas import GeneratePDFWithOptionsRequest, GeneratePDFWithOptionsResponse
from ...services.report_template import build_complete_report, load_sample_raw_data
from ...services.pdf_builder_service import generate_pdf_from_report
from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["reports"])


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "county"


@router.post("/generate-pdf", response_model=GeneratePDFWithOptionsResponse)
async def generate_pdf_from_options(payload: GeneratePDFWithOptionsRequest):
    """Generate a PDF report based on UI selections."""
    if not payload.county_id and not payload.county_name:
        raise HTTPException(status_code=400, detail="county_id or county_name is required")

    raw_data = load_sample_raw_data(payload.county_id, payload.county_name)
    county_name = payload.county_name or (raw_data or {}).get("county_name") or "Unknown"
    county_id = payload.county_id or (raw_data or {}).get("county_id") or "00"

    try:
        report_data = build_complete_report(
            county_name=county_name,
            week_number=payload.week_number,
            year=payload.year,
            include_observations=payload.include_observations,
            raw_data=raw_data,
        )
    except Exception as exc:
        logger.error("report_build_failed", error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to build report data") from exc

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    county_slug = _slugify(county_name)
    filename = f"{county_slug}_W{payload.week_number:02d}_{payload.year}_{timestamp}.pdf"
    output_path = str(Path(settings.PDF_STORAGE_PATH) / filename)

    try:
        pdf_path = generate_pdf_from_report(report_data, output_path=output_path)
    except Exception as exc:
        logger.error("pdf_generation_failed", error=str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate PDF") from exc

    pdf_url = f"/storage/pdfs/{Path(pdf_path).name}"

    return GeneratePDFWithOptionsResponse(
        pdf_url=pdf_url,
        filename=Path(pdf_path).name,
        county_id=county_id,
        county_name=county_name,
        week_number=payload.week_number,
        year=payload.year,
        include_observations=payload.include_observations,
        generated_at=datetime.utcnow(),
    )


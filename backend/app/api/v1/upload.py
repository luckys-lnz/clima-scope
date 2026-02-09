"""
Upload API

Endpoints for uploading weather data and related files.
"""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from ...utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["upload"])


@router.post("/weather-data")
async def upload_weather_data(
    file: UploadFile = File(..., description="Weather data file (CSV or JSON)"),
):
    """
    Accept weather data upload (CSV or JSON).
    Returns a message and optional pipeline identifiers for async processing.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    content_type = file.content_type or ""
    if "csv" not in content_type and "json" not in content_type and not (
        file.filename.endswith(".csv") or file.filename.endswith(".json")
    ):
        raise HTTPException(
            status_code=400,
            detail="Unsupported format. Use CSV or JSON.",
        )

    try:
        # Read and validate size (e.g. max 10MB)
        body = await file.read()
        if len(body) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        # TODO: validate content, enqueue pipeline, or persist to storage
        logger.info(
            "weather_data_uploaded",
            filename=file.filename,
            size=len(body),
            content_type=content_type,
        )

        return {
            "message": "Upload received successfully",
            "filename": file.filename,
            "size_bytes": len(body),
            "pipeline_id": None,
            "pipeline_status_url": None,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("weather_data_upload_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Upload failed") from exc

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from datetime import timedelta, datetime
from typing import List
from pathlib import Path
from uuid import UUID

from app.schemas.report import ReportArchiveItem
from app.api.v1.auth import get_current_user
from app.core.supabase import get_db_client
from app.core.config import settings

router = APIRouter(tags=["reports"])


@router.get("", response_model=List[ReportArchiveItem])
async def get_user_reports(user=Depends(get_current_user)):
    """
    Return list of reports for the current user
    """
    db = get_db_client()
    user_id = user.get("id") if isinstance(user, dict) else user.id

    # ---- get user county ----
    user_row = await db.select(
        table="profiles",
        filters={"id": f"eq.{user_id}"},
        columns="county"
    ) or []

    county = user_row[0]["county"] if user_row else "Unknown"

    # ---- get user's reports ----
    rows = await db.select(
        table="generated_reports",
        filters={"user_id": f"eq.{user_id}"},
        columns="id, generation_date, status, file_path"
    ) or []

    # sort newest first
    rows.sort(key=lambda r: r["generation_date"], reverse=True)

    reports: List[ReportArchiveItem] = []

    for r in rows:
        gen_date = r["generation_date"]

        # Convert ISO string to datetime if necessary
        if isinstance(gen_date, str):
            gen_date = datetime.fromisoformat(gen_date.replace("Z", "+00:00"))

        period_start = gen_date + timedelta(days=1)
        period_end = gen_date + timedelta(days=7)

        reports.append(
            ReportArchiveItem(
                id=r["id"],
                county=county,
                generatedAt=gen_date,
                periodStart=period_start.date(),
                periodEnd=period_end.date(),
                status=r["status"],
                pdfUrl=f"/api/v1/reports/download/{r['id']}",  # secure download URL
            )
        )

    return reports

@router.get("/download/{report_id}")
async def download_report(report_id: UUID, user=Depends(get_current_user)):
    db = get_db_client()
    storage = get_storage_client()

    user_id = user.get("id") if isinstance(user, dict) else user.id

    rows = await db.select(
        table="generated_reports",
        filters={"id": f"eq.{report_id}", "user_id": f"eq.{user_id}"},
        columns="file_path"
    ) or []

    if not rows:
        raise HTTPException(status_code=404, detail="Report not found")

    file_path = rows[0]["file_path"]

    if not file_path:
        raise HTTPException(status_code=404, detail="File path missing")

    # fetch file from Supabase Storage using service role key
    file_data = await storage.download_file(file_path)
    if not file_data:
        raise HTTPException(status_code=404, detail="File not found in storage")

    return StreamingResponse(io.BytesIO(file_data), media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="{file_path.split("/")[-1]}"'
    })

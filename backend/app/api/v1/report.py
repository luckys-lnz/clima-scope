from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from datetime import timedelta, datetime
from typing import List
from pathlib import Path
from uuid import UUID
import io

from app.schemas.report import ReportArchiveItem
from app.api.v1.auth import get_current_user
from app.core.supabase import get_supabase_anon
from app.core.config import settings

router = APIRouter(tags=["reports"])


@router.get("", response_model=List[ReportArchiveItem])
async def get_user_reports(user=Depends(get_current_user)):
    """
    Return list of reports for the current user
    """
    supabase = get_supabase_anon()
    user_id = user.id if hasattr(user, "id") else user.get("id")

    # ---- get user county ----
    try:
        profile_response = supabase.table("profiles")\
            .select("county")\
            .eq("id", user_id)\
            .execute()
        
        county = profile_response.data[0]["county"] if profile_response.data else "Unknown"
    except Exception as e:
        print(f"Error fetching user county: {e}")
        county = "Unknown"

    # ---- get user's reports ----
    try:
        reports_response = supabase.table("generated_reports")\
            .select("id, generation_date, status, file_path")\
            .eq("user_id", user_id)\
            .order("generation_date", desc=True)\
            .execute()
        
        rows = reports_response.data or []
    except Exception as e:
        print(f"Error fetching reports: {e}")
        rows = []

    reports: List[ReportArchiveItem] = []

    for r in rows:
        gen_date = r.get("generation_date")
        if not gen_date:
            continue

        # Convert ISO string to datetime if necessary
        if isinstance(gen_date, str):
            try:
                gen_date = datetime.fromisoformat(gen_date.replace("Z", "+00:00"))
            except ValueError:
                # Fallback for different date formats
                gen_date = datetime.now()

        period_start = gen_date + timedelta(days=1)
        period_end = gen_date + timedelta(days=7)

        reports.append(
            ReportArchiveItem(
                id=r["id"],
                county=county,
                generatedAt=gen_date,
                periodStart=period_start.date(),
                periodEnd=period_end.date(),
                status=r.get("status", "completed"),
                pdfUrl=f"/api/v1/reports/download/{r['id']}",  # secure download URL
            )
        )

    return reports


@router.get("/download/{report_id}")
async def download_report(report_id: UUID, user=Depends(get_current_user)):
    # Use anon client - respects RLS policies
    supabase = get_supabase_anon()
    
    user_id = user.id if hasattr(user, "id") else user.get("id")

    # Get report details and verify ownership in one query
    try:
        report_response = supabase.table("generated_reports")\
            .select("file_path")\
            .eq("id", str(report_id))\
            .eq("user_id", user_id)\
            .execute()
        
        rows = report_response.data or []
    except Exception as e:
        print(f"Error fetching report: {e}")
        rows = []

    if not rows:
        raise HTTPException(status_code=404, detail="Report not found")

    file_path = rows[0].get("file_path")
    if not file_path:
        raise HTTPException(status_code=404, detail="File path missing")

    # Download file from Supabase Storage using anon client
    # RLS policies should allow users to read their own files
    try:
        # Extract bucket and path
        # Assuming file_path format: "bucket_name/path/to/file.pdf"
        path_parts = file_path.split("/", 1)
        if len(path_parts) == 2:
            bucket_name = path_parts[0]
            object_path = path_parts[1]
        else:
            # Use default bucket if not specified
            bucket_name = settings.SUPABASE_STORAGE_BUCKET
            object_path = file_path

        # Download file from storage using anon client
        # This will only work if:
        # 1. The bucket has proper RLS policies
        # 2. The user has access to this specific file
        file_data = supabase.storage.from_(bucket_name).download(object_path)
        
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found in storage")
        
        filename = object_path.split("/")[-1]
        
        return StreamingResponse(
            io.BytesIO(file_data), 
            media_type="application/pdf", 
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        print(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}")
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime, date
import uuid
import logging

from app.schemas.upload import UploadResponse
from app.core.supabase import get_supabase_anon
from app.api.v1.subscription_guard import require_paid_or_trial_access
from app.core.config import settings

router = APIRouter(tags=["uploads"])
logger = logging.getLogger(__name__)

BUCKET_NAME = settings.SUPABASE_STORAGE_BUCKET


# -------------------------
# Helpers
# -------------------------
def generate_file_path(user_id: str, file_name: str) -> str:
    """Generate a unique file path for storage"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    name_parts = file_name.rsplit(".", 1)
    base_name = name_parts[0]
    extension = f".{name_parts[1]}" if len(name_parts) > 1 else ""
    safe_file_name = f"{base_name}_{timestamp}_{unique_id}{extension}"
    return f"users/{user_id}/observations/{safe_file_name}"


async def handle_file_upload(
    supabase,
    file: UploadFile,
    user_id: str,
    file_type: str,
    report_week: int,
    report_year: int,
    report_start_at: date,
    report_end_at: date,
) -> UploadResponse:
    """Handle single file upload to storage and database"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Empty filename")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    file_path = generate_file_path(user_id, file.filename)
    upload_id = str(uuid.uuid4())

    # ✅ DB record aligned with schema
    record = {
        "id": upload_id,
        "user_id": user_id,
        "file_name": file.filename,
        "file_path": file_path,
        "file_type": file_type,
        "status": "pending",
        "report_week": report_week,
        "report_year": report_year,
        "report_start_at": report_start_at.isoformat(),
        "report_end_at": report_end_at.isoformat(),
        # uploaded_at uses DB default
    }

    # Insert record first
    try:
        db_response = supabase.table("uploads").insert(record).execute()

        if not db_response.data:
            raise HTTPException(status_code=500, detail="Failed to create upload record")
    except Exception as e:
        logger.error(f"Database insert failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Upload file to storage
    try:
        # Upload to Supabase Storage
        supabase.storage.from_(BUCKET_NAME).upload(
            path=file_path,
            file=content,
            file_options={"content-type": file.content_type or "application/octet-stream"}
        )
    except Exception as e:
        # Clean up database record if storage upload fails
        supabase.table("uploads").delete().eq("id", upload_id).execute()
        logger.error(f"Storage upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {str(e)}")

    return UploadResponse.model_validate(db_response.data[0])


# -------------------------
# POST: Upload files
# -------------------------
@router.post("/", response_model=List[UploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_files(
    file_type: str = Form(...),
    files: List[UploadFile] = File(...),
    # ✅ reporting period fields
    report_week: int = Form(...),
    report_year: int = Form(...),
    report_start_at: date = Form(...),
    report_end_at: date = Form(...),
    user=Depends(require_paid_or_trial_access),
):
    supabase = get_supabase_anon()
    user_id = user.id if hasattr(user, "id") else user.get("id")

    uploaded = []
    errors = []

    for f in files:
        try:
            result = await handle_file_upload(
                supabase,
                f,
                user_id,
                file_type,
                report_week,
                report_year,
                report_start_at,
                report_end_at,
            )
            uploaded.append(result)
        except Exception as e:
            errors.append({"file": f.filename, "error": str(e)})

    if errors and not uploaded:
        raise HTTPException(status_code=400, detail={"errors": errors})

    return uploaded


# -------------------------
# GET: List user uploads
# -------------------------
@router.get("/", response_model=List[UploadResponse])
async def list_uploads(
    user=Depends(require_paid_or_trial_access),
    limit: int = 100,
    offset: int = 0,
):
    supabase = get_supabase_anon()
    user_id = user.id if hasattr(user, "id") else user.get("id")

    try:
        response = supabase.table("uploads")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("uploaded_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()

        return [UploadResponse.model_validate(item) for item in response.data]
    except Exception as e:
        logger.error(f"Error listing uploads: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch uploads")


# -------------------------
# GET: Single upload
# -------------------------
@router.get("/{upload_id}", response_model=UploadResponse)
async def get_upload(upload_id: str, user=Depends(require_paid_or_trial_access)):
    supabase = get_supabase_anon()
    user_id = user.id if hasattr(user, "id") else user.get("id")

    try:
        response = supabase.table("uploads")\
            .select("*")\
            .eq("id", upload_id)\
            .eq("user_id", user_id)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Upload not found")

        return UploadResponse.model_validate(response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch upload")


# -------------------------
# PATCH: Update upload status
# -------------------------
@router.patch("/{upload_id}", response_model=UploadResponse)
async def update_status(
    upload_id: str,
    status: str = Form(...),
    user=Depends(require_paid_or_trial_access),
):
    supabase = get_supabase_anon()
    user_id = user.id if hasattr(user, "id") else user.get("id")

    # Verify ownership first
    try:
        check = supabase.table("uploads")\
            .select("id")\
            .eq("id", upload_id)\
            .eq("user_id", user_id)\
            .execute()

        if not check.data:
            raise HTTPException(status_code=404, detail="Upload not found or access denied")

        # Update status
        response = supabase.table("uploads")\
            .update({"status": status, "updated_at": datetime.utcnow().isoformat()})\
            .eq("id", upload_id)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Upload not found")

        return UploadResponse.model_validate(response.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to update upload")


# -------------------------
# DELETE: Remove upload
# -------------------------
@router.delete("/{upload_id}")
async def delete_upload(upload_id: str, user=Depends(require_paid_or_trial_access)):
    supabase = get_supabase_anon()
    user_id = user.id if hasattr(user, "id") else user.get("id")

    # Get upload details first (verify ownership)
    try:
        uploads = supabase.table("uploads")\
            .select("file_path")\
            .eq("id", upload_id)\
            .eq("user_id", user_id)\
            .execute()

        if not uploads.data:
            raise HTTPException(status_code=404, detail="Upload not found")

        upload = uploads.data[0]
        file_path = upload.get("file_path")

        # Delete from database first
        supabase.table("uploads")\
            .delete()\
            .eq("id", upload_id)\
            .execute()

        # Delete from storage (try even if db delete succeeded)
        if file_path:
            try:
                supabase.storage.from_(BUCKET_NAME).remove([file_path])
            except Exception as e:
                logger.error(f"Storage deletion failed for {file_path}: {e}")
                # Don't fail the request if storage delete fails
                # Could be that file doesn't exist

        return {"success": True, "message": "Upload deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete upload")

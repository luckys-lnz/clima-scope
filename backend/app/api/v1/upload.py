# backend/app/api/v1/upload.py
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import logging

from app.config import settings
from supabase import create_client, Client
from app.schemas.upload import UploadResponse

router = APIRouter(tags=["upload"])
logger = logging.getLogger(__name__)

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY
)

security = HTTPBearer()

# ----------------------------
# Auth dependency
# ----------------------------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    resp = supabase.auth.get_user(token)
    if not resp.user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return resp.user

# ----------------------------
# Upload file route
# ----------------------------
@router.post("/", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    user=Depends(get_current_user),
):
    if file_type != "observations":
        raise HTTPException(400, "Invalid file_type")

    try:
        # -----------------------
        # Create unique filename
        # -----------------------
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = file.filename.replace(" ", "_").replace("/", "_")
        file_path = f"users/{user.id}/inputs/{file_type}/{timestamp}_{safe_name}"

        # -----------------------
        # Upload to Supabase Storage
        # -----------------------
        bucket = settings.SUPABASE_STORAGE_BUCKET
        content = await file.read()
        storage_resp = supabase.storage.from_(bucket).upload(
            file_path,
            content,
            {"content-type": file.content_type},
        )
        if isinstance(storage_resp, dict) and storage_resp.get("error"):
            raise HTTPException(500, f"Storage upload failed: {storage_resp['error']}")

        # -----------------------
        # Insert record into database
        # -----------------------
        db_resp = supabase.table("uploads").insert({
            "user_id": user.id,
            "file_name": file.filename,
            "file_path": file_path,
            "file_type": file_type,
            "status": "pending",
        }).execute()

        # ✅ Check if insert returned data
        if not db_resp.data or len(db_resp.data) == 0:
            raise HTTPException(500, f"Failed to insert upload: {db_resp.data}")

        # -----------------------
        # Return via Pydantic schema
        # -----------------------
        row = db_resp.data[0]
        return UploadResponse(
            id=row["id"],
            file_name=row["file_name"],
            file_type=row["file_type"],
            status=row["status"],
            upload_date=row["upload_date"],
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Upload failed")
        raise HTTPException(500, "Upload failed")

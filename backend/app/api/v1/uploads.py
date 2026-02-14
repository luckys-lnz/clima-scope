from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime
import uuid

from app.schemas.upload import UploadResponse
from app.core.supabase import get_storage_client, get_db_client
from app.api.v1.auth import get_current_user
from app.core.config import settings

router = APIRouter(tags=["uploads"])

# Get client instances
supabase_storage = get_storage_client()
supabase_db = get_db_client()
BUCKET_NAME = settings.SUPABASE_STORAGE_BUCKET

# -------------------------
# Helpers
# -------------------------
def generate_file_path(user_id: str, file_name: str) -> str:
    """Generate unique file path to avoid collisions"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    name_parts = file_name.rsplit('.', 1)
    base_name = name_parts[0]
    extension = f".{name_parts[1]}" if len(name_parts) > 1 else ""
    safe_file_name = f"{base_name}_{timestamp}_{unique_id}{extension}"
    return f"users/{user_id}/observations/{safe_file_name}"

async def handle_file_upload(
    file: UploadFile, 
    user_id: str, 
    file_type: str
) -> UploadResponse:
    """Uploads a file to Supabase storage and creates a record"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Empty filename")
    
    content = await file.read()
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    
    file_path = generate_file_path(user_id, file.filename)
    
    # 1️⃣ FIRST: Create database record - ONLY columns that exist in your table
    record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "file_name": file.filename,
        "file_path": file_path,
        "file_type": file_type,
        "upload_date": datetime.utcnow().isoformat(),
        "status": "pending"
        # REMOVED: public_url, file_size - these columns don't exist in your table
    }
    
    db_response = await supabase_db.insert("uploads", record)
    
    if not db_response:
        raise HTTPException(status_code=500, detail="Failed to create upload record")
    
    # 2️⃣ THEN: Upload to Supabase Storage
    await supabase_storage.upload_file(file_path, content)
    
    return UploadResponse.model_validate(db_response[0])

# -------------------------
# POST: Upload files
# -------------------------
@router.post("/", response_model=List[UploadResponse], status_code=status.HTTP_201_CREATED)
async def upload_files(
    file_type: str = Form(...),
    files: List[UploadFile] = File(...),
    user = Depends(get_current_user)
):
    """Upload one or multiple files to Supabase storage"""
    
    user_id = user.get("id")
    uploaded = []
    errors = []
    
    for f in files:
        try:
            result = await handle_file_upload(f, user_id, file_type)
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
    user = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    """List user's uploads"""
    user_id = user.get("id")
    
    response = await supabase_db.select(
        "uploads", 
        filters={
            "user_id": f"eq.{user_id}",
            "order": "upload_date.desc",
            "limit": str(limit),
            "offset": str(offset)
        }
    )
    
    return [UploadResponse.model_validate(item) for item in response]

# -------------------------
# GET: Single upload
# -------------------------
@router.get("/{upload_id}", response_model=UploadResponse)
async def get_upload(
    upload_id: str,
    user = Depends(get_current_user)
):
    """Get specific upload"""
    user_id = user.get("id")
    
    response = await supabase_db.select(
        "uploads", 
        filters={
            "id": f"eq.{upload_id}",
            "user_id": f"eq.{user_id}"
        }
    )
    
    if not response:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    return UploadResponse.model_validate(response[0])

# -------------------------
# PATCH: Update upload status
# -------------------------
@router.patch("/{upload_id}", response_model=UploadResponse)
async def update_status(
    upload_id: str,
    status: str = Form(...),
    user = Depends(get_current_user)
):
    """Update upload status"""
    user_id = user.get("id")
    
    # Verify ownership
    check = await supabase_db.select(
        "uploads", 
        filters={
            "id": f"eq.{upload_id}",
            "user_id": f"eq.{user_id}"
        }
    )
    
    if not check:
        raise HTTPException(status_code=404, detail="Upload not found or access denied")
    
    response = await supabase_db.update(
        "uploads",
        {"status": status},
        filters={"id": f"eq.{upload_id}"}
    )
    
    if not response:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    return UploadResponse.model_validate(response[0])

# -------------------------
# DELETE: Remove upload
# -------------------------
@router.delete("/{upload_id}")
async def delete_upload(
    upload_id: str,
    user = Depends(get_current_user)
):
    """Delete upload and associated file"""
    user_id = user.get("id")
    
    # Get upload details
    uploads = await supabase_db.select(
        "uploads", 
        filters={
            "id": f"eq.{upload_id}",
            "user_id": f"eq.{user_id}"
        }
    )
    
    if not uploads:
        raise HTTPException(status_code=404, detail="Upload not found")
    
    upload = uploads[0]
    
    # Delete from database first
    await supabase_db.delete(
        "uploads",
        filters={"id": f"eq.{upload_id}"}
    )
    
    # Then delete from storage
    try:
        await supabase_storage.delete_file(upload['file_path'])
    except Exception as e:
        print(f"Storage deletion failed: {e}")
    
    return {"success": True, "message": "Upload deleted successfully"}

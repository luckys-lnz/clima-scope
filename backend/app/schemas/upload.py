# backend/app/schemas/upload.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class UploadResponse(BaseModel):
    id: UUID
    file_name: str
    file_type: str
    status: str
    upload_date: datetime

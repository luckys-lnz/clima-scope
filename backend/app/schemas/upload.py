# backend/app/schemas/upload.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UploadResponse(BaseModel):
    id: str
    user_id: str
    file_name: str
    file_path: str
    file_type: str
    upload_date: datetime
    status: str

    class Config:
        orm_mode = True

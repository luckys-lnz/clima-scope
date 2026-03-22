# backend/app/schemas/upload.py

from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional


class UploadResponse(BaseModel):
    id: str
    user_id: str
    file_name: str
    file_path: str
    file_type: Optional[str] = None
    uploaded_at: datetime
    status: str

    # reporting period
    report_start_at: Optional[date] = None
    report_end_at: Optional[date] = None
    report_week: Optional[int] = None
    report_year: Optional[int] = None

    class Config:
        orm_mode = True

from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional
from datetime import datetime


class SharedFileResponse(BaseModel):
    id: UUID
    file_name: str
    file_type: str
    upload_date: datetime


class UserSettingsResponse(BaseModel):
    pdf_template_id: Optional[UUID]


class SettingsResponse(BaseModel):
    shapefile_name: str
    shapefile_path: str
    templates: List[SharedFileResponse]
    user_settings: UserSettingsResponse


class UpdateSettingsRequest(BaseModel):
    pdf_template_id: UUID
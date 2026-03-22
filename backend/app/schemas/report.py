from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Literal


class ReportArchiveItem(BaseModel):
    id: UUID
    county: str
    generatedAt: datetime
    periodStart: date
    periodEnd: date
    status: Literal["pending", "success", "failed"]
    pdfUrl: str

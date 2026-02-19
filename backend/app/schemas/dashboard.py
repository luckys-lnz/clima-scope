from pydantic import BaseModel
from typing import Optional


class DashboardStats(BaseModel):
    countiesProcessed: int
    totalCounties: int
    allReportsDone: int
    lastGeneration: Optional[str]
    userReportsGenerated: int


class DashboardOverviewResponse(BaseModel):
    stats: DashboardStats
    workflow_step: Optional[str]

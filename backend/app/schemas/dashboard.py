from pydantic import BaseModel
from typing import Optional


class DashboardStats(BaseModel):
    countiesProcessed: int
    totalCounties: int
    allReportsDone: int
    lastGeneration: Optional[str]
    userReportsGenerated: int


class DashboardReportWindow(BaseModel):
    week: int
    year: int
    start: str
    end: str


class DashboardWorkflowProgress(BaseModel):
    stage: str
    status: str
    message: str
    created_at: str


class DashboardOverviewResponse(BaseModel):
    stats: DashboardStats
    workflow_step: Optional[str]
    current_window: DashboardReportWindow
    workflow_progress: Optional[DashboardWorkflowProgress] = None

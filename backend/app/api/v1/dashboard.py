from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.api.v1.auth import get_current_user
from app.core.supabase import get_db_client
from app.schemas.dashboard import DashboardOverviewResponse

router = APIRouter(tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(user=Depends(get_current_user)):
    db = get_db_client()

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    # --------------------------------------------------
    # USER COUNTY
    # --------------------------------------------------
    profile = await db.select(
        table="profiles",
        filters={"id": f"eq.{user_id}"},
        columns="county"
    ) or []

    county = profile[0]["county"] if profile else None

    # --------------------------------------------------
    # USER REPORTS
    # --------------------------------------------------
    user_reports = await db.select(
        table="generated_reports",
        filters={"user_id": f"eq.{user_id}"},
        columns="generation_date"
    ) or []

    user_reports_generated = len(user_reports)

    last_generation = max(
        (r["generation_date"] for r in user_reports),
        default=None
    )

    # --------------------------------------------------
    # ALL REPORTS
    # --------------------------------------------------
    all_reports = await db.select(
        table="generated_reports",
        columns="id"
    ) or []

    all_reports_done = len(all_reports)

    # --------------------------------------------------
    # COUNTIES PROCESSED
    # --------------------------------------------------
    all_profiles = await db.select(
        table="profiles",
        columns="county"
    ) or []

    counties_processed = len(set(p["county"] for p in all_profiles if p.get("county")))

    # --------------------------------------------------
    # WORKFLOW STEP (latest this week)
    # --------------------------------------------------
    workflows = await db.select(
        table="workflow_status",
        filters={"user_id": f"eq.{user_id}"},
        columns="uploaded,aggregated,mapped,generated,completed,updated_at"
    ) or []

    workflow_step = None
    if workflows:
        # Sort in Python by updated_at descending
        workflows_sorted = sorted(
            workflows,
            key=lambda x: x.get("updated_at") or datetime.min,
            reverse=True
        )
        latest = workflows_sorted[0]

        # Determine step based on booleans
        if latest.get("completed"):
            workflow_step = "completed"
        elif latest.get("generated"):
            workflow_step = "generated"
        elif latest.get("mapped"):
            workflow_step = "mapped"
        elif latest.get("aggregated"):
            workflow_step = "aggregated"
        elif latest.get("uploaded"):
            workflow_step = "uploaded"
        else:
            workflow_step = "started"

    return DashboardOverviewResponse(
        stats={
            "countiesProcessed": counties_processed,
            "totalCounties": 47,  # static or configurable
            "allReportsDone": all_reports_done,
            "lastGeneration": last_generation,
            "userReportsGenerated": user_reports_generated,
        },
        workflow_step=workflow_step,
    )

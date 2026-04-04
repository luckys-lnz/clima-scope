from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Optional

from app.api.v1.auth import get_current_user
from app.core.supabase import get_supabase_admin, get_supabase_anon
from app.schemas.dashboard import DashboardOverviewResponse
from app.services.profile_service import fetch_profile_for_user
from app.utils.report_date import get_current_weekly_report_window

router = APIRouter(tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(user=Depends(get_current_user)):
    supabase = get_supabase_anon()
    supabase_admin = get_supabase_admin()

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user_id = user.id if hasattr(user, "id") else user.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found")

    # --------------------------------------------------
    # USER COUNTY
    # --------------------------------------------------
    profile = fetch_profile_for_user(supabase_admin, user)
    county = profile.get("county") if profile else None

    # --------------------------------------------------
    # USER REPORTS
    # --------------------------------------------------
    try:
        user_reports_response = supabase.table("generated_reports")\
            .select("generated_at")\
            .eq("user_id", user_id)\
            .execute()
        
        user_reports = user_reports_response.data or []
        user_reports_generated = len(user_reports)

        last_generation = None
        if user_reports:
            # Sort by generated_at descending
            sorted_reports = sorted(
                user_reports,
                key=lambda x: x.get("generated_at", ""),
                reverse=True
            )
            last_generation = sorted_reports[0].get("generated_at")
    except Exception as e:
        print(f"Error fetching user reports: {e}")
        user_reports_generated = 0
        last_generation = None

    # --------------------------------------------------
    # ALL REPORTS
    # --------------------------------------------------
    try:
        all_reports_response = supabase.table("generated_reports")\
            .select("id", count="exact")\
            .execute()
        
        all_reports_done = all_reports_response.count if hasattr(all_reports_response, 'count') else len(all_reports_response.data or [])
    except Exception as e:
        print(f"Error fetching all reports: {e}")
        all_reports_done = 0

    # --------------------------------------------------
    # COUNTIES PROCESSED
    # --------------------------------------------------
    try:
        all_profiles_response = supabase.table("profiles")\
            .select("county")\
            .not_.is_("county", "null")\
            .execute()
        
        counties_processed = len(set(p["county"] for p in all_profiles_response.data if p.get("county")))
    except Exception as e:
        print(f"Error fetching counties: {e}")
        counties_processed = 0

    # --------------------------------------------------
    # WORKFLOW STEP (CURRENT REPORT WINDOW ONLY)
    # --------------------------------------------------
    workflow_step: Optional[str] = None
    workflow_progress = None
    current_window = get_current_weekly_report_window(datetime.now())
    
    try:
        workflows_response = supabase.table("workflow_status")\
            .select(
                "id,uploaded,aggregated,mapped,generated,completed,"
                "updated_at,generated_report_id"
            )\
            .eq("user_id", user_id)\
            .order("updated_at", desc=True)\
            .limit(1)\
            .execute()
        
        if workflows_response.data:
            latest = workflows_response.data[0]

            # Determine step based on current schema booleans
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

            workflow_status_id = latest.get("id")
            if workflow_status_id is not None:
                logs_response = (
                    supabase.table("workflow_logs")
                    .select("stage,status,message,created_at")
                    .eq("workflow_status_id", workflow_status_id)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )
                if logs_response.data:
                    workflow_progress = logs_response.data[0]

            # Fallback: infer step from latest log stage if flags are still all false.
            if workflow_step is None and workflow_progress:
                stage = str(workflow_progress.get("stage") or "").lower()
                status = str(workflow_progress.get("status") or "").lower()
                if stage in {"validate_inputs", "observation_context"}:
                    workflow_step = "uploaded"
                elif stage in {"generate_maps", "map_context"}:
                    workflow_step = "mapped"
                elif stage in {"generate_narration", "generate_pdf", "store_report"}:
                    workflow_step = "generated"
                elif stage == "report_generation" and status in {"in_progress", "info"}:
                    workflow_step = "generated"
                elif stage in {"workflow_complete", "report_generation"} and status in {"success", "completed"}:
                    workflow_step = "completed"
                else:
                    # If we have any workflow log but flags are unset, treat process as started.
                    workflow_step = "uploaded"
    except Exception as e:
        print(f"Error fetching workflow: {e}")
        workflow_step = None
        workflow_progress = None

    return DashboardOverviewResponse(
        stats={
            "countiesProcessed": counties_processed,
            "totalCounties": 47,  # static or configurable
            "allReportsDone": all_reports_done,
            "lastGeneration": last_generation,
            "userReportsGenerated": user_reports_generated,
        },
        workflow_step=workflow_step,
        current_window={
            "week": current_window.week,
            "year": current_window.year,
            "start": current_window.start.date().isoformat(),
            "end": current_window.end.date().isoformat(),
        },
        workflow_progress=workflow_progress,
    )

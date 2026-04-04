from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from datetime import timedelta, datetime
from typing import List
from uuid import UUID
import io
import json
import re
import pandas as pd

from app.schemas.report import ReportArchiveItem
from app.api.v1.auth import get_current_user
from app.core.supabase import get_supabase_admin, get_supabase_anon
from app.core.config import settings
from app.services.narration_service import summarize_observation_data, generate_report_narration
from app.services.open_meteo_service import fetch_daily_forecast, centroid_from_rows
from app.services.profile_service import fetch_profile_for_user

router = APIRouter(tags=["reports"])


def _resolve_column(columns, candidates):
    lowered = {str(col).strip().lower(): str(col) for col in columns}
    for candidate in candidates:
        key = candidate.lower()
        if key in lowered:
            return lowered[key]
    for candidate in candidates:
        key = candidate.lower()
        for lower_name, original in lowered.items():
            if key in lower_name:
                return original
    return None


def _extract_centroid_from_observation_csv(csv_bytes: bytes):
    try:
        df = pd.read_csv(io.BytesIO(csv_bytes))
    except Exception:
        return None

    lat_col = _resolve_column(df.columns, ["lat", "latitude", "y"])
    lon_col = _resolve_column(df.columns, ["lon", "lng", "long", "longitude", "x"])
    if not lat_col or not lon_col:
        return None

    latitudes = pd.to_numeric(df[lat_col], errors="coerce").dropna().tolist()
    longitudes = pd.to_numeric(df[lon_col], errors="coerce").dropna().tolist()
    if not latitudes or not longitudes:
        return None

    lat, lon = centroid_from_rows(latitudes, longitudes)
    return {"lat": float(lat), "lon": float(lon)}


def _extract_numeric_values(text: str) -> List[float]:
    if not text:
        return []
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(text))]


def _format_range(values: List[float]) -> str:
    if not values:
        return ""
    return f"{min(values):.0f}–{max(values):.0f}"


def _summarize_morning_conditions(rows: List[str]) -> str:
    if not rows:
        return "cloudy mornings with sunny intervals"
    bucket = {"sunny": 0, "cloudy": 0, "rain": 0}
    for row in rows:
        text = str(row or "").lower()
        if any(word in text for word in ["rain", "showers", "drizzle", "storm"]):
            bucket["rain"] += 1
        elif any(word in text for word in ["cloud", "overcast"]):
            bucket["cloudy"] += 1
        elif any(word in text for word in ["sun", "clear"]):
            bucket["sunny"] += 1
    if bucket["rain"] >= max(bucket["cloudy"], bucket["sunny"]):
        return "cloudy mornings with light showers"
    if bucket["cloudy"] >= bucket["sunny"]:
        return "cloudy mornings with sunny intervals"
    return "mostly sunny mornings"


def _build_weekly_narrative_summary(report_data: dict, fallback_text: str) -> str:
    sub_counties = (report_data or {}).get("sub_counties") or []
    if not sub_counties:
        return fallback_text or ""

    max_values: List[float] = []
    min_values: List[float] = []
    wind_values: List[float] = []
    morning_values: List[str] = []
    for sub in sub_counties:
        forecast = sub.get("forecast") or {}
        for _, day_rows in forecast.items():
            max_values += _extract_numeric_values(day_rows.get("Maximum temperature", ""))
            min_values += _extract_numeric_values(day_rows.get("Minimum temperature", ""))
            wind_values += _extract_numeric_values(day_rows.get("Winds", ""))
            morning_values.append(str(day_rows.get("Morning", "")))

    max_range = _format_range(max_values) or "30–34"
    min_range = _format_range(min_values) or "21–25"
    wind_range = _format_range(wind_values) or "10–25"
    morning_phrase = _summarize_morning_conditions(morning_values)

    lines = [
        f"• The county will generally experience {morning_phrase} through the week, with mostly dry conditions across all sub-counties. Light showers may occur in a few places.",
        f"• Maximum/Daytime temperatures are expected to range from {max_range}°C.",
        f"• Minimum/Night temperatures are expected to range from {min_range}°C.",
        f"• Moderate to strong Northeasterly (NE) to East-Northeasterly (ENE) winds ({wind_range} knots) are expected throughout the week.",
        "• Marine users are strongly advised to exercise caution the rest of the week.",
        "• Any significant change in the forecast will be shared in your WhatsApp groups.",
    ]
    return "\n".join(lines)


def _build_forecast_summary_from_report_data(report_data: dict) -> dict:
    sub_counties = (report_data or {}).get("sub_counties") or []
    if not sub_counties:
        return {}

    max_values: List[float] = []
    min_values: List[float] = []
    wind_values: List[float] = []
    rain_values_by_day: dict[str, float] = {}

    for sub in sub_counties:
        forecast = sub.get("forecast") or {}
        for day_label, day_rows in forecast.items():
            max_values += _extract_numeric_values(day_rows.get("Maximum temperature", ""))
            min_values += _extract_numeric_values(day_rows.get("Minimum temperature", ""))
            wind_values += _extract_numeric_values(day_rows.get("Winds", ""))
            rain_values = _extract_numeric_values(day_rows.get("Rainfall distribution", ""))
            if rain_values:
                rain_values_by_day[day_label] = rain_values_by_day.get(day_label, 0.0) + sum(rain_values)

    mean_temperature = None
    if max_values and min_values:
        mean_temperature = round((sum(max_values) / len(max_values) + sum(min_values) / len(min_values)) / 2.0, 2)
    elif max_values:
        mean_temperature = round(sum(max_values) / len(max_values), 2)
    elif min_values:
        mean_temperature = round(sum(min_values) / len(min_values), 2)

    max_wind_speed = round(max(wind_values), 2) if wind_values else None
    # "Total Rainfall" card should show average daily rainfall across the 7-day window.
    rainfall_sum = (
        round(sum(rain_values_by_day.values()) / len(rain_values_by_day), 2)
        if rain_values_by_day
        else None
    )

    return {
        "mean_temperature": mean_temperature,
        "max_wind_speed": max_wind_speed,
        "rainfall_sum": rainfall_sum,
    }


@router.get("", response_model=List[ReportArchiveItem])
async def get_user_reports(user=Depends(get_current_user)):
    """
    Return list of reports for the current user
    """
    supabase = get_supabase_anon()
    supabase_admin = get_supabase_admin()
    user_id = user.id if hasattr(user, "id") else user.get("id")

    profile = fetch_profile_for_user(supabase_admin, user)
    county = profile.get("county") or "Unknown"

    # ---- get user's reports ----
    try:
        reports_response = supabase.table("generated_reports")\
            .select("id, generated_at, status, file_path")\
            .eq("user_id", user_id)\
            .order("generated_at", desc=True)\
            .execute()
        
        rows = reports_response.data or []
    except Exception as e:
        print(f"Error fetching reports: {e}")
        rows = []

    reports: List[ReportArchiveItem] = []

    for r in rows:
        gen_date = r.get("generated_at")
        if not gen_date:
            continue

        # Convert ISO string to datetime if necessary
        if isinstance(gen_date, str):
            try:
                gen_date = datetime.fromisoformat(gen_date.replace("Z", "+00:00"))
            except ValueError:
                # Fallback for different date formats
                gen_date = datetime.now()

        period_start = gen_date + timedelta(days=1)
        period_end = gen_date + timedelta(days=7)

        reports.append(
            ReportArchiveItem(
                id=r["id"],
                county=county,
                generatedAt=gen_date,
                periodStart=period_start.date(),
                periodEnd=period_end.date(),
                status=r.get("status", "completed"),
                pdfUrl=f"/api/v1/reports/download/{r['id']}",  # secure download URL
            )
        )

    return reports


@router.get("/detail/{report_id}")
async def get_report_detail(report_id: UUID, user=Depends(get_current_user)):
    """
    Return dynamic detail payload for a specific generated report.
    """
    supabase = get_supabase_anon()
    supabase_admin = get_supabase_admin()
    user_id = user.id if hasattr(user, "id") else user.get("id")

    try:
        report_response = supabase.table("generated_reports")\
            .select("id,status,generated_at,file_path,observation_file_id")\
            .eq("id", str(report_id))\
            .eq("user_id", user_id)\
            .limit(1)\
            .execute()
        report_rows = report_response.data or []
    except Exception as e:
        print(f"Error fetching report detail: {e}")
        report_rows = []

    if not report_rows:
        # Graceful fallback for stale/deleted report IDs from cached UI state.
        try:
            latest_response = (
                supabase.table("generated_reports")
                .select("id,status,generated_at,file_path,observation_file_id")
                .eq("user_id", user_id)
                .order("generated_at", desc=True)
                .limit(1)
                .execute()
            )
            report_rows = latest_response.data or []
        except Exception as e:
            print(f"Error fetching latest report fallback: {e}")
            report_rows = []

    if not report_rows:
        raise HTTPException(status_code=404, detail="Report not found")

    report = report_rows[0]
    observation = None
    maps = []
    workflow_logs = []
    observation_summary = {}
    forecast_summary = {}
    ai_narration = {}
    observation_bytes = None
    snapshot_data = None
    weekly_narrative_summary = ""

    # Prefer immutable snapshot captured at report-generation time.
    try:
        snapshot_path = f"users/{user_id}/report_snapshots/{report.get('id')}.json"
        snapshot_bytes = supabase.storage.from_(settings.SUPABASE_STORAGE_BUCKET).download(snapshot_path)
        if snapshot_bytes:
            snapshot_data = json.loads(snapshot_bytes.decode("utf-8"))
            observation_summary = snapshot_data.get("observation_summary") or {}
            ai_narration = snapshot_data.get("ai_narration") or {}
            maps = snapshot_data.get("maps") or []
            forecast_summary = _build_forecast_summary_from_report_data(
                snapshot_data.get("report_data") or {}
            )
            weekly_narrative_summary = _build_weekly_narrative_summary(
                snapshot_data.get("report_data") or {},
                ai_narration.get("weekly_summary_text", ""),
            )
            if ai_narration:
                ai_narration["weekly_summary_text"] = weekly_narrative_summary or ai_narration.get("weekly_summary_text", "")
    except Exception:
        snapshot_data = None

    observation_file_id = report.get("observation_file_id")
    if observation_file_id:
        try:
            obs_response = supabase.table("uploads")\
                .select("id,file_name,file_path,status,report_week,report_year,report_start_at,report_end_at")\
                .eq("id", str(observation_file_id))\
                .limit(1)\
                .execute()
            obs_rows = obs_response.data or []
            if obs_rows:
                observation = obs_rows[0]

                file_path = observation.get("file_path")
                if file_path:
                    file_bytes = supabase.storage.from_(settings.SUPABASE_STORAGE_BUCKET).download(file_path)
                    observation_bytes = file_bytes
                    if not snapshot_data:
                        observation_summary = summarize_observation_data(
                            csv_bytes=file_bytes,
                            requested_variables=["rainfall", "tmin", "tmax", "wind"],
                        )
        except Exception as e:
            print(f"Error fetching observation detail: {e}")

    if not observation and snapshot_data:
        period = snapshot_data.get("period") or {}
        observation = {
            "id": str(snapshot_data.get("observation_file_id") or ""),
            "file_name": "snapshot",
            "status": "snapshot",
            "report_week": period.get("week"),
            "report_year": period.get("year"),
            "report_start_at": period.get("start"),
            "report_end_at": period.get("end"),
        }

    if (not maps) and observation and observation.get("report_week") and observation.get("report_year"):
        try:
            maps_response = supabase.table("generated_maps")\
                .select("variable,map_url,created_at")\
                .eq("user_id", user_id)\
                .eq("report_week", observation["report_week"])\
                .eq("report_year", observation["report_year"])\
                .order("created_at", desc=True)\
                .execute()
            maps = maps_response.data or []
        except Exception as e:
            print(f"Error fetching report maps detail: {e}")

    # Resolve county for centroid fallback and narration context.
    county_name = "County"
    profile = fetch_profile_for_user(supabase_admin, user)
    if profile.get("county"):
        county_name = str(profile["county"])

    # Open-Meteo forecast summary fallback for missing observation variables.
    # Skip recomputation when an immutable snapshot exists.
    if not snapshot_data:
        try:
            # 1) Determine forecast period; fallback to generated_at-derived weekly window.
            period_start = observation.get("report_start_at") if observation else None
            period_end = observation.get("report_end_at") if observation else None
            if not period_start or not period_end:
                generated_at = report.get("generated_at")
                if generated_at:
                    gen_dt = (
                        datetime.fromisoformat(str(generated_at).replace("Z", "+00:00"))
                        if isinstance(generated_at, str)
                        else generated_at
                    )
                else:
                    gen_dt = datetime.utcnow()
                period_start = (gen_dt + timedelta(days=1)).date().isoformat()
                period_end = (gen_dt + timedelta(days=7)).date().isoformat()

            # 2) Determine centroid from station CSV; fallback to Kenya centroid.
            centroid = _extract_centroid_from_observation_csv(observation_bytes) if observation_bytes else None
            if not centroid:
                # Conservative fallback so forecast-derived stats still compute.
                centroid = {"lat": -0.0236, "lon": 37.9062}

            daily = fetch_daily_forecast(
                latitude=centroid["lat"],
                longitude=centroid["lon"],
                report_start_at=str(period_start),
                report_end_at=str(period_end),
            )

            tmax = pd.to_numeric(pd.Series(daily.get("temperature_2m_max", [])), errors="coerce").dropna()
            tmin = pd.to_numeric(pd.Series(daily.get("temperature_2m_min", [])), errors="coerce").dropna()
            wind = pd.to_numeric(pd.Series(daily.get("wind_speed_10m_max", [])), errors="coerce").dropna()
            gust = pd.to_numeric(pd.Series(daily.get("wind_gusts_10m_max", [])), errors="coerce").dropna()
            rain = pd.to_numeric(pd.Series(daily.get("precipitation_sum", [])), errors="coerce").dropna()

            mean_temp = None
            if not tmax.empty and not tmin.empty:
                mean_temp = round(float(((tmax + tmin) / 2.0).mean()), 2)
            elif not tmax.empty:
                mean_temp = round(float(tmax.mean()), 2)
            elif not tmin.empty:
                mean_temp = round(float(tmin.mean()), 2)

            max_wind = None
            if not wind.empty:
                max_wind = round(float(wind.max()), 2)
            elif not gust.empty:
                max_wind = round(float(gust.max()), 2)

            forecast_summary = {
                "mean_temperature": mean_temp,
                "max_wind_speed": max_wind,
                # Keep response key for compatibility, but value is average daily rainfall.
                "rainfall_sum": (round(float(rain.mean()), 2) if not rain.empty else None),
            }
        except Exception as e:
            print(f"Error fetching Open-Meteo forecast summary: {e}")

    # AI narration for dynamic county detail summary.
    if not snapshot_data:
        try:
            wk = int(observation.get("report_week")) if observation and observation.get("report_week") is not None else 0
            yr = int(observation.get("report_year")) if observation and observation.get("report_year") is not None else datetime.utcnow().year
            report_start = observation.get("report_start_at") if observation else None
            report_end = observation.get("report_end_at") if observation else None

            if report_start and report_end:
                map_context = [
                    {"variable": m.get("variable", ""), "map_url": m.get("map_url", "")}
                    for m in maps
                ]
                ai_narration = await generate_report_narration(
                    county_name=county_name,
                    week_number=wk,
                    year=yr,
                    report_start_at=str(report_start),
                    report_end_at=str(report_end),
                    selected_variables=["rainfall", "tmin", "tmax", "wind"],
                    observation_summary=observation_summary or {},
                    map_context=map_context,
                )
                weekly_narrative_summary = _build_weekly_narrative_summary(
                    {"sub_counties": []},
                    ai_narration.get("weekly_summary_text", ""),
                )
        except Exception as e:
            print(f"Error generating AI narration for report detail: {e}")

    try:
        ws_response = supabase.table("workflow_status")\
            .select("id")\
            .eq("generated_report_id", str(report_id))\
            .order("updated_at", desc=True)\
            .limit(1)\
            .execute()
        ws_rows = ws_response.data or []
        if ws_rows:
            workflow_status_id = ws_rows[0]["id"]
            logs_response = supabase.table("workflow_logs")\
                .select("stage,status,message,created_at")\
                .eq("workflow_status_id", workflow_status_id)\
                .order("created_at", desc=True)\
                .limit(20)\
                .execute()
            workflow_logs = logs_response.data or []
    except Exception as e:
        print(f"Error fetching report workflow detail: {e}")

    return {
        "report": {
            "id": report.get("id"),
            "status": report.get("status"),
            "generated_at": report.get("generated_at"),
            "file_path": report.get("file_path"),
            "pdf_url": f"/api/v1/reports/download/{report.get('id')}",
        },
        "observation": observation,
        "observation_summary": observation_summary,
        "forecast_summary": forecast_summary,
        "ai_narration": ai_narration,
        "weekly_narrative_summary": weekly_narrative_summary or ai_narration.get("weekly_summary_text", ""),
        "maps": maps,
        "workflow_logs": workflow_logs,
        "snapshot_used": bool(snapshot_data),
    }


@router.get("/download/{report_id}")
async def download_report(report_id: UUID, user=Depends(get_current_user)):
    # Use anon client - respects RLS policies
    supabase = get_supabase_anon()
    
    user_id = user.id if hasattr(user, "id") else user.get("id")

    # Get report details and verify ownership in one query
    try:
        report_response = supabase.table("generated_reports")\
            .select("file_path")\
            .eq("id", str(report_id))\
            .eq("user_id", user_id)\
            .execute()
        
        rows = report_response.data or []
    except Exception as e:
        print(f"Error fetching report: {e}")
        rows = []

    if not rows:
        raise HTTPException(status_code=404, detail="Report not found")

    file_path = rows[0].get("file_path")
    if not file_path:
        raise HTTPException(status_code=404, detail="File path missing")

    # Download file from Supabase Storage using anon client
    # RLS policies should allow users to read their own files
    try:
        # Extract bucket and path
        # Assuming file_path format: "bucket_name/path/to/file.pdf"
        path_parts = file_path.split("/", 1)
        if len(path_parts) == 2:
            bucket_name = path_parts[0]
            object_path = path_parts[1]
        else:
            # Use default bucket if not specified
            bucket_name = settings.SUPABASE_STORAGE_BUCKET
            object_path = file_path

        # Download file from storage using anon client
        # This will only work if:
        # 1. The bucket has proper RLS policies
        # 2. The user has access to this specific file
        file_data = supabase.storage.from_(bucket_name).download(object_path)
        
        if not file_data:
            raise HTTPException(status_code=404, detail="File not found in storage")
        
        filename = object_path.split("/")[-1]
        
        return StreamingResponse(
            io.BytesIO(file_data), 
            media_type="application/pdf", 
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        print(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=f"File download failed: {str(e)}")

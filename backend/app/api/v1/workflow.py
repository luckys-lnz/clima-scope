from app.utils.geospatial_compat import ensure_fiona_path
from fastapi import APIRouter, HTTPException, Depends, Query
import pandas as pd
import numpy as np
import io
import json
import logging
import os
import tempfile
import uuid
import asyncio
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.core.supabase import get_supabase_anon, get_supabase_admin
from app.api.v1.auth import get_current_user
from app.schemas.workflow import (
    ValidationRequest,
    ValidationResponse,
    ReportPeriod,
    ReportGenerationRequest,
    ReportGenerationResponse,
)
from app.core.config import settings
from app.utils.map_generator import create_weather_map
from app.utils.map_settings import DEFAULT_MAP_SETTINGS, sanitize_map_settings
from app.utils.pdf_renderer import generate_weekly_forecast_pdf
from app.services.narration_service import (
    generate_report_narration,
    summarize_observation_data,
)
from app.services.open_meteo_service import (
    fetch_daily_forecast,
    centroid_from_rows,
)
from app.services.profile_service import fetch_profile_for_user
from app.services.station_data_service import (
    fetch_aggregated_station_csv_bytes,
    fetch_open_meteo_two_week_observations_csv,
    get_full_year_window_from_previous_day,
)
from app.services.weather_history_service import (
    fetch_historical_weather_csv_bytes,
    fetch_recent_station_weather_csv_bytes,
)
import re

router = APIRouter(tags=["Workflow"])
logger = logging.getLogger(__name__)

# Get bucket name from settings
BUCKET_NAME = settings.SUPABASE_STORAGE_BUCKET
BACKGROUND_REPORT_TASKS: Dict[str, asyncio.Task] = {}


def _resolve_column(columns, candidates):
    lowered = {str(col).strip().lower(): str(col) for col in columns}
    normalized = {
        re.sub(r"[^a-z0-9]+", "", str(col).strip().lower()): str(col)
        for col in columns
    }
    for candidate in candidates:
        key = candidate.lower()
        if key in lowered:
            return lowered[key]
        norm_key = re.sub(r"[^a-z0-9]+", "", key)
        if norm_key in normalized:
            return normalized[norm_key]
    for candidate in candidates:
        key = candidate.lower()
        norm_key = re.sub(r"[^a-z0-9]+", "", key)
        for lower_name, original in lowered.items():
            if key in lower_name:
                return original
            norm_name = re.sub(r"[^a-z0-9]+", "", lower_name)
            if norm_key and norm_key in norm_name:
                return original
    return None


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def _get_personal_email(user: Any, profile: Dict[str, Any]) -> Optional[str]:
    profile_email = profile.get("email")
    if isinstance(profile_email, str) and profile_email.strip():
        return profile_email.strip()

    if hasattr(user, "email"):
        user_email = getattr(user, "email")
        if isinstance(user_email, str) and user_email.strip():
            return user_email.strip()

    if isinstance(user, dict):
        user_email = user.get("email")
        if isinstance(user_email, str) and user_email.strip():
            return user_email.strip()

    return None


def _missing_required_profile_fields(user: Any, profile: Dict[str, Any]) -> List[str]:
    personal_email = _get_personal_email(user, profile)
    work_email = profile.get("signoff_email")

    required_fields = [
        ("Title", profile.get("prefix") or profile.get("title")),
        ("Full Name", profile.get("full_name")),
        ("Job Title", profile.get("job_title") or profile.get("title")),
        ("Phone", profile.get("phone")),
        ("County", profile.get("county")),
        ("Personal Email", personal_email),
        ("Work Email", work_email),
        ("Station Name", profile.get("station_name")),
        ("Station Address", profile.get("station_address")),
    ]

    return [label for label, value in required_fields if _is_blank(value)]


def _format_wards_phrase(wards: List[str]) -> str:
    cleaned = [str(w).strip() for w in wards if str(w).strip()]
    if not cleaned:
        return "N/A Ward"
    if len(cleaned) == 1:
        return f"{cleaned[0]} Ward"
    if len(cleaned) == 2:
        return f"{cleaned[0]} and {cleaned[1]} Ward"
    return f"{', '.join(cleaned[:-1])} and {cleaned[-1]} Ward"


def _load_subcounty_ward_map(
    supabase_admin,
    county_name: str,
    bucket_name: str,
) -> List[Dict[str, Any]]:
    """
    Build sub-county -> wards mapping from the uploaded shapefile components.
    Returns a list of {"sub_county": str, "wards": List[str], "centroid": {"lat": float, "lon": float}}.
    """
    temp_shapefile_dir = None
    try:
        shapefile_records = (
            supabase_admin.table("shared_files")
            .select("file_name,file_path")
            .in_("file_type", ["shapefile", "shapefiles"])
            .execute()
        )
        components = shapefile_records.data or []
        if not components:
            return []

        temp_shapefile_dir = tempfile.mkdtemp(prefix="report_shapefile_")
        local_shapefile_path = None

        for component in components:
            file_name = component.get("file_name")
            file_path = component.get("file_path")
            if not file_name or not file_path:
                continue
            file_data = supabase_admin.storage.from_(bucket_name).download(file_path)
            local_path = os.path.join(temp_shapefile_dir, file_name)
            with open(local_path, "wb") as f:
                f.write(file_data)
            if file_name.lower().endswith(".shp"):
                local_shapefile_path = local_path

        if not local_shapefile_path:
            return []

        ensure_fiona_path()
        import geopandas as gpd

        wards_gdf = gpd.read_file(local_shapefile_path)
        county_col = _resolve_column(wards_gdf.columns, ["county", "county_name", "adm1_name"])
        subcounty_col = _resolve_column(
            wards_gdf.columns,
            ["sub_county", "subcounty", "const", "constituency", "adm2_name"],
        )
        ward_col = _resolve_column(wards_gdf.columns, ["ward", "ward_name", "adm3_name", "name"])

        if not county_col or not subcounty_col or not ward_col:
            return []

        county_rows = wards_gdf[
            wards_gdf[county_col].astype(str).str.strip().str.lower() == county_name.strip().lower()
        ].copy()
        if county_rows.empty:
            return []

        mapping: Dict[str, set] = {}
        centroids: Dict[str, Dict[str, float]] = {}
        for _, row in county_rows.iterrows():
            subcounty = str(row[subcounty_col]).strip()
            ward = str(row[ward_col]).strip()
            if not subcounty or not ward or subcounty.lower() == "nan" or ward.lower() == "nan":
                continue
            mapping.setdefault(subcounty, set()).add(ward)

        for subcounty in mapping.keys():
            sub_rows = county_rows[county_rows[subcounty_col].astype(str).str.strip() == subcounty]
            if sub_rows.empty:
                continue
            geom = sub_rows.unary_union
            if geom is None or geom.is_empty:
                continue
            centroid = geom.centroid
            centroids[subcounty] = {"lat": float(centroid.y), "lon": float(centroid.x)}

        result: List[Dict[str, Any]] = []
        for subcounty in sorted(mapping.keys(), key=lambda x: x.lower()):
            result.append(
                {
                    "sub_county": subcounty,
                    "wards": sorted(mapping[subcounty], key=lambda x: x.lower()),
                    "centroid": centroids.get(subcounty),
                }
            )
        return result
    except Exception as e:
        print(f"⚠️ Failed to load sub-county/ward mapping from shapefile: {e}")
        return []
    finally:
        if temp_shapefile_dir and os.path.exists(temp_shapefile_dir):
            import shutil

            shutil.rmtree(temp_shapefile_dir)


def _deg_to_compass(value: Optional[float]) -> str:
    if value is None:
        return "Variable"
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    idx = int((float(value) + 11.25) // 22.5) % 16
    return directions[idx]


def _weather_phrase_from_code(code: Optional[float], period: str) -> str:
    if code is None:
        return "N/A"
    code_int = int(code)
    if code_int in {0, 1}:
        return "Sunny intervals" if period != "night" else "Clear night sky"
    if code_int in {2, 3}:
        return "Cloudy with sunny intervals" if period != "night" else "Partly cloudy night sky"
    if code_int in {45, 48}:
        return "Misty conditions"
    if code_int in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}:
        return "Sunny intervals and light showers" if period != "night" else "Light showers possible"
    if code_int in {71, 73, 75, 77, 85, 86}:
        return "Cool with possible snowfall"
    if code_int in {95, 96, 99}:
        return "Showers with thunderstorms possible"
    return "Cloudy with sunny intervals"


def _build_rows_from_daily(
    daily_payload: Dict[str, List],
    report_dates: List[str],
    day_labels: List[str],
) -> Dict[str, Dict[str, str]]:
    dates = [str(d) for d in (daily_payload.get("time", []) or [])]
    index_by_date = {dt: idx for idx, dt in enumerate(dates)}

    def _at(key: str, idx: int) -> Optional[float]:
        arr = daily_payload.get(key, []) or []
        if idx < 0 or idx >= len(arr):
            return None
        value = arr[idx]
        return None if value is None else float(value)

    rows: Dict[str, Dict[str, str]] = {}
    for iso_date, label in zip(report_dates, day_labels):
        idx = index_by_date.get(iso_date, -1)
        code = _at("weather_code", idx)
        rain = _at("precipitation_sum", idx)
        pop = _at("precipitation_probability_max", idx)
        tmax = _at("temperature_2m_max", idx)
        tmin = _at("temperature_2m_min", idx)
        wind = _at("wind_speed_10m_max", idx)
        gust = _at("wind_gusts_10m_max", idx)
        wind_dir = _at("wind_direction_10m_dominant", idx)

        if rain is None:
            rain_text = "N/A"
        elif pop is None:
            rain_text = f"{rain:.1f} mm"
        elif pop < 35:
            rain_text = "Showers possible over few places"
        elif pop < 70:
            rain_text = "Showers expected over several places"
        else:
            rain_text = "Showers expected over most places"

        if wind is None and gust is None:
            wind_text = "N/A"
        else:
            wind_kts = int(round((wind or 0) * 0.539957))
            gust_kts = int(round((gust or wind or 0) * 0.539957))
            low_kts = min(wind_kts, gust_kts)
            high_kts = max(wind_kts, gust_kts)
            wind_text = f"{_deg_to_compass(wind_dir)} winds {low_kts}-{high_kts} knots"

        rows[label] = {
            "Morning": _weather_phrase_from_code(code, "morning"),
            "Afternoon": _weather_phrase_from_code(code, "afternoon"),
            "Night": _weather_phrase_from_code(code, "night"),
            "Rainfall distribution": rain_text,
            "Maximum temperature": f"{int(round(tmax))}℃" if tmax is not None else "N/A",
            "Minimum temperature": f"{int(round(tmin))}℃" if tmin is not None else "N/A",
            "Winds": wind_text,
        }

    return rows


def _extract_centroid_from_observation_csv(csv_bytes: bytes) -> Optional[Dict[str, float]]:
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


def _build_prepared_csv_frames(df: pd.DataFrame) -> Dict[str, Any]:
    lat_col = _resolve_column(df.columns, ["lat", "latitude", "y"])
    lon_col = _resolve_column(df.columns, ["lon", "lng", "long", "longitude", "x"])
    if not lat_col or not lon_col:
        raise ValueError("Observation CSV must contain latitude and longitude columns.")

    rain_col = _resolve_column(df.columns, ["rainfall", "rain", "precipitation", "precip", "rr"])
    tmin_col = _resolve_column(df.columns, ["tmin", "min_temp", "minimum_temperature", "tn"])
    tmax_col = _resolve_column(df.columns, ["tmax", "max_temp", "maximum_temperature", "tx"])
    station_col = _resolve_column(df.columns, ["station", "station_name", "name", "code"])

    station_frame = pd.DataFrame(
        {
            "lat": pd.to_numeric(df[lat_col], errors="coerce"),
            "lon": pd.to_numeric(df[lon_col], errors="coerce"),
            "station_name": (
                df[station_col].astype(str).str.strip()
                if station_col
                else pd.Series([f"Station {i+1}" for i in range(len(df))], index=df.index)
            ),
            "rainfall": (
                pd.to_numeric(df[rain_col], errors="coerce")
                if rain_col
                else pd.Series([None] * len(df), index=df.index)
            ),
            "tmin": (
                pd.to_numeric(df[tmin_col], errors="coerce")
                if tmin_col
                else pd.Series([None] * len(df), index=df.index)
            ),
            "tmax": (
                pd.to_numeric(df[tmax_col], errors="coerce")
                if tmax_col
                else pd.Series([None] * len(df), index=df.index)
            ),
        }
    )
    station_frame = station_frame.dropna(subset=["lat", "lon"]).copy()
    if station_frame.empty:
        raise ValueError("No valid rows after normalizing latitude and longitude.")

    # Historical rows are aggregated per station-location so rainfall uses cumulative totals.
    station_frame = (
        station_frame.groupby(["station_name", "lat", "lon"], as_index=False)
        .agg(
            rainfall=("rainfall", lambda s: s.sum(min_count=1)),
            tmin=("tmin", "mean"),
            tmax=("tmax", "mean"),
        )
        .sort_values(["station_name", "lat", "lon"])
        .reset_index(drop=True)
    )

    map_frame = station_frame.rename(
        columns={
            "lat": "Lat",
            "lon": "Lon",
            "rainfall": "Rain",
            "tmin": "Tmin",
            "tmax": "Tmax",
        }
    )[["Lat", "Lon", "Rain", "Tmin", "Tmax"]]

    # Keep one point per coordinate in map input while preserving rainfall totals.
    map_frame = (
        map_frame.groupby(["Lat", "Lon"], as_index=False)
        .agg(
            Rain=("Rain", lambda s: s.sum(min_count=1)),
            Tmin=("Tmin", "mean"),
            Tmax=("Tmax", "mean"),
        )
        .sort_values(["Lat", "Lon"])
        .reset_index(drop=True)
    )

    variables: List[str] = []
    if map_frame["Rain"].notna().any():
        variables.append("rainfall")
    if map_frame["Tmin"].notna().any():
        variables.append("tmin")
    if map_frame["Tmax"].notna().any():
        variables.append("tmax")

    return {
        "station_frame": station_frame,
        "map_frame": map_frame,
        "variables": variables,
    }




def _build_recent_station_frame(
    *,
    county_name: str,
    report_start_at: str,
    supabase_admin,
) -> pd.DataFrame:
    """
    Resolve recent 14-day station behavior used to correct the 1-year historical baseline.
    Priority:
    1) daily_weather station/upload/observation rows (recent station reality)
    2) Open-Meteo 14-day archive fallback
    """
    recent_bytes = b""
    try:
        recent_bytes, _ = fetch_recent_station_weather_csv_bytes(
            county_identifier=county_name,
            report_start_at=report_start_at,
            supabase_admin=supabase_admin,
        )
    except Exception:
        recent_bytes = b""

    if not recent_bytes:
        try:
            recent_bytes, _ = fetch_open_meteo_two_week_observations_csv(
                county_name=county_name,
                report_start_at=report_start_at,
            )
        except Exception:
            recent_bytes = b""

    if not recent_bytes:
        return pd.DataFrame(columns=["lat", "lon", "recent_rainfall"])

    try:
        recent_df = pd.read_csv(io.BytesIO(recent_bytes))
    except Exception:
        return pd.DataFrame(columns=["lat", "lon", "recent_rainfall"])

    lat_col = _resolve_column(recent_df.columns, ["lat", "latitude", "y"])
    lon_col = _resolve_column(recent_df.columns, ["lon", "lng", "long", "longitude", "x"])
    rain_col = _resolve_column(recent_df.columns, ["rainfall", "rain", "precipitation", "precip", "rr"])
    if not lat_col or not lon_col or not rain_col:
        return pd.DataFrame(columns=["lat", "lon", "recent_rainfall"])

    normalized = pd.DataFrame(
        {
            "lat": pd.to_numeric(recent_df[lat_col], errors="coerce"),
            "lon": pd.to_numeric(recent_df[lon_col], errors="coerce"),
            "recent_rainfall": pd.to_numeric(recent_df[rain_col], errors="coerce"),
        }
    ).dropna(subset=["lat", "lon"])

    if normalized.empty:
        return pd.DataFrame(columns=["lat", "lon", "recent_rainfall"])

    return (
        normalized.groupby(["lat", "lon"], as_index=False)
        .agg(recent_rainfall=("recent_rainfall", lambda s: s.sum(min_count=1)))
        .dropna(subset=["recent_rainfall"])
        .reset_index(drop=True)
    )


def _blend_historical_with_recent(
    map_frame: pd.DataFrame,
    recent_frame: pd.DataFrame,
    recent_weight: float = 0.6,
) -> pd.DataFrame:
    """
    Blend 1-year historical rainfall with nearest-point recent 14-day station rainfall.
    The blended output continues to feed forecast rectification in map_generator.
    """
    output = map_frame.copy()
    if output.empty or "Rain" not in output.columns:
        return output
    if recent_frame.empty:
        return output

    valid_map = output["Rain"].notna()
    if not valid_map.any():
        return output

    hist_vals = output["Rain"].to_numpy(dtype=float)
    map_lat = output["Lat"].to_numpy(dtype=float)
    map_lon = output["Lon"].to_numpy(dtype=float)
    rec_lat = recent_frame["lat"].to_numpy(dtype=float)
    rec_lon = recent_frame["lon"].to_numpy(dtype=float)
    rec_val = recent_frame["recent_rainfall"].to_numpy(dtype=float)
    if len(rec_val) == 0:
        return output

    # Nearest-neighbor mapping from recent station behavior to historical station points.
    dlat = map_lat[:, None] - rec_lat[None, :]
    dlon = map_lon[:, None] - rec_lon[None, :]
    dist2 = (dlat * dlat) + (dlon * dlon)
    nearest_idx = np.argmin(dist2, axis=1)
    mapped_recent = rec_val[nearest_idx]

    w = max(0.0, min(1.0, float(recent_weight)))
    output["RainHistorical"] = output["Rain"]
    output["RainRecent14"] = mapped_recent
    output["Rain"] = (hist_vals * (1.0 - w)) + (mapped_recent * w)
    return output


def _persist_csv_cache_artifact(
    *,
    supabase_admin,
    user_id: str,
    county_name: str,
    report_week: int,
    report_year: int,
    report_start_at: str,
    report_end_at: str,
    cache_type: str,
    file_name: str,
    csv_bytes: bytes,
    source_hash: str,
) -> str:
    storage_path = (
        f"users/{user_id}/cache/"
        f"week_{report_week}_{report_year}/{cache_type}/{file_name}"
    )
    supabase_admin.storage.from_(BUCKET_NAME).upload(
        path=storage_path,
        file=csv_bytes,
        file_options={"content-type": "text/csv", "upsert": "true"},
    )

    # Non-blocking metadata upsert; keep workflow resilient if table isn't available.
    try:
        supabase_admin.table("forecast_cache_files").upsert(
            {
                "user_id": user_id,
                "county_name": county_name,
                "report_week": report_week,
                "report_year": report_year,
                "cache_type": cache_type,
                "file_path": storage_path,
                "source_hash": source_hash,
                "report_start_at": report_start_at,
                "report_end_at": report_end_at,
                "bucket_name": BUCKET_NAME,
                "file_size_bytes": len(csv_bytes),
                "model_version": "workflow-v1",
                "source_version": "step1-prepared",
                "updated_at": datetime.utcnow().isoformat(),
            },
            on_conflict="user_id,county_name,report_year,report_week,cache_type,source_hash",
        ).execute()
    except Exception as exc:
        print(f"⚠️ Failed to write forecast_cache_files metadata: {exc}")

    return storage_path


def _load_cached_map_csv_bytes(
    *,
    supabase_admin,
    user_id: str,
    county_name: str,
    report_week: int,
    report_year: int,
) -> Optional[Dict[str, Any]]:
    try:
        response = (
            supabase_admin.table("forecast_cache_files")
            .select("file_path,bucket_name,updated_at")
            .eq("user_id", user_id)
            .eq("county_name", county_name)
            .eq("report_week", report_week)
            .eq("report_year", report_year)
            .eq("cache_type", "map_input_csv")
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            return None

        row = rows[0]
        file_path = row.get("file_path")
        if not file_path:
            return None
        bucket = row.get("bucket_name") or BUCKET_NAME
        file_bytes = supabase_admin.storage.from_(bucket).download(file_path)
        return {"bytes": file_bytes, "file_path": file_path, "bucket": bucket}
    except Exception as exc:
        print(f"⚠️ Unable to load cached map CSV: {exc}")
        return None


def _load_observation_bytes_with_fallback(
    supabase,
    user_id: str,
    report_week: int,
    report_year: int,
    county_name: str,
    report_start_at: str,
    report_end_at: str,
    persist_auto_upload: bool = False,
    supabase_admin=None,
) -> Dict[str, Any]:
    """
    Observation resolution strategy:
    1) Uploaded observation CSV for the selected week/year
    2) Existing 1-year historical observations from daily_weather
    3) Auto-fetch from TAHMO/KMD aggregated over the full-year window (fallback)
    4) Open-Meteo historical fallback if TAHMO/KMD are unavailable
    """
    upload = (
        supabase.table("uploads")
        .select("id, file_name, file_path")
        .eq("user_id", user_id)
        .eq("file_type", "observations")
        .eq("report_week", report_week)
        .eq("report_year", report_year)
        .order("uploaded_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = upload.data or []
    if rows:
        obs = rows[0]
        file_bytes = supabase.storage.from_(BUCKET_NAME).download(obs["file_path"])
        return {
            "bytes": file_bytes,
            "observation_file_id": obs.get("id"),
            "observation_label": obs.get("file_name", "uploaded_observation.csv"),
            "source_type": "upload",
            "meta": {},
        }

    window_start, window_end = get_full_year_window_from_previous_day(report_start_at)
    try:
        historical_bytes, historical_meta = fetch_historical_weather_csv_bytes(
            county_identifier=county_name,
            window_start=window_start,
            window_end=window_end,
            supabase_admin=supabase_admin,
        )
        if historical_bytes:
            return {
                "bytes": historical_bytes,
                "observation_file_id": None,
                "observation_label": (
                    f"historical_daily_weather_{county_name}_{window_start}_to_{window_end}.csv"
                ),
                "source_type": "historical_daily_weather",
                "meta": historical_meta,
            }
    except Exception as exc:
        print(f"⚠️ Failed to load historical daily_weather baseline: {exc}")

    auto_bytes, meta = fetch_aggregated_station_csv_bytes(
        county_name=county_name,
        report_start_at=report_start_at,
    )
    payload = {
        "bytes": auto_bytes,
        "observation_file_id": None,
        "observation_label": (
            f"auto_station_data_{county_name}_{meta['window_start']}_to_{meta['window_end']}.csv"
        ),
        "source_type": "auto_fetch",
        "meta": meta,
    }
    if not persist_auto_upload or supabase_admin is None:
        return payload

    auto_upload_id = str(uuid.uuid4())
    auto_file_name = payload["observation_label"]
    auto_storage_path = (
        f"users/{user_id}/observations/"
        f"auto_{report_week}_{report_year}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    supabase_admin.storage.from_(BUCKET_NAME).upload(
        path=auto_storage_path,
        file=auto_bytes,
        file_options={"content-type": "text/csv"},
    )
    supabase_admin.table("uploads").insert(
        {
            "id": auto_upload_id,
            "user_id": user_id,
            "file_name": auto_file_name,
            "file_path": auto_storage_path,
            "file_type": "observations",
            "status": "auto_fetched",
            "report_week": report_week,
            "report_year": report_year,
            "report_start_at": report_start_at,
            "report_end_at": report_end_at,
        }
    ).execute()
    payload["observation_file_id"] = auto_upload_id
    payload["source_type"] = "auto_fetch_persisted"
    return payload


def _get_user_county(supabase, user, fallback: str = "Unknown") -> str:
    profile = fetch_profile_for_user(supabase, user)
    county = profile.get("county") if profile else None
    if county:
        return str(county)
    return fallback


def _is_missing_column_error(exc: Exception, column_name: str) -> bool:
    text = str(exc).lower()
    return "does not exist" in text and f".{column_name.lower()}" in text


def get_or_create_workflow_status(
    supabase_admin,
    user_id: str,
    report_week: int,
    report_year: int,
    observation_file_id: Optional[str] = None,
    report_start_at: Optional[str] = None,
    report_end_at: Optional[str] = None,
) -> Optional[int]:
    """Get existing workflow row for period or create a new one."""
    try:
        # Schema-aligned: workflow_status has no report_week/report_year columns.
        existing = (
            supabase_admin.table("workflow_status")
            .select("id")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        if existing.data:
            return existing.data[0]["id"]

        insert_payload: Dict[str, Any] = {
            "user_id": user_id,
            "uploaded": False,
            "aggregated": False,
            "mapped": False,
            "generated": False,
            "completed": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        if observation_file_id:
            insert_payload["observation_file_id"] = observation_file_id

        created = supabase_admin.table("workflow_status").insert(insert_payload).execute()
        rows = created.data or []
        if rows:
            return rows[0]["id"]
    except Exception as exc:
        print(f"⚠️ Failed to get/create workflow_status: {exc}")
    return None


def update_workflow_status_flags(
    supabase_admin,
    workflow_status_id: int,
    flags: Dict[str, Any],
) -> None:
    """Update workflow_status with known schema flags only."""
    allowed_keys = {
        "uploaded",
        "aggregated",
        "mapped",
        "generated",
        "completed",
        "observation_file_id",
        "generated_report_id",
    }
    update_payload = {k: v for k, v in flags.items() if k in allowed_keys}
    if not update_payload:
        return
    update_payload["updated_at"] = datetime.utcnow().isoformat()
    try:
        (
            supabase_admin.table("workflow_status")
            .update(update_payload)
            .eq("id", workflow_status_id)
            .execute()
        )
    except Exception as exc:
        print(f"⚠️ Failed to update workflow_status flags: {exc}")


def append_workflow_log(
    supabase_admin,
    workflow_status_id: Optional[int],
    stage: str,
    status: str,
    message: str,
) -> None:
    """Append a workflow log row; non-blocking on failure."""
    if workflow_status_id is None:
        return
    try:
        supabase_admin.table("workflow_logs").insert(
            {
                "workflow_status_id": workflow_status_id,
                "stage": stage,
                "status": status,
                "message": message,
                "created_at": datetime.utcnow().isoformat(),
            }
        ).execute()
    except Exception as exc:
        print(f"⚠️ Failed to append workflow log: {exc}")

# ===== Map Generation Schemas =====
class MapGenerationRequest(BaseModel):
    county: str
    variables: List[str]
    report_week: int
    report_year: int
    report_start_at: str
    report_end_at: str


class MapOutput(BaseModel):
    variable: str
    map_url: str


class MapGenerationResponse(BaseModel):
    outputs: List[MapOutput]


class AsyncReportStartResponse(BaseModel):
    accepted: bool
    workflow_status_id: Optional[int] = None
    report_week: int
    report_year: int
    message: str


@router.get("/status")
async def get_workflow_status(
    week: Optional[int] = Query(default=None),
    year: Optional[int] = Query(default=None),
    user=Depends(get_current_user),
):
    supabase = get_supabase_anon()
    user_id = user.id if hasattr(user, "id") else user.get("id")

    # Schema-aligned: workflow_status has no report_week/report_year columns.
    # Keep query params for API compatibility, but resolve latest status for user.
    response = (
        supabase.table("workflow_status")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
    )

    rows = response.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="Workflow status not found")
    row = rows[0]
    workflow_status_id = row.get("id")
    if workflow_status_id is not None:
        try:
            logs_response = (
                supabase.table("workflow_logs")
                .select("stage,status,message,created_at")
                .eq("workflow_status_id", workflow_status_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            logs = logs_response.data or []
            row["latest_log"] = logs[0] if logs else None
        except Exception:
            row["latest_log"] = None
    else:
        row["latest_log"] = None
    return row


async def _run_report_generation_background(
    request: ReportGenerationRequest,
    user_payload: Dict[str, Any],
    task_key: str,
):
    try:
        await generate_report(request=request, user=user_payload)
    except Exception as exc:
        logger.exception("background_report_generation_failed", extra={"error": str(exc)})
    finally:
        BACKGROUND_REPORT_TASKS.pop(task_key, None)


@router.post("/generate-report-async", response_model=AsyncReportStartResponse)
async def generate_report_async(
    request: ReportGenerationRequest,
    user=Depends(get_current_user),
):
    """
    Start Step 4 report generation as a background task.
    The task continues server-side even if user navigates to another page.
    """
    supabase_admin = get_supabase_admin()
    user_id = user.id if hasattr(user, "id") else user.get("id")
    user_email = getattr(user, "email", None) or (user.get("email") if isinstance(user, dict) else None)

    workflow_status_id = get_or_create_workflow_status(
        supabase_admin=supabase_admin,
        user_id=user_id,
        report_week=request.week_number,
        report_year=request.year,
        report_start_at=request.report_start_at,
        report_end_at=request.report_end_at,
    )
    if workflow_status_id is not None:
        update_workflow_status_flags(
            supabase_admin=supabase_admin,
            workflow_status_id=workflow_status_id,
            flags={
                "generated": False,
                "completed": False,
                "generated_report_id": None,
            },
        )
        append_workflow_log(
            supabase_admin=supabase_admin,
            workflow_status_id=workflow_status_id,
            stage="report_generation",
            status="in_progress",
            message="Background report generation started",
        )

    task_key = f"{user_id}:{request.week_number}:{request.year}"
    existing = BACKGROUND_REPORT_TASKS.get(task_key)
    if existing and not existing.done():
        return AsyncReportStartResponse(
            accepted=True,
            workflow_status_id=workflow_status_id,
            report_week=request.week_number,
            report_year=request.year,
            message="Report generation is already running in background",
        )

    user_payload = {"id": user_id, "email": user_email}
    BACKGROUND_REPORT_TASKS[task_key] = asyncio.create_task(
        _run_report_generation_background(
            request=request,
            user_payload=user_payload,
            task_key=task_key,
        )
    )

    return AsyncReportStartResponse(
        accepted=True,
        workflow_status_id=workflow_status_id,
        report_week=request.week_number,
        report_year=request.year,
        message="Background report generation started",
    )


# ============================================================================
# STEP 1: VALIDATE INPUTS
# ============================================================================
@router.post("/validate-inputs", response_model=ValidationResponse)
async def validate_inputs(
    request: ValidationRequest,
    user=Depends(get_current_user)
):
    """
    Step 1: Validate observation + shapefile for the SPECIFIED reporting period
    """
    print("\n" + "="*60)
    print("🔍 WORKFLOW VALIDATION STARTED")
    print("="*60)
    
    supabase_admin = get_supabase_admin()
    # Use admin client for server-side validation queries to avoid RLS-based false negatives.
    supabase = supabase_admin
    user_id = user.id if hasattr(user, "id") else user.get("id")
    workflow_status_id: Optional[int] = None

    # Allow validation on any day so operators can regenerate reports
    # or recover workflows mid-week using explicit request dates.
    now = datetime.now()
    if now.weekday() != 0:  # Monday=0
        logger.info(
            "validate_inputs_non_monday_run",
            extra={
                "weekday": now.weekday(),
                "report_start_at": request.report_start_at,
                "report_end_at": request.report_end_at,
            },
        )
    
    print(f"👤 User ID: {user_id}")
    print(f"🪣 Using bucket: {BUCKET_NAME}")
    print(f"📊 Validating for week: {request.report_week}, year: {request.report_year}")
    print(f"📅 Period: {request.report_start_at} to {request.report_end_at}")
    
    # =========================
    # DEBUG: Check ALL user uploads first
    # =========================
    print("\n" + "-"*40)
    print("📋 CHECKING ALL USER UPLOADS")
    print("-"*40)
    
    try:
        all_uploads = supabase.table("uploads")\
            .select("*")\
            .eq("user_id", user_id)\
            .execute()
        
        print(f"📊 Total uploads for user: {len(all_uploads.data)}")
        
        if all_uploads.data:
            print("\n📁 ALL UPLOADS:")
            for i, upload in enumerate(all_uploads.data):
                print(f"  {i+1}. File: {upload.get('file_name')}")
                print(f"     Type: {upload.get('file_type')}")
                print(f"     Week: {upload.get('report_week')}")
                print(f"     Year: {upload.get('report_year')}")
                print(f"     Start: {upload.get('report_start_at')}")
                print(f"     End: {upload.get('report_end_at')}")
                print(f"     ID: {upload.get('id')}")
                print(f"     Path: {upload.get('file_path')}")
                print("     ---")
        else:
            print("❌ No uploads found for this user!")
            
    except Exception as e:
        print(f"❌ Error fetching all uploads: {e}")
    
    # =========================
    # DEBUG: Check observation files only
    # =========================
    print("\n" + "-"*40)
    print("📋 CHECKING OBSERVATION FILES ONLY")
    print("-"*40)
    
    try:
        obs_files = supabase.table("uploads")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("file_type", "observations")\
            .execute()
        
        print(f"📊 Total observation files: {len(obs_files.data)}")
        
        if obs_files.data:
            print("\n📁 OBSERVATION FILES:")
            for i, obs in enumerate(obs_files.data):
                print(f"  {i+1}. File: {obs.get('file_name')}")
                print(f"     Week: {obs.get('report_week')}")
                print(f"     Year: {obs.get('report_year')}")
                print(f"     Start: {obs.get('report_start_at')}")
                print(f"     End: {obs.get('report_end_at')}")
                print("     ---")
        else:
            print("❌ No observation files found!")
            
    except Exception as e:
        print(f"❌ Error fetching observation files: {e}")
    
    # =========================
    # 1️⃣ RESOLVE OBSERVATION DATA (UPLOAD OR AUTO-FETCH)
    # =========================
    print("\n" + "-"*40)
    print(f"🔍 RESOLVING OBSERVATION DATA FOR WEEK {request.report_week}")
    print("-"*40)

    try:
        user_county = _get_user_county(supabase_admin, user, fallback="Unknown")
        obs_payload = _load_observation_bytes_with_fallback(
            supabase=supabase_admin,
            user_id=user_id,
            report_week=request.report_week,
            report_year=request.report_year,
            county_name=user_county,
            report_start_at=request.report_start_at,
            report_end_at=request.report_end_at,
            persist_auto_upload=True,
            supabase_admin=supabase_admin,
        )
        source_type = obs_payload["source_type"]
        print(f"✅ Observation source resolved: {source_type}")
        print(f"📁 Label: {obs_payload['observation_label']}")
        if str(source_type).startswith("auto_fetch"):
            window_start, window_end = get_full_year_window_from_previous_day(
                request.report_start_at
            )
            print(
                f"🧮 Auto-fetch aggregation window: {window_start} to {window_end} "
                "(full year ending previous-day)"
            )
    except Exception as e:
        print(f"❌ Observation resolution failed: {e}")
        workflow_status_id = get_or_create_workflow_status(
            supabase_admin=supabase_admin,
            user_id=user_id,
            report_week=request.report_week,
            report_year=request.report_year,
            report_start_at=request.report_start_at,
            report_end_at=request.report_end_at,
        )
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="validate_inputs",
            status="error",
            message="Validation failed: no observation data from upload or TAHMO/KMD/Open-Meteo auto-fetch",
        )
        raise HTTPException(
            status_code=400,
            detail=(
                f"Validation failed: no observation data for week {request.report_week}, {request.report_year}. "
                "Upload observations or configure TAHMO/KMD/Open-Meteo auto-fetch."
            ),
        )

    observation_file_id = obs_payload.get("observation_file_id")
    workflow_status_id = get_or_create_workflow_status(
        supabase_admin=supabase_admin,
        user_id=user_id,
        report_week=request.report_week,
        report_year=request.report_year,
        observation_file_id=observation_file_id,
        report_start_at=request.report_start_at,
        report_end_at=request.report_end_at,
    )
    append_workflow_log(
        supabase_admin,
        workflow_status_id,
        stage="validate_inputs",
        status="info",
        message="Starting validation for observation and shapefile inputs",
    )
    print(f"\n✅ Using observation data: {obs_payload['observation_label']}")

    # =========================
    # 2️⃣ FIND SHAPEFILE
    # =========================
    print("\n" + "-"*40)
    print("🗺️ LOOKING FOR SHAPEFILE")
    print("-"*40)
    
    try:
        shapes_response = supabase_admin.table("shared_files")\
            .select("id,file_name,file_path,upload_date")\
            .eq("file_type", "shapefile")\
            .order("upload_date", desc=True)\
            .limit(1)\
            .execute()
        
        shapes = shapes_response.data or []
        print(f"📊 Found {len(shapes)} shapefiles")
        
        if shapes:
            print(f"✅ Using shapefile: {shapes[0].get('file_name')}")
        else:
            print("❌ No shapefile found")
            
    except Exception as e:
        print(f"❌ Error fetching shapefiles: {e}")
        shapes = []

    if not shapes:
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="validate_inputs",
            status="error",
            message="Validation failed: shapefile not found",
        )
        raise HTTPException(
            status_code=400,
            detail="Validation failed: no shapefile is available in shared_files. Please upload shapefile components.",
        )

    shp = shapes[0]

    # =========================
    # 3️⃣ LOAD OBSERVATION DATAFRAME
    # =========================
    print("\n" + "-"*40)
    print("⬇️ LOADING OBSERVATION DATA")
    print("-"*40)
    
    try:
        file_data = obs_payload["bytes"]
        print(f"✅ Download successful: {len(file_data)} bytes")
        
        # Read CSV from bytes
        df = pd.read_csv(io.BytesIO(file_data))
        print(f"📊 CSV loaded: {len(df)} rows, {len(df.columns)} columns")
        print(f"📋 Columns: {list(df.columns)}")
        
    except Exception as e:
        print(f"❌ Failed to read observation file: {e}")
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="validate_inputs",
            status="error",
            message="Validation failed: could not read observation file",
        )
        raise HTTPException(status_code=400, detail=f"Failed to read observation file: {str(e)}")

    # =========================
    # 4️⃣ PREPARE CSV ARTIFACTS + DETECT MAP VARIABLES
    # =========================
    print("\n" + "-"*40)
    print("🧮 PREPARING MAP INPUT CSVs")
    print("-"*40)
    prepared_observation_csv_path: Optional[str] = None
    prepared_map_csv_path: Optional[str] = None
    try:
        prepared = _build_prepared_csv_frames(df)
        station_frame = prepared["station_frame"]
        map_frame = prepared["map_frame"]

        # Blend recent 14-day station behavior into the 1-year historical rainfall baseline.
        recent_frame = _build_recent_station_frame(
            county_name=user_county,
            report_start_at=request.report_start_at,
            supabase_admin=supabase_admin,
        )
        map_frame = _blend_historical_with_recent(map_frame, recent_frame)
        found = prepared["variables"]

        if not found:
            raise ValueError(
                "No map-ready variables found after formatting. Need at least one of rainfall, tmin, or tmax."
            )

        station_csv_bytes = station_frame.to_csv(index=False).encode("utf-8")
        map_csv_bytes = map_frame.to_csv(index=False).encode("utf-8")
        source_hash = hashlib.sha256(file_data).hexdigest()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        prepared_observation_csv_path = _persist_csv_cache_artifact(
            supabase_admin=supabase_admin,
            user_id=user_id,
            county_name=user_county,
            report_week=request.report_week,
            report_year=request.report_year,
            report_start_at=request.report_start_at,
            report_end_at=request.report_end_at,
            cache_type="station_observation_csv",
            file_name=f"station_observation_{request.report_year}_{request.report_week}_{timestamp}.csv",
            csv_bytes=station_csv_bytes,
            source_hash=source_hash,
        )
        prepared_map_csv_path = _persist_csv_cache_artifact(
            supabase_admin=supabase_admin,
            user_id=user_id,
            county_name=user_county,
            report_week=request.report_week,
            report_year=request.report_year,
            report_start_at=request.report_start_at,
            report_end_at=request.report_end_at,
            cache_type="map_input_csv",
            file_name=f"map_input_{request.report_year}_{request.report_week}_{timestamp}.csv",
            csv_bytes=map_csv_bytes,
            source_hash=source_hash,
        )

        print(f"✅ Prepared station CSV rows: {len(station_frame)}")
        print(f"✅ Prepared map CSV rows: {len(map_frame)}")
        print(f"✅ Recent station correction points (14 days): {len(recent_frame)}")
        print(f"✅ Map variables detected: {found}")
    except Exception as e:
        print(f"❌ Failed preparing CSV artifacts: {e}")
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="validate_inputs",
            status="error",
            message=f"Validation failed during CSV preparation: {str(e)}",
        )
        raise HTTPException(status_code=400, detail=f"Failed preparing map CSVs: {str(e)}")

    # =========================
    # 5️⃣ UPDATE WORKFLOW STATUS
    # =========================
    print("\n" + "-"*40)
    print("💾 UPDATING WORKFLOW STATUS")
    print("-"*40)
    if workflow_status_id is None:
        workflow_status_id = get_or_create_workflow_status(
            supabase_admin=supabase_admin,
            user_id=user_id,
            report_week=request.report_week,
            report_year=request.report_year,
            observation_file_id=observation_file_id,
            report_start_at=request.report_start_at,
            report_end_at=request.report_end_at,
        )
    if workflow_status_id is not None:
        update_workflow_status_flags(
            supabase_admin=supabase_admin,
            workflow_status_id=workflow_status_id,
            flags={
                "uploaded": True,
                "aggregated": True,
                "observation_file_id": observation_file_id,
            },
        )
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="validate_inputs",
            status="success",
            message=(
                f"Preparation completed: {len(found)} map variable(s) detected; "
                "station and map CSVs created"
            ),
        )
        print("✅ Workflow status updated")

    # =========================
    # 6️⃣ RETURN RESPONSE
    # =========================
    print("\n" + "-"*40)
    print("✅ PREPARATION COMPLETE")
    print("-"*40)
    print(f"📊 Response: {len(found)} variables, {len(df)} source rows")
    print("="*60 + "\n")
    
    return ValidationResponse(
        observation_found=True,
        shapefile_found=True,
        variables=found,
        observation_file=obs_payload["observation_label"],
        shapefile=shp["file_name"],
        report_week=request.report_week,
        report_year=request.report_year,
        report_period=ReportPeriod(
            start=request.report_start_at,
            end=request.report_end_at
        ),
        column_count=len(df.columns),
        row_count=len(df),
        prepared_observation_csv_path=prepared_observation_csv_path,
        prepared_map_csv_path=prepared_map_csv_path,
    )


# ============================================================================
# STEP 3: GENERATE MAPS
# ============================================================================
@router.post("/generate-maps", response_model=MapGenerationResponse)
async def generate_maps(
    request: MapGenerationRequest,
    user=Depends(get_current_user),
):
    """
    Step 3: Generate maps for each selected variable
    """
    print("\n" + "=" * 60)
    print("🗺️ MAP GENERATION STARTED")
    print("=" * 60)

    supabase = get_supabase_anon()
    supabase_admin = get_supabase_admin()
    user_id = user.id if hasattr(user, "id") else user.get("id")
    workflow_status_id: Optional[int] = get_or_create_workflow_status(
        supabase_admin=supabase_admin,
        user_id=user_id,
        report_week=request.report_week,
        report_year=request.report_year,
        report_start_at=request.report_start_at,
        report_end_at=request.report_end_at,
    )
    append_workflow_log(
        supabase_admin,
        workflow_status_id,
        stage="generate_maps",
        status="info",
        message=f"Starting map generation for {len(request.variables)} variable(s)",
    )

    print(f"👤 User ID: {user_id}")
    print(f"📍 County: {request.county}")
    print(f"📊 Variables: {request.variables}")
    print(f"📅 Week: {request.report_week}, Year: {request.report_year}")
    print(f"📅 Period: {request.report_start_at} to {request.report_end_at}")

    # =========================
    # 1. RESOLVE PREPARED MAP CSV (CACHE-FIRST)
    # =========================
    county_for_fetch = (
        request.county
        if request.county and request.county != "—"
        else _get_user_county(supabase_admin, user, fallback="Unknown")
    )
    resolved_map_csv_bytes: Optional[bytes] = None
    try:
        cached_map_csv = _load_cached_map_csv_bytes(
            supabase_admin=supabase_admin,
            user_id=user_id,
            county_name=county_for_fetch,
            report_week=request.report_week,
            report_year=request.report_year,
        )
        if cached_map_csv:
            resolved_map_csv_bytes = cached_map_csv["bytes"]
            print(f"✅ Using cached prepared map CSV: {cached_map_csv['file_path']}")
            append_workflow_log(
                supabase_admin,
                workflow_status_id,
                stage="observation_context",
                status="success",
                message="Using prepared map CSV from cache",
            )
        else:
            obs_payload = _load_observation_bytes_with_fallback(
                supabase=supabase_admin,
                user_id=user_id,
                report_week=request.report_week,
                report_year=request.report_year,
                county_name=county_for_fetch,
                report_start_at=request.report_start_at,
                report_end_at=request.report_end_at,
                persist_auto_upload=True,
                supabase_admin=supabase_admin,
            )
            resolved_map_csv_bytes = obs_payload["bytes"]
            print("⚠️ Prepared map CSV cache miss, using observation CSV directly")
            print(f"✅ Observation source: {obs_payload['source_type']}")
            print(f"✅ Observation label: {obs_payload['observation_label']}")
            if workflow_status_id is not None:
                update_workflow_status_flags(
                    supabase_admin=supabase_admin,
                    workflow_status_id=workflow_status_id,
                    flags={
                        "uploaded": True,
                        "aggregated": True,
                        "observation_file_id": obs_payload.get("observation_file_id"),
                    },
                )
            append_workflow_log(
                supabase_admin,
                workflow_status_id,
                stage="observation_context",
                status="info",
                message="Prepared CSV cache miss; fell back to raw observation CSV",
            )
    except Exception as e:
        print(f"❌ Error resolving map input data: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to resolve map input CSV from cache or observation fallback",
        )

    # =========================
    # 2. GET ALL SHAPEFILE COMPONENTS FROM shared_files
    # =========================
    try:
        shapefile_records = (
            supabase_admin.table("shared_files")
            .select("file_name, file_path")
            .in_("file_type", ["shapefile", "shapefiles"])
            .execute()
        )

        if not shapefile_records.data:
            raise HTTPException(
                status_code=404,
                detail="No shapefile found. Please contact administrator.",
            )

        print(f"\n📁 Found {len(shapefile_records.data)} shapefile components:")
        for comp in shapefile_records.data:
            print(f"   - {comp['file_name']}")

    except Exception as e:
        print(f"❌ Error fetching shapefiles: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch shapefiles")

    # =========================
    # 3. PREPARE MAP INPUT CSV
    # =========================
    temp_csv = None
    try:
        file_data = resolved_map_csv_bytes or b""
        if not file_data:
            raise ValueError("Resolved map CSV is empty")
        print(f"\n✅ Loaded map input data: {len(file_data)} bytes")

        incoming_df = pd.read_csv(io.BytesIO(file_data))
        if all(col in incoming_df.columns for col in ["Lat", "Lon", "Rain"]):
            map_frame = incoming_df.copy()
        else:
            map_frame = _build_prepared_csv_frames(incoming_df)["map_frame"]

        # Ensure rainfall map uses: 1-year historical + recent 14-day station correction.
        if "RainHistorical" not in map_frame.columns or "RainRecent14" not in map_frame.columns:
            recent_frame = _build_recent_station_frame(
                county_name=county_for_fetch,
                report_start_at=request.report_start_at,
                supabase_admin=supabase_admin,
            )
            map_frame = _blend_historical_with_recent(map_frame, recent_frame)
            print(f"✅ Applied recent 14-day correction points: {len(recent_frame)}")

        temp_csv = f"/tmp/weather_data_{user_id}_{request.report_week}.csv"
        map_frame.to_csv(temp_csv, index=False)
        print(f"✅ Saved temp file: {temp_csv}")

    except Exception as e:
        print(f"❌ Error preparing map input CSV: {e}")
        raise HTTPException(status_code=500, detail="Failed to prepare map input CSV")

    # =========================
    # 4. DOWNLOAD ALL SHAPEFILE COMPONENTS
    # =========================
    temp_shapefile_dir = None
    local_shapefile_path = None

    try:
        # Create temp directory for all shapefile components
        temp_shapefile_dir = tempfile.mkdtemp(
            prefix=f"shapefiles_{user_id}_{request.report_week}_"
        )
        print(f"\n✅ Created temp directory: {temp_shapefile_dir}")

        # Download each shapefile component
        for component in shapefile_records.data:
            try:
                file_data = supabase.storage.from_(BUCKET_NAME).download(
                    component["file_path"]
                )

                # Save to temp directory with original filename
                local_path = os.path.join(temp_shapefile_dir, component["file_name"])
                with open(local_path, "wb") as f:
                    f.write(file_data)

                print(f"✅ Downloaded: {component['file_name']}")

                # Store path to .shp file for map generation
                if component["file_name"].endswith(".shp"):
                    local_shapefile_path = local_path

            except Exception as e:
                print(f"⚠️ Failed to download {component['file_name']}: {e}")
                continue

        if not local_shapefile_path:
            raise Exception("No .shp file found in downloaded components")

        print(f"\n✅ Main shapefile: {os.path.basename(local_shapefile_path)}")
        print("✅ All shapefile components downloaded to temp directory")

    except Exception as e:
        print(f"❌ Error downloading shapefile components: {e}")
        # Clean up if error occurs
        if temp_shapefile_dir and os.path.exists(temp_shapefile_dir):
            import shutil

            shutil.rmtree(temp_shapefile_dir)
        raise HTTPException(
            status_code=500, detail=f"Failed to download shapefile: {str(e)}"
        )

    # =========================
    # 5. LOAD USER MAP SETTINGS
    # =========================
    map_settings = dict(DEFAULT_MAP_SETTINGS)
    try:
        user_settings_response = (
            supabase_admin.table("user_settings")
            .select(
                "show_constituencies, show_wards, "
                "show_constituency_labels, show_ward_labels, "
                "constituency_label_font_size, ward_label_font_size, "
                "constituency_border_color, constituency_border_width, constituency_border_style, "
                "ward_border_color, ward_border_width, ward_border_style"
            )
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        user_settings_results = user_settings_response.data or []
        if user_settings_results:
            map_settings = sanitize_map_settings(user_settings_results[0])
    except Exception as e:
        print(f"⚠️ Failed to load user map settings: {e}")

    # =========================
    # 6. VARIABLE MAPPING
    # =========================
    var_map = {
        "rainfall": "Rain",
        "tmin": "Tmin",
        "tmax": "Tmax",
    }

    # =========================
    # 7. GENERATE MAPS FOR EACH VARIABLE
    # =========================
    outputs: List[MapOutput] = []

    for variable in request.variables:
        col_name = var_map.get(variable)
        if not col_name:
            print(f"⚠️ Unknown variable: {variable}, skipping")
            continue

        print(f"\n{'=' * 50}")
        print(f"🔄 Generating {variable} map...")
        print(f"{'=' * 50}")

        try:
            image_bytes, filename = create_weather_map(
                county_name=(
                    request.county
                    if request.county != "—"
                    else ("County" if variable == "rainfall" else None)
                ),
                variable=col_name,
                data_file=temp_csv,
                shapefile_path=local_shapefile_path,
                map_settings=map_settings,
                report_start_at=request.report_start_at,
                report_end_at=request.report_end_at,
                title_period_label=f"{request.report_start_at} to {request.report_end_at}",
            )

            print(f"✅ Map generated: {filename} ({len(image_bytes)} bytes)")

            # Create storage path
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            storage_path = (
                f"users/{user_id}/maps/"
                f"week_{request.report_week}_{request.report_year}/{variable}_{timestamp}.png"
            )

            # Upload to Supabase Storage
            supabase_admin.storage.from_(BUCKET_NAME).upload(
                path=storage_path,
                file=image_bytes,
                file_options={"content-type": "image/png"},
            )
            print(f"✅ Uploaded to storage: {storage_path}")

            # ========== URL GENERATION ==========
            map_url = None

            # Method 1: Signed URL
            try:
                signed_result = supabase_admin.storage.from_(BUCKET_NAME).create_signed_url(
                    storage_path,
                    expires_in=604800,  # 1 week in seconds
                )
                map_url = signed_result["signedURL"]
                print("✅ Generated signed URL (expires in 1 week)")
            except Exception as e:
                print(f"⚠️ Signed URL failed: {e}")

                # Method 2: Public URL
                try:
                    map_url = supabase_admin.storage.from_(BUCKET_NAME).get_public_url(
                        storage_path
                    )
                    print("✅ Generated public URL")
                except Exception as e2:
                    print(f"⚠️ Public URL failed: {e2}")

                    # Method 3: Manual construction as last resort
                    try:
                        project_id = (
                            settings.SUPABASE_URL.replace("https://", "").split(".")[0]
                        )
                        map_url = (
                            f"https://{project_id}.supabase.co/storage/v1/"
                            f"object/public/{BUCKET_NAME}/{storage_path}"
                        )
                        print("✅ Manually constructed URL")
                    except Exception as e3:
                        print(f"❌ All URL methods failed: {e3}")
                        raise Exception(
                            "Could not generate accessible URL for map"
                        )

            # Save record to generated_maps table
            map_record = {
                "user_id": user_id,
                "workflow_status_id": workflow_status_id,
                "variable": variable,
                "map_url": map_url,
                "storage_path": storage_path,
                "report_week": request.report_week,
                "report_year": request.report_year,
                "created_at": datetime.utcnow().isoformat(),
            }

            supabase.table("generated_maps").insert(map_record).execute()
            print("✅ Database record saved")

            outputs.append(MapOutput(variable=variable, map_url=map_url))

        except Exception as e:
            print(f"❌ Error generating {variable} map: {e}")
            append_workflow_log(
                supabase_admin,
                workflow_status_id,
                stage="generate_maps",
                status="error",
                message=f"Failed generating map for variable: {variable} ({str(e)[:240]})",
            )
            # Continue with other variables
            continue

    # =========================
    # 7. CLEAN UP TEMP FILES
    # =========================
    import shutil

    # Remove temp CSV
    if temp_csv and os.path.exists(temp_csv):
        os.remove(temp_csv)
        print("\n✅ Temp CSV cleaned up")

    # Remove shapefile temp directory
    if temp_shapefile_dir and os.path.exists(temp_shapefile_dir):
        shutil.rmtree(temp_shapefile_dir)
        print("✅ Shapefile temp directory cleaned up")

    print(f"\n{'=' * 60}")
    print(f"✅ MAP GENERATION COMPLETE: {len(outputs)} maps created")
    print(f"{'=' * 60}\n")

    if not outputs:
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="generate_maps",
            status="error",
            message="Map generation failed: no map outputs created",
        )
        raise HTTPException(status_code=500, detail="No maps were generated successfully")

    if workflow_status_id is not None:
        update_workflow_status_flags(
            supabase_admin=supabase_admin,
            workflow_status_id=workflow_status_id,
            flags={"mapped": True},
        )
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage="generate_maps",
            status="success",
            message=f"Map generation complete: {len(outputs)} map(s) created",
        )

    return MapGenerationResponse(outputs=outputs)


# ============================================================================
# STEP 4: GENERATE FINAL PDF REPORT
# ============================================================================
@router.post("/generate-report", response_model=ReportGenerationResponse)
async def generate_report(
    request: ReportGenerationRequest,
    user=Depends(get_current_user),
):
    """
    Step 4: Generate the final weekly PDF report and store it in Supabase.

    Step 4 workflow:
    1) Gather latest observation file for the selected report window
    2) Gather generated maps for the same window
    3) Generate AI narration from those inputs
    4) Build the PDF with existing helper and store it in Supabase
    """
    print("\n" + "=" * 60)
    print("📄 REPORT GENERATION STARTED")
    print("=" * 60)

    supabase_admin = get_supabase_admin()
    user_id = user.id if hasattr(user, "id") else user.get("id")

    print(f"👤 User ID: {user_id}")
    print(f"📍 County: {request.county_name}")
    print(
        f"📅 Week: {request.week_number}, Year: {request.year}, "
        f"Period: {request.report_start_at} to {request.report_end_at}"
    )

    stage_statuses = []
    workflow_status_id: Optional[int] = None

    def add_stage(
        stage: str,
        status: str,
        message: str,
        *,
        workflow_flags: Optional[Dict[str, Any]] = None,
        log_stage: Optional[str] = None,
    ):
        stage_statuses.append(
            {
                "stage": stage,
                "status": status,
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )
        append_workflow_log(
            supabase_admin,
            workflow_status_id,
            stage=log_stage or stage,
            status=status,
            message=message,
        )
        if workflow_flags and workflow_status_id is not None:
            update_workflow_status_flags(
                supabase_admin=supabase_admin,
                workflow_status_id=workflow_status_id,
                flags=workflow_flags,
            )

    add_stage("report_generation", "in_progress", "Step 4 started")
    workflow_status_id = get_or_create_workflow_status(
        supabase_admin=supabase_admin,
        user_id=user_id,
        report_week=request.week_number,
        report_year=request.year,
        report_start_at=request.report_start_at,
        report_end_at=request.report_end_at,
    )

    profile = {}
    try:
        add_stage(
            "profile_validation",
            "in_progress",
            "Checking required profile details for report generation",
        )
        profile = fetch_profile_for_user(
            supabase_admin,
            user,
            raise_on_error=True,
        )
    except Exception as e:
        print(f"⚠️ Failed to fetch profile for report details validation: {e}")
        add_stage(
            "profile_validation",
            "failed",
            "Unable to verify profile details. Please try again.",
            workflow_flags={"generated": False, "completed": False},
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to verify profile details. Please try again.",
        )

    missing_fields = _missing_required_profile_fields(user, profile)
    if missing_fields:
        missing_fields_str = ", ".join(missing_fields)
        add_stage(
            "profile_validation",
            "failed",
            f"Missing profile details: {missing_fields_str}",
            workflow_flags={"generated": False, "completed": False},
        )
        raise HTTPException(
            status_code=400,
            detail=(
                "Your profile is incomplete for report generation. "
                "Please update your profile details on the Profile page. "
                f"Missing fields: {missing_fields_str}."
            ),
        )

    add_stage(
        "profile_validation",
        "completed",
        "All required profile details are present",
    )

    # ------------------------------------------------------------------
    # 1. Gather observation + map context for AI narration
    # ------------------------------------------------------------------
    centroid = None
    open_meteo_daily = {}
    observation_file_id = None
    observation_label = "observation_data.csv"
    try:
        add_stage(
            "observation_context",
            "in_progress",
            "Loading observation file for selected report window",
        )
        obs_payload = _load_observation_bytes_with_fallback(
            supabase=supabase_admin,
            user_id=user_id,
            report_week=request.week_number,
            report_year=request.year,
            county_name=request.county_name,
            report_start_at=request.report_start_at,
            report_end_at=request.report_end_at,
            persist_auto_upload=True,
            supabase_admin=supabase_admin,
        )
        observation_file_id = obs_payload.get("observation_file_id")
        observation_label = obs_payload.get("observation_label", observation_label)
        if workflow_status_id is not None:
            update_workflow_status_flags(
                supabase_admin=supabase_admin,
                workflow_status_id=workflow_status_id,
                flags={"observation_file_id": observation_file_id, "uploaded": True},
            )
        observation_bytes = obs_payload["bytes"]
        centroid = _extract_centroid_from_observation_csv(observation_bytes)
        observation_summary = summarize_observation_data(
            csv_bytes=observation_bytes,
            requested_variables=request.variables,
        )
        add_stage(
            "observation_context",
            "completed",
            f"Observation data prepared from {observation_label}",
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to prepare observation context: {e}")
        add_stage(
            "observation_context",
            "failed",
            "Failed to read observation data from upload or TAHMO/KMD/Open-Meteo auto-fetch",
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to read observation data from upload or TAHMO/KMD/Open-Meteo auto-fetch",
        )

    try:
        if centroid:
            add_stage(
                "open_meteo_forecast",
                "in_progress",
                "Fetching Open-Meteo daily forecast for report window",
            )
            open_meteo_daily = fetch_daily_forecast(
                latitude=centroid["lat"],
                longitude=centroid["lon"],
                report_start_at=request.report_start_at,
                report_end_at=request.report_end_at,
            )
            add_stage(
                "open_meteo_forecast",
                "completed",
                "Open-Meteo forecast loaded",
            )
        else:
            add_stage(
                "open_meteo_forecast",
                "failed",
                "No station coordinates found; Open-Meteo forecast unavailable",
            )
    except Exception as e:
        print(f"⚠️ Failed to fetch Open-Meteo forecast: {e}")
        open_meteo_daily = {}
        add_stage(
            "open_meteo_forecast",
            "failed",
            "Failed to load Open-Meteo forecast; report uses fallback placeholders",
        )

    rainfall_map_storage_path = None
    try:
        add_stage(
            "map_context",
            "in_progress",
            "Loading generated maps for selected variables",
        )
        maps_response = (
            supabase_admin.table("generated_maps")
            .select("variable,map_url,storage_path,created_at")
            .eq("user_id", user_id)
            .eq("report_week", request.week_number)
            .eq("report_year", request.year)
            .order("created_at", desc=True)
            .execute()
        )
        rows = maps_response.data or []

        latest_maps_by_var = {}
        for row in rows:
            variable = row.get("variable")
            if variable and variable not in latest_maps_by_var:
                latest_maps_by_var[variable] = row

        map_context = []
        for variable in request.variables:
            row = latest_maps_by_var.get(variable)
            if row:
                map_context.append(
                    {
                        "variable": variable,
                        "map_url": row.get("map_url", ""),
                        "storage_path": row.get("storage_path", ""),
                    }
                )

        # Prefer rainfall map for the PDF cover page map slot.
        rainfall_row = latest_maps_by_var.get("rainfall") or latest_maps_by_var.get("rain")
        if rainfall_row:
            rainfall_map_storage_path = rainfall_row.get("storage_path")
        add_stage(
            "map_context",
            "completed",
            f"Map context prepared for {len(map_context)} variable(s)",
        )
    except Exception as e:
        print(f"⚠️ Failed to fetch generated maps context: {e}")
        map_context = []
        add_stage(
            "map_context",
            "failed",
            "Failed to load map context; continuing without map metadata",
        )

    # ------------------------------------------------------------------
    # 2. Generate AI narration from maps + observation summary
    # ------------------------------------------------------------------
    report_dates_for_narration: List[str] = []
    start_date_for_narration = datetime.fromisoformat(request.report_start_at).date()
    end_date_for_narration = datetime.fromisoformat(request.report_end_at).date()
    cursor_for_narration = start_date_for_narration
    while cursor_for_narration <= end_date_for_narration:
        report_dates_for_narration.append(cursor_for_narration.isoformat())
        cursor_for_narration = cursor_for_narration.fromordinal(cursor_for_narration.toordinal() + 1)
    if not report_dates_for_narration:
        report_dates_for_narration = [request.report_start_at]

    day_labels_for_narration = [
        f"{datetime.fromisoformat(d).strftime('%A')}\n{datetime.fromisoformat(d).strftime('%d/%m/%Y')}"
        for d in report_dates_for_narration
    ]
    county_rows_for_narration = _build_rows_from_daily(
        open_meteo_daily or {},
        report_dates_for_narration,
        day_labels_for_narration,
    )
    marine_daily_wind_for_narration: Dict[str, Any] = {}
    for idx, label in enumerate(day_labels_for_narration, start=1):
        marine_daily_wind_for_narration[f"Day {idx}"] = (
            county_rows_for_narration.get(label, {}).get("Winds", "N/A")
        )

    add_stage(
        "ai_narration",
        "in_progress",
        "Generating weekly narration from observation and map context",
        log_stage="generate_narration",
    )
    narration = await generate_report_narration(
        county_name=request.county_name,
        week_number=request.week_number,
        year=request.year,
        report_start_at=request.report_start_at,
        report_end_at=request.report_end_at,
        selected_variables=request.variables,
        observation_summary=observation_summary,
        map_context=map_context,
        marine_daily_wind=marine_daily_wind_for_narration,
    )
    narration_source = narration.get("source", "unknown")
    if narration_source == "fallback":
        add_stage(
            "ai_narration",
            "completed",
            "AI narration unavailable; fallback narration applied",
            log_stage="generate_narration",
        )
    else:
        add_stage(
            "ai_narration",
            "completed",
            f"AI narration generated via {narration_source}",
            log_stage="generate_narration",
        )

    # ------------------------------------------------------------------
    # 3. Build structured data payload for the PDF helper
    # ------------------------------------------------------------------
    signoff_raw_name = profile.get("full_name") or "N/A"
    signoff_prefix = (profile.get("prefix") or "").strip()
    if signoff_prefix and signoff_raw_name != "N/A":
        normalized_name = signoff_raw_name.strip()
        lower_prefix = signoff_prefix.lower().rstrip(".")
        lower_name = normalized_name.lower()
        if lower_name.startswith(f"{lower_prefix}. ") or lower_name.startswith(f"{lower_prefix} "):
            signoff_name = normalized_name
        else:
            signoff_name = f"{signoff_prefix} {normalized_name}"
    else:
        signoff_name = signoff_raw_name
    county_for_title = profile.get("county") or request.county_name
    signoff_title = (
        profile.get("job_title")
        or profile.get("title")
        or f"County Director of Meteorological Services, {county_for_title} County."
    )
    signoff_mobile = profile.get("phone") or "N/A"
    signoff_email = profile.get("signoff_email") or _get_personal_email(user, profile)
    if not signoff_email:
        signoff_email = "N/A"

    signoff = {
        "name": signoff_name,
        "job_title": signoff_title,
        "mobile": signoff_mobile,
        "email": signoff_email,
    }

    issue_date = datetime.utcnow().strftime("%Y-%m-%d")
    period_str = f"{request.report_start_at} to {request.report_end_at}"
    report_dates = []
    start_date = datetime.fromisoformat(request.report_start_at).date()
    end_date = datetime.fromisoformat(request.report_end_at).date()
    cursor = start_date
    while cursor <= end_date:
        report_dates.append(cursor.isoformat())
        cursor = cursor.fromordinal(cursor.toordinal() + 1)
    if not report_dates:
        report_dates = [request.report_start_at]
    day_labels = [
        f"{datetime.fromisoformat(d).strftime('%A')}\n{datetime.fromisoformat(d).strftime('%d/%m/%Y')}"
        for d in report_dates
    ]

    county_rows_for_fallback = _build_rows_from_daily(open_meteo_daily or {}, report_dates, day_labels)

    marine_daily_wind = {}
    for idx, label in enumerate(day_labels, start=1):
        marine_daily_wind[f"Day {idx}"] = county_rows_for_fallback.get(label, {}).get("Winds", "N/A")

    subcounty_ward_map = _load_subcounty_ward_map(
        supabase_admin=supabase_admin,
        county_name=request.county_name,
        bucket_name=BUCKET_NAME,
    )
    sub_counties_payload: List[Dict[str, Any]] = []
    if subcounty_ward_map:
        for idx, sub in enumerate(subcounty_ward_map, start=1):
            centroid = sub.get("centroid") or {}
            lat = centroid.get("lat")
            lon = centroid.get("lon")
            sub_daily = {}
            if isinstance(lat, (float, int)) and isinstance(lon, (float, int)):
                try:
                    sub_daily = fetch_daily_forecast(
                        latitude=float(lat),
                        longitude=float(lon),
                        report_start_at=request.report_start_at,
                        report_end_at=request.report_end_at,
                    )
                except Exception as e:
                    print(f"⚠️ Open-Meteo fetch failed for sub-county {sub['sub_county']}: {e}")

            sub_rows = _build_rows_from_daily(sub_daily or open_meteo_daily or {}, report_dates, day_labels)
            wards_phrase = _format_wards_phrase(sub.get("wards", []))
            sub_counties_payload.append(
                {
                    "title": f"Table {idx}: {sub['sub_county']} Sub-County; {wards_phrase}.",
                    "days": day_labels,
                    "forecast": sub_rows,
                }
            )
    else:
        sub_counties_payload = [
            {
                "title": request.county_name,
                "days": day_labels,
                "forecast": county_rows_for_fallback,
            }
        ]

    data = {
        "meta": {
            "station": profile.get("station_name") or request.county_name,
            "station_name": profile.get("station_name") or request.county_name,
            "station_address": profile.get("station_address") or "",
            "county": profile.get("county") or request.county_name,
            "issue_date": issue_date,
            "period": period_str,
            "period_start": request.report_start_at,
            "period_end": request.report_end_at,
        },
        "profile": {
            "station_name": profile.get("station_name") or request.county_name,
            "station_address": profile.get("station_address") or "",
            "county": profile.get("county") or request.county_name,
        },
        "sub_counties": sub_counties_payload,
        "marine": {
            "daily_wind": marine_daily_wind
        },
    }

    # ------------------------------------------------------------------
    # 4. Generate PDF to a temporary file
    # ------------------------------------------------------------------
    filename = (
        f"{request.county_name.replace(' ', '_').lower()}_week_"
        f"{request.week_number}_{request.year}.pdf"
    )

    temp_dir = tempfile.mkdtemp(prefix="weekly_report_")
    output_path = os.path.join(temp_dir, filename)
    map_path = None

    # Try to attach rainfall distribution map below issue/period on cover page.
    if rainfall_map_storage_path:
        try:
            add_stage(
                "map_attachment",
                "in_progress",
                "Fetching rainfall distribution map for report cover",
            )
            map_bytes = supabase_admin.storage.from_(BUCKET_NAME).download(
                rainfall_map_storage_path
            )
            map_path = os.path.join(temp_dir, "rainfall_distribution_map.png")
            with open(map_path, "wb") as map_file:
                map_file.write(map_bytes)
            add_stage(
                "map_attachment",
                "completed",
                "Rainfall distribution map attached to report cover",
            )
        except Exception as e:
            print(f"⚠️ Failed to attach rainfall map: {e}")
            map_path = None
            add_stage(
                "map_attachment",
                "failed",
                "Could not attach rainfall map; continuing without cover map",
            )
    else:
        add_stage(
            "map_attachment",
            "completed",
            "No rainfall map found for this window; report generated without cover map",
        )

    try:
        add_stage(
            "pdf_generation",
            "in_progress",
            "Generating PDF document",
            log_stage="generate_pdf",
        )
        print(f"📝 Generating PDF at: {output_path}")
        generate_weekly_forecast_pdf(
            data=data,
            narration=narration,
            map_path=map_path,
            output_path=output_path,
            signoff=signoff,
        )
        print("✅ PDF generation complete")
        add_stage(
            "pdf_generation",
            "completed",
            "PDF document generated",
            log_stage="generate_pdf",
        )
    except Exception as e:
        print(f"❌ Failed to generate PDF: {e}")
        add_stage(
            "pdf_generation",
            "failed",
            "Failed to generate report PDF",
            log_stage="generate_pdf",
        )
        raise HTTPException(status_code=500, detail="Failed to generate report PDF")

    # ------------------------------------------------------------------
    # 5. Upload PDF to Supabase Storage and create DB record
    # ------------------------------------------------------------------
    try:
        add_stage(
            "storage_upload",
            "in_progress",
            "Uploading generated PDF to storage",
            log_stage="store_report",
        )
        with open(output_path, "rb") as f:
            pdf_bytes = f.read()

        resolved_observation_file_id = observation_file_id
        if not resolved_observation_file_id:
            add_stage(
                "observation_persist",
                "in_progress",
                "Persisting auto-fetched observation data for report linkage",
                workflow_flags={"uploaded": True, "aggregated": True},
            )
            obs_timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            auto_upload_id = str(uuid.uuid4())
            auto_file_name = (
                observation_label
                if observation_label.endswith(".csv")
                else f"auto_observation_{request.week_number}_{request.year}.csv"
            )
            auto_storage_path = (
                f"users/{user_id}/observations/"
                f"auto_{request.week_number}_{request.year}_{obs_timestamp}.csv"
            )
            supabase_admin.storage.from_(BUCKET_NAME).upload(
                path=auto_storage_path,
                file=observation_bytes,
                file_options={"content-type": "text/csv"},
            )
            supabase_admin.table("uploads").insert(
                {
                    "id": auto_upload_id,
                    "user_id": user_id,
                    "file_name": auto_file_name,
                    "file_path": auto_storage_path,
                    "file_type": "observations",
                    "status": "auto_fetched",
                    "report_week": request.week_number,
                    "report_year": request.year,
                    "report_start_at": request.report_start_at,
                    "report_end_at": request.report_end_at,
                }
            ).execute()
            resolved_observation_file_id = auto_upload_id
            add_stage(
                "observation_persist",
                "completed",
                "Auto-fetched observation data persisted and linked",
                workflow_flags={"observation_file_id": resolved_observation_file_id},
            )

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        storage_path = (
            f"users/{user_id}/reports/"
            f"week_{request.week_number}_{request.year}/report_{timestamp}.pdf"
        )

        print(f"⬆️ Uploading PDF to storage: {storage_path}")
        supabase_admin.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=pdf_bytes,
            file_options={"content-type": "application/pdf"},
        )

        # Store as "<bucket>/<path>" so existing download route can split it
        file_path = f"{BUCKET_NAME}/{storage_path}"

        report_record = {
            "user_id": user_id,
            "observation_file_id": resolved_observation_file_id,
            "template_file_id": None,
            "status": "success",
            "file_path": file_path,
            "generated_at": datetime.utcnow().isoformat(),
        }

        print("💾 Saving generated_reports record")
        insert_result = (
            supabase_admin.table("generated_reports")
            .insert(report_record)
            .execute()
        )

        rows = insert_result.data or []
        if not rows:
            raise Exception("Insert into generated_reports returned no rows")

        report_id = rows[0]["id"]
        pdf_url = f"/api/v1/reports/download/{report_id}"

        # Persist immutable input/output snapshot for archive detail view fidelity.
        try:
            snapshot_payload = {
                "report_id": str(report_id),
                "user_id": str(user_id),
                "generated_at": report_record["generated_at"],
                "observation_file_id": (
                    str(resolved_observation_file_id) if resolved_observation_file_id else None
                ),
                "observation_summary": observation_summary or {},
                "ai_narration": narration or {},
                "maps": map_context or [],
                "report_data": data or {},
                "period": {
                    "start": request.report_start_at,
                    "end": request.report_end_at,
                    "week": request.week_number,
                    "year": request.year,
                },
            }
            snapshot_bytes = json.dumps(snapshot_payload, ensure_ascii=True).encode("utf-8")
            snapshot_path = f"users/{user_id}/report_snapshots/{report_id}.json"
            supabase_admin.storage.from_(BUCKET_NAME).upload(
                path=snapshot_path,
                file=snapshot_bytes,
                file_options={"content-type": "application/json"},
            )
        except Exception as snapshot_exc:
            print(f"⚠️ Failed to persist report snapshot JSON: {snapshot_exc}")

        print("✅ Report record created")
        add_stage(
            "storage_upload",
            "completed",
            "PDF uploaded and report record created",
            workflow_flags={
                "generated": True,
                "completed": True,
                "generated_report_id": report_id,
            },
            log_stage="store_report",
        )
        add_stage(
            "workflow_complete",
            "success",
            "Workflow completed successfully",
        )

    except Exception as e:
        print(f"❌ Failed to upload or save report record: {e}")
        add_stage(
            "storage_upload",
            "failed",
            "Failed to store generated report",
            workflow_flags={"generated": False, "completed": False},
            log_stage="store_report",
        )
        raise HTTPException(status_code=500, detail="Failed to store generated report")
    finally:
        # Clean up temp directory
        try:
            import shutil

            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print("🧹 Temp report directory cleaned up")
        except Exception as cleanup_err:
            print(f"⚠️ Failed to clean up temp directory: {cleanup_err}")

    print("\n" + "=" * 60)
    print("✅ REPORT GENERATION COMPLETE")
    print("=" * 60 + "\n")
    add_stage(
        "report_generation",
        "completed",
        "Step 4 completed successfully",
        workflow_flags={"generated": True, "completed": True},
    )

    return ReportGenerationResponse(
        pdf_url=pdf_url,
        filename=filename,
        report_week=request.week_number,
        report_year=request.year,
        stage_statuses=stage_statuses,
    )

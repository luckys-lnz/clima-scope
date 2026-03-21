"""Load past weather observations from the daily_weather table."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, Tuple

import pandas as pd

from app.core.supabase import get_supabase_admin
from app.services.county_service import get_county_by_identifier


def _normalize_dataframe(df: pd.DataFrame, county: Dict[str, Any]) -> pd.DataFrame:
    """Normalize columns so they match the observation CSV expectations."""
    result = df.copy()
    result["lat"] = county.get("centroid_lat")
    result["lon"] = county.get("centroid_lon")
    result["rainfall"] = pd.to_numeric(result.get("precipitation_mm"), errors="coerce")
    result["tmin"] = pd.to_numeric(result.get("temp_min_c"), errors="coerce")
    result["tmax"] = pd.to_numeric(result.get("temp_max_c"), errors="coerce")
    result["station_name"] = county.get("name") or "Unknown County"
    return result[["date", "lat", "lon", "station_name", "rainfall", "tmin", "tmax"]]


def fetch_historical_weather_dataframe(
    county_identifier: str,
    window_start: str,
    window_end: str,
    supabase_admin=None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Retrieve historical records and normalize them for the workflow."""

    supabase_admin = supabase_admin or get_supabase_admin()
    county = get_county_by_identifier(county_identifier, supabase_admin=supabase_admin)
    metadata: Dict[str, Any] = {
        "window_start": window_start,
        "window_end": window_end,
        "county_identifier": county_identifier,
        "source": "daily_weather",
    }

    if not county:
        return pd.DataFrame(), metadata

    response = (
        supabase_admin.table("daily_weather")
        .select(
            "date,temp_max_c,temp_min_c,precipitation_mm,wind_speed_avg_kmh,confidence,source"
        )
        .eq("county_id", county["id"])
        .gte("date", window_start)
        .lte("date", window_end)
        .order("date", desc=False)
        .execute()
    )
    rows = response.data or []
    metadata.update(
        {
            "county_id": county["id"],
            "county_name": county.get("name"),
            "county_code": county.get("code"),
            "row_count": len(rows),
        }
    )

    if not rows:
        return pd.DataFrame(), metadata

    df = pd.DataFrame(rows)
    normalized = _normalize_dataframe(df, county)
    metadata["lat"] = county.get("centroid_lat")
    metadata["lon"] = county.get("centroid_lon")
    return normalized, metadata


def fetch_historical_weather_csv_bytes(
    county_identifier: str,
    window_start: str,
    window_end: str,
    supabase_admin=None,
) -> Tuple[bytes, Dict[str, Any]]:
    df, metadata = fetch_historical_weather_dataframe(
        county_identifier=county_identifier,
        window_start=window_start,
        window_end=window_end,
        supabase_admin=supabase_admin,
    )

    if df.empty:
        return b"", metadata

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    metadata["source_type"] = "daily_weather"
    return csv_bytes, metadata


def _two_week_window_from_previous_day(report_start_at: str) -> Tuple[str, str]:
    report_start = date.fromisoformat(report_start_at)
    window_end = report_start - timedelta(days=1)
    window_start = window_end - timedelta(days=13)
    return window_start.isoformat(), window_end.isoformat()


def fetch_recent_station_weather_csv_bytes(
    county_identifier: str,
    report_start_at: str,
    supabase_admin=None,
) -> Tuple[bytes, Dict[str, Any]]:
    window_start, window_end = _two_week_window_from_previous_day(report_start_at)
    supabase_admin = supabase_admin or get_supabase_admin()
    county = get_county_by_identifier(county_identifier, supabase_admin=supabase_admin)
    metadata: Dict[str, Any] = {
        "window_start": window_start,
        "window_end": window_end,
        "county_identifier": county_identifier,
        "source": "daily_weather_recent",
    }

    if not county:
        return b"", metadata

    allowed_sources = ["station", "upload", "observation"]
    response = (
        supabase_admin.table("daily_weather")
        .select(
            "date,temp_max_c,temp_min_c,precipitation_mm,wind_speed_avg_kmh,confidence,source"
        )
        .eq("county_id", county["id"])
        .gte("date", window_start)
        .lte("date", window_end)
        .in_("source", allowed_sources)
        .order("date", desc=False)
        .execute()
    )
    rows = response.data or []
    metadata.update(
        {
            "county_id": county["id"],
            "county_name": county.get("name"),
            "county_code": county.get("code"),
            "row_count": len(rows),
        }
    )

    if not rows:
        return b"", metadata

    normalized = _normalize_dataframe(pd.DataFrame(rows), county)
    metadata["lat"] = county.get("centroid_lat")
    metadata["lon"] = county.get("centroid_lon")
    metadata["source_type"] = "recent_station"
    csv_bytes = normalized.to_csv(index=False).encode("utf-8")
    return csv_bytes, metadata

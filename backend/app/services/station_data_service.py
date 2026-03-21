from __future__ import annotations

import io
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
import pandas as pd
from dateutil.relativedelta import relativedelta

from app.core.config import settings

OPEN_METEO_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OPEN_METEO_DAILY_PARAMS = ",".join(
    ["precipitation_sum", "temperature_2m_max", "temperature_2m_min"]
)


def _resolve_column(columns: List[str], candidates: List[str]) -> Optional[str]:
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


def get_three_month_window_from_previous_week(report_start_at: str) -> Tuple[str, str]:
    """
    Build a rolling 3-month historical window ending at the day before the report starts.
    Example: report starts on 2026-03-09 -> window ends 2026-03-08 and starts ~3 months earlier.
    """
    report_start = date.fromisoformat(report_start_at)
    window_end = report_start - timedelta(days=1)
    window_start = window_end - relativedelta(months=3) + timedelta(days=1)
    return window_start.isoformat(), window_end.isoformat()


def get_full_year_window_from_previous_day(report_start_at: str) -> Tuple[str, str]:
    """
    Build a full-year window ending at the day before the report starts.
    Example: report starts on 2026-03-09 -> window spans 2025-03-09 through 2026-03-08.
    """
    report_start = date.fromisoformat(report_start_at)
    window_end = report_start - timedelta(days=1)
    window_start = window_end - relativedelta(years=1) + timedelta(days=1)
    return window_start.isoformat(), window_end.isoformat()


def _normalize_station_df(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    lat_col = _resolve_column(df.columns.tolist(), ["lat", "latitude", "y"])
    lon_col = _resolve_column(df.columns.tolist(), ["lon", "lng", "long", "longitude", "x"])
    rain_col = _resolve_column(
        df.columns.tolist(),
        ["rainfall", "rain", "precipitation", "precip", "rr", "rain_mm", "amount_mm"],
    )
    station_col = _resolve_column(df.columns.tolist(), ["station", "station_name", "name", "code"])
    date_col = _resolve_column(df.columns.tolist(), ["date", "obs_date", "observation_date", "timestamp"])

    if not lat_col or not lon_col or not rain_col:
        raise ValueError(f"{source_name}: missing latitude/longitude/rainfall columns")

    keep_cols = [lat_col, lon_col, rain_col]
    if station_col:
        keep_cols.append(station_col)
    if date_col:
        keep_cols.append(date_col)

    out = df[keep_cols].copy()
    out = out.rename(
        columns={
            lat_col: "lat",
            lon_col: "lon",
            rain_col: "rainfall",
            station_col: "station_name" if station_col else None,
            date_col: "obs_date" if date_col else None,
        }
    )
    out["source"] = source_name

    if "station_name" not in out.columns:
        out["station_name"] = [f"{source_name}_station_{idx+1}" for idx in range(len(out))]
    if "obs_date" in out.columns:
        out["obs_date"] = pd.to_datetime(out["obs_date"], errors="coerce").dt.date

    out["lat"] = pd.to_numeric(out["lat"], errors="coerce")
    out["lon"] = pd.to_numeric(out["lon"], errors="coerce")
    out["rainfall"] = pd.to_numeric(out["rainfall"], errors="coerce")
    out = out.dropna(subset=["lat", "lon", "rainfall"]).copy()
    return out


def _parse_payload_to_df(response: httpx.Response) -> pd.DataFrame:
    content_type = response.headers.get("content-type", "").lower()
    if "text/csv" in content_type or "application/csv" in content_type:
        return pd.read_csv(io.StringIO(response.text))

    payload = response.json()
    if isinstance(payload, list):
        return pd.DataFrame(payload)
    if isinstance(payload, dict):
        for key in ["data", "results", "stations", "observations"]:
            if isinstance(payload.get(key), list):
                return pd.DataFrame(payload[key])
    raise ValueError("Unsupported station API payload format")


def _fetch_source_rows(
    source_name: str,
    base_url: str,
    api_key: str,
    county_name: str,
    window_start: str,
    window_end: str,
) -> pd.DataFrame:
    headers: Dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["x-api-key"] = api_key

    params = {
        "county": county_name,
        "start_date": window_start,
        "end_date": window_end,
    }
    response = httpx.get(
        base_url,
        params=params,
        headers=headers,
        timeout=settings.STATION_FETCH_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    raw_df = _parse_payload_to_df(response)
    return _normalize_station_df(raw_df, source_name=source_name)


def _aggregate_station_rainfall(
    df: pd.DataFrame,
    window_start: str,
    window_end: str,
) -> pd.DataFrame:
    if "obs_date" in df.columns:
        window_start_date = date.fromisoformat(window_start)
        window_end_date = date.fromisoformat(window_end)
        df = df[
            (df["obs_date"].notna())
            & (df["obs_date"] >= window_start_date)
            & (df["obs_date"] <= window_end_date)
        ].copy()

    if df.empty:
        return df

    grouped = (
        df.groupby(["station_name", "lat", "lon", "source"], dropna=False)["rainfall"]
        .sum()
        .reset_index()
    )
    grouped["window_start"] = window_start
    grouped["window_end"] = window_end
    grouped = grouped.rename(columns={"rainfall": "rainfall"})
    return grouped


def _geocode_county_centroid(county_name: str) -> Tuple[float, float]:
    queries = []
    county = (county_name or "").strip()
    if county and county.lower() != "unknown":
        queries.append(f"{county} County, Kenya")
    queries.append("Kenya")

    for query in queries:
        try:
            response = httpx.get(
                OPEN_METEO_GEOCODE_URL,
                params={"name": query, "count": 1, "language": "en", "format": "json"},
                timeout=settings.STATION_FETCH_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
            results = payload.get("results") or []
            if results:
                return float(results[0]["latitude"]), float(results[0]["longitude"])
        except Exception:
            continue

    # Kenya centroid fallback (works even if geocoding service is unavailable).
    return -0.0236, 37.9062


def _fetch_open_meteo_precip_sum(lat: float, lon: float, window_start: str, window_end: str) -> float:
    response = httpx.get(
        OPEN_METEO_ARCHIVE_URL,
        params={
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "start_date": window_start,
            "end_date": window_end,
            "daily": "precipitation_sum",
            "timezone": "Africa/Nairobi",
        },
        timeout=settings.STATION_FETCH_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    daily = payload.get("daily", {})
    values = pd.to_numeric(pd.Series(daily.get("precipitation_sum", [])), errors="coerce").dropna()
    if values.empty:
        raise ValueError(f"Open-Meteo archive returned no precipitation data for ({lat}, {lon})")
    return float(values.sum())


def _fetch_open_meteo_historical_fallback(
    county_name: str,
    window_start: str,
    window_end: str,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    center_lat, center_lon = _geocode_county_centroid(county_name)
    offsets = [
        (0.0, 0.0),
        (0.12, 0.0),
        (-0.12, 0.0),
        (0.0, 0.12),
        (0.0, -0.12),
    ]

    rows: List[Dict[str, Any]] = []
    for idx, (dlat, dlon) in enumerate(offsets, start=1):
        lat = center_lat + dlat
        lon = center_lon + dlon
        rainfall_sum = _fetch_open_meteo_precip_sum(
            lat=lat,
            lon=lon,
            window_start=window_start,
            window_end=window_end,
        )
        rows.append(
            {
                "station_name": f"OpenMeteoGrid{idx}",
                "lat": lat,
                "lon": lon,
                "source": "OPEN_METEO_ARCHIVE",
                "rainfall": rainfall_sum,
                "window_start": window_start,
                "window_end": window_end,
            }
        )

    df = pd.DataFrame(rows)
    metadata = {
        "window_start": window_start,
        "window_end": window_end,
        "sources_used": ["OPEN_METEO_ARCHIVE"],
        "row_count_raw": int(len(rows)),
        "row_count_aggregated": int(len(df)),
    }
    return df, metadata


def fetch_aggregated_station_data(
    county_name: str,
    report_start_at: str,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    if not settings.AUTO_STATION_FETCH_ENABLED:
        raise ValueError("Automatic station fetch is disabled")

    window_start, window_end = get_three_month_window_from_previous_week(report_start_at)
    frames: List[pd.DataFrame] = []
    sources_used: List[str] = []
    errors: List[str] = []

    if settings.TAHMO_BASE_URL:
        try:
            tahmo_df = _fetch_source_rows(
                source_name="TAHMO",
                base_url=settings.TAHMO_BASE_URL,
                api_key=settings.TAHMO_API_KEY,
                county_name=county_name,
                window_start=window_start,
                window_end=window_end,
            )
            if not tahmo_df.empty:
                frames.append(tahmo_df)
                sources_used.append("TAHMO")
        except Exception as exc:
            errors.append(f"TAHMO fetch failed: {exc}")

    if settings.KMD_BASE_URL:
        try:
            kmd_df = _fetch_source_rows(
                source_name="KMD",
                base_url=settings.KMD_BASE_URL,
                api_key=settings.KMD_API_KEY,
                county_name=county_name,
                window_start=window_start,
                window_end=window_end,
            )
            if not kmd_df.empty:
                frames.append(kmd_df)
                sources_used.append("KMD")
        except Exception as exc:
            errors.append(f"KMD fetch failed: {exc}")

    if not frames:
        try:
            return _fetch_open_meteo_historical_fallback(
                county_name=county_name,
                window_start=window_start,
                window_end=window_end,
            )
        except Exception as exc:
            details = "; ".join(errors) if errors else "No source endpoints configured"
            raise ValueError(
                "No station data fetched from TAHMO/KMD and Open-Meteo historical fallback failed. "
                f"{details}; Open-Meteo error: {exc}"
            )

    combined = pd.concat(frames, ignore_index=True)
    aggregated = _aggregate_station_rainfall(combined, window_start=window_start, window_end=window_end)
    if aggregated.empty:
        raise ValueError("Fetched station data but no valid rows in the 3-month aggregation window")

    metadata = {
        "window_start": window_start,
        "window_end": window_end,
        "sources_used": sorted(set(sources_used)),
        "row_count_raw": int(len(combined)),
        "row_count_aggregated": int(len(aggregated)),
    }
    return aggregated, metadata


def fetch_aggregated_station_csv_bytes(
    county_name: str,
    report_start_at: str,
) -> Tuple[bytes, Dict[str, Any]]:
    aggregated, metadata = fetch_aggregated_station_data(
        county_name=county_name,
        report_start_at=report_start_at,
    )
    csv_bytes = aggregated.to_csv(index=False).encode("utf-8")
    return csv_bytes, metadata


def _two_week_window_from_previous_day(report_start_at: str) -> Tuple[str, str]:
    report_start = date.fromisoformat(report_start_at)
    window_end = report_start - timedelta(days=1)
    window_start = window_end - timedelta(days=13)
    return window_start.isoformat(), window_end.isoformat()


def _fetch_open_meteo_daily_series(
    lat: float,
    lon: float,
    window_start: str,
    window_end: str,
) -> Dict[str, List[Any]]:
    response = httpx.get(
        OPEN_METEO_ARCHIVE_URL,
        params={
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "start_date": window_start,
            "end_date": window_end,
            "daily": OPEN_METEO_DAILY_PARAMS,
            "timezone": "Africa/Nairobi",
        },
        timeout=settings.STATION_FETCH_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    daily = payload.get("daily", {})
    if not daily:
        raise ValueError("Open-Meteo returned no daily data")
    return daily


def fetch_open_meteo_two_week_observations_csv(
    county_name: str,
    report_start_at: str,
) -> Tuple[bytes, Dict[str, Any]]:
    window_start, window_end = _two_week_window_from_previous_day(report_start_at)
    center_lat, center_lon = _geocode_county_centroid(county_name)
    offsets = [
        (0.0, 0.0),
        (0.12, 0.0),
        (-0.12, 0.0),
        (0.0, 0.12),
        (0.0, -0.12),
    ]

    rows: List[Dict[str, Any]] = []
    for idx, (dlat, dlon) in enumerate(offsets, start=1):
        lat = center_lat + dlat
        lon = center_lon + dlon
        daily = _fetch_open_meteo_daily_series(
            lat=lat,
            lon=lon,
            window_start=window_start,
            window_end=window_end,
        )
        dates = daily.get("time") or []
        precip = daily.get("precipitation_sum") or []
        tmax = daily.get("temperature_2m_max") or []
        tmin = daily.get("temperature_2m_min") or []
        max_len = max(len(dates), len(precip), len(tmax), len(tmin))
        for day_index in range(max_len):
            rows.append(
                {
                    "date": dates[day_index] if day_index < len(dates) else "",
                    "lat": lat,
                    "lon": lon,
                    "station_name": f"OpenMeteoGrid{idx}",
                    "rainfall": precip[day_index] if day_index < len(precip) else "",
                    "tmin": tmin[day_index] if day_index < len(tmin) else "",
                    "tmax": tmax[day_index] if day_index < len(tmax) else "",
                }
            )

    df = pd.DataFrame(rows)
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    metadata = {
        "window_start": window_start,
        "window_end": window_end,
        "sources_used": ["OPEN_METEO_ARCHIVE"],
        "row_count": len(df),
        "county_centroid": {"lat": center_lat, "lon": center_lon},
        "source_type": "open_meteo_two_week",
    }
    return csv_bytes, metadata

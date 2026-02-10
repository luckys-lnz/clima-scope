"""
Report Template Service

Builds a complete report payload for PDF generation by adapting a
sample complete report with selected county/week options and optional
raw sample data.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from ..config import settings
from ..utils.logging import get_logger
from .map_storage import MapStorageService, MapVariable

logger = get_logger(__name__)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _template_path() -> Path:
    return Path(settings.PDF_GENERATOR_PATH) / "sample_data" / "nairobi_sample.json"


def _raw_data_dir() -> Path:
    return _repo_root() / "backend" / "resources" / "sample_data"


def load_template_report() -> Dict[str, Any]:
    """Load the base complete-report template."""
    template_file = _template_path()
    if not template_file.exists():
        raise FileNotFoundError(f"Template report not found at {template_file}")
    with template_file.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_sample_raw_data(
    county_id: Optional[str],
    county_name: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Load sample raw weather data for a county if available."""
    raw_dir = _raw_data_dir()
    if not raw_dir.exists():
        logger.warning("sample_raw_data_dir_missing", path=str(raw_dir))
        return None

    for file_path in raw_dir.glob("*.json"):
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            continue

        if county_id and data.get("county_id") == county_id:
            return data
        if county_name and str(data.get("county_name", "")).lower() == county_name.lower():
            return data
    return None


def iso_week_dates(year: int, week_number: int) -> Tuple[str, str]:
    """Return ISO week start/end (Mon-Sun) as YYYY-MM-DD strings."""
    start = date.fromisocalendar(year, week_number, 1)
    end = date.fromisocalendar(year, week_number, 7)
    return start.isoformat(), end.isoformat()


def _format_period(week_number: int, year: int, start: str, end: str) -> str:
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    return f"Week {week_number}, {year} ({start_dt:%B %d} - {end_dt:%B %d, %Y})"


def _safe_float(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _day_names() -> list[str]:
    return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _day_abbr() -> list[str]:
    return ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "county"


def build_complete_report(
    county_name: str,
    week_number: int,
    year: int,
    include_observations: bool,
    raw_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a complete report payload using the template and optional raw data.
    """
    template = load_template_report()
    report = copy.deepcopy(template)

    county_name = county_name or report.get("cover_page", {}).get("county", {}).get("name", "Unknown")
    county_id = (
        (raw_data or {}).get("county_id")
        or report.get("cover_page", {}).get("county", {}).get("code", "00")
    )

    try:
        period_start, period_end = iso_week_dates(year, week_number)
    except ValueError:
        # Fall back to template dates if week is invalid
        raw_period = report.get("cover_page", {}).get("report_period", {})
        period_start = raw_period.get("start_date", "2026-01-19")
        period_end = raw_period.get("end_date", "2026-01-25")

    period_formatted = _format_period(week_number, year, period_start, period_end)

    # Update cover page
    cover = report.setdefault("cover_page", {})
    cover["report_title"] = f"Weekly Weather Outlook for {county_name} County"
    cover.setdefault("county", {})
    cover["county"]["name"] = county_name
    cover["county"]["code"] = county_id
    cover.setdefault("report_period", {})
    cover["report_period"].update(
        {
            "week_number": week_number,
            "year": year,
            "start_date": period_start,
            "end_date": period_end,
            "formatted": period_formatted,
        }
    )
    cover.setdefault("generation_metadata", {})
    cover["generation_metadata"]["generated_at"] = datetime.utcnow().isoformat() + "Z"

    # Inject raw data (or keep template raw data)
    raw_payload = raw_data or report.get("raw_data", {})
    raw_payload.setdefault("county_id", county_id)
    raw_payload.setdefault("county_name", county_name)
    raw_payload.setdefault("period", {})
    raw_payload["period"].update(
        {
            "start": period_start,
            "end": period_end,
            "week_number": week_number,
            "year": year,
        }
    )
    raw_payload.setdefault("metadata", {})
    raw_payload["metadata"]["include_observations"] = include_observations
    report["raw_data"] = raw_payload

    # Try to attach map paths if available in storage
    try:
        map_storage = MapStorageService()
        storage_dir = map_storage._build_storage_path(county_id, period_start, ensure_exists=False)
        if storage_dir.exists():
            def map_file(variable: MapVariable) -> Optional[Path]:
                filename = f"{county_id}_{variable.value}_{period_start}_{period_end}.png"
                return storage_dir / filename

            rain_map = map_file(MapVariable.RAINFALL)
            temp_map = map_file(MapVariable.TEMPERATURE)
            wind_map = map_file(MapVariable.WIND)

            if rain_map.exists():
                report["rainfall_outlook"]["rainfall_distribution_map"]["image_path"] = str(rain_map)
            if temp_map.exists():
                report["temperature_outlook"]["temperature_distribution_map"]["image_path"] = str(temp_map)
            if wind_map.exists():
                report["wind_outlook"]["wind_speed_distribution_map"]["image_path"] = str(wind_map)
    except Exception as exc:
        logger.warning("map_path_attach_failed", error=str(exc))

    # Update some headline stats from raw data if available
    variables = (raw_payload or {}).get("variables", {})
    temp = variables.get("temperature", {})
    rain = variables.get("rainfall", {})
    wind = variables.get("wind", {})

    weekly_temp = temp.get("weekly", {})
    weekly_rain = rain.get("weekly", {})
    weekly_wind = wind.get("weekly", {})

    exec_summary = report.setdefault("executive_summary", {})
    summary_stats = exec_summary.setdefault("summary_statistics", {})
    summary_stats["total_rainfall"] = _safe_float(
        weekly_rain.get("total"), summary_stats.get("total_rainfall", 0.0)
    )
    summary_stats["mean_temperature"] = _safe_float(
        weekly_temp.get("mean"), summary_stats.get("mean_temperature", 0.0)
    )
    summary_stats.setdefault("temperature_range", {})
    summary_stats["temperature_range"]["min"] = _safe_float(
        weekly_temp.get("min"), summary_stats["temperature_range"].get("min", 0.0)
    )
    summary_stats["temperature_range"]["max"] = _safe_float(
        weekly_temp.get("max"), summary_stats["temperature_range"].get("max", 0.0)
    )
    summary_stats["max_wind_speed"] = _safe_float(
        weekly_wind.get("max_gust"), summary_stats.get("max_wind_speed", 0.0)
    )
    summary_stats["dominant_wind_direction"] = (
        weekly_wind.get("dominant_direction")
        or summary_stats.get("dominant_wind_direction", "N/A")
    )

    # Rainfall outlook updates
    rainfall_outlook = report.get("rainfall_outlook", {})
    county_summary = rainfall_outlook.get("county_level_summary", {})
    county_summary["total_weekly_rainfall"] = summary_stats["total_rainfall"]
    county_summary["max_daily_intensity"] = _safe_float(
        weekly_rain.get("max_intensity"), county_summary.get("max_daily_intensity", 0.0)
    )
    county_summary["number_of_rainy_days"] = int(
        weekly_rain.get("rainy_days", county_summary.get("number_of_rainy_days", 0))
    )
    county_summary["probability_above_normal"] = rain.get(
        "probability_above_normal", county_summary.get("probability_above_normal")
    )

    daily_rain = rain.get("daily") or []
    if daily_rain:
        day_names = _day_names()
        daily_breakdown = []
        daily_chart = []
        try:
            base_date = date.fromisoformat(period_start)
        except ValueError:
            base_date = None
        for idx, amount in enumerate(daily_rain[:7]):
            day = day_names[idx]
            daily_breakdown.append(
                {
                    "day": day,
                    "date": (base_date + timedelta(days=idx)).isoformat() if base_date else "",
                    "rainfall": _safe_float(amount, 0.0),
                }
            )
            daily_chart.append(
                {"day": _day_abbr()[idx], "rainfall": _safe_float(amount, 0.0)}
            )
        county_summary["daily_breakdown"] = daily_breakdown
        rainfall_outlook.setdefault("temporal_patterns", {}).setdefault("daily_chart", {})[
            "data"
        ] = daily_chart

        # Peak rainfall days
        if daily_rain:
            top_indices = sorted(
                range(len(daily_rain[:7])),
                key=lambda i: daily_rain[i],
                reverse=True,
            )[:2]
            rainfall_outlook.setdefault("temporal_patterns", {})[
                "peak_rainfall_days"
            ] = [_day_names()[i] for i in top_indices]

    report["rainfall_outlook"] = rainfall_outlook

    # Temperature outlook updates
    temp_outlook = report.get("temperature_outlook", {})
    temp_summary = temp_outlook.get("county_level_summary", {})
    temp_summary["mean_weekly_temperature"] = summary_stats["mean_temperature"]
    temp_summary["temperature_range"] = _safe_float(
        weekly_temp.get("max"), temp_summary.get("temperature_range", 0.0)
    ) - _safe_float(weekly_temp.get("min"), 0.0)

    daily_mean = temp.get("daily_mean") or temp.get("daily") or []
    if daily_mean:
        day_names = _day_names()
        temp_summary["daily_mean_temperatures"] = [
            {"day": day_names[i], "mean": _safe_float(val, 0.0)}
            for i, val in enumerate(daily_mean[:7])
        ]
        max_val = max(daily_mean[:7])
        min_val = min(daily_mean[:7])
        max_day = day_names[daily_mean.index(max_val)]
        min_day = day_names[daily_mean.index(min_val)]
        temp_summary["maximum_temperature"] = {"value": _safe_float(max_val, 0.0), "day": max_day}
        temp_summary["minimum_temperature"] = {"value": _safe_float(min_val, 0.0), "day": min_day}

    temp_outlook["county_level_summary"] = temp_summary
    report["temperature_outlook"] = temp_outlook

    # Wind outlook updates
    wind_outlook = report.get("wind_outlook", {})
    wind_summary = wind_outlook.get("county_level_summary", {})
    wind_summary["mean_wind_speed"] = _safe_float(
        weekly_wind.get("mean_speed"), wind_summary.get("mean_wind_speed", 0.0)
    )
    wind_summary["dominant_wind_direction"] = summary_stats["dominant_wind_direction"]
    wind_summary["maximum_gust"] = {
        "value": _safe_float(weekly_wind.get("max_gust"), wind_summary.get("maximum_gust", {}).get("value", 0.0)),
        "day": wind_summary.get("maximum_gust", {}).get("day", "Wednesday"),
    }

    daily_peak = wind.get("daily_peak") or []
    if daily_peak:
        wind_summary["daily_peak_wind_speeds"] = [
            {"day": _day_names()[i], "speed": _safe_float(val, 0.0)}
            for i, val in enumerate(daily_peak[:7])
        ]

    wind_outlook["county_level_summary"] = wind_summary
    report["wind_outlook"] = wind_outlook

    # Sync metadata/disclaimers generation timestamp
    meta = report.get("metadata_and_disclaimers", {}).get("generation_metadata", {})
    meta["report_generation_timestamp"] = datetime.utcnow().isoformat() + "Z"

    # Update cover page data source if provided
    data_source = raw_payload.get("metadata", {}).get("data_source")
    if data_source:
        cover["generation_metadata"]["data_source"] = data_source

    logger.info(
        "report_template_built",
        county=county_name,
        week=week_number,
        year=year,
        include_observations=include_observations,
        has_raw_data=bool(raw_data),
    )

    return report

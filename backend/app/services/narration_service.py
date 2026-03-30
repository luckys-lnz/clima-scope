import io
import json
import logging
import re
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)

VARIABLE_COLUMN_ALIASES: Dict[str, List[str]] = {
    "rainfall": [
        "rain",
        "rainfall",
        "precip",
        "precipitation",
        "precipitation_sum",
        "rr",
        "rain_mm",
    ],
    "tmin": [
        "tmin",
        "min_temp",
        "minimum_temperature",
        "temperature_2m_min",
        "temp_min",
        "tn",
    ],
    "tmax": [
        "tmax",
        "max_temp",
        "maximum_temperature",
        "temperature_2m_max",
        "temp_max",
        "tx",
    ],
    "wind": [
        "wind",
        "wind_speed",
        "windspeed",
        "wind_speed_10m_max",
        "wind_gusts_10m_max",
        "gust",
        "ff",
    ],
    "humidity": ["humidity", "rh", "relative_humidity"],
    "pressure": ["pressure", "pres", "atmospheric_pressure"],
}


def _find_best_column(df: pd.DataFrame, aliases: List[str]) -> Optional[str]:
    lower_map = {str(col).lower().strip(): str(col) for col in df.columns}

    # Exact alias match first
    for alias in aliases:
        if alias in lower_map:
            return lower_map[alias]

    # Then partial match against any column name
    for alias in aliases:
        for lower_col, original_col in lower_map.items():
            if alias in lower_col:
                return original_col

    return None


def summarize_observation_data(
    csv_bytes: bytes,
    requested_variables: List[str],
) -> Dict[str, Any]:
    df = pd.read_csv(io.BytesIO(csv_bytes))

    summary: Dict[str, Any] = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": [str(c) for c in df.columns],
        "variables": {},
    }

    for variable in requested_variables:
        aliases = VARIABLE_COLUMN_ALIASES.get(variable, [variable])
        column = _find_best_column(df, aliases)

        if not column:
            summary["variables"][variable] = {
                "column": None,
                "available": False,
            }
            continue

        numeric_series = pd.to_numeric(df[column], errors="coerce").dropna()

        if numeric_series.empty:
            summary["variables"][variable] = {
                "column": column,
                "available": True,
                "non_null_count": 0,
                "numeric": False,
            }
            continue

        summary["variables"][variable] = {
            "column": column,
            "available": True,
            "numeric": True,
            "non_null_count": int(numeric_series.shape[0]),
            "mean": round(float(numeric_series.mean()), 2),
            "min": round(float(numeric_series.min()), 2),
            "max": round(float(numeric_series.max()), 2),
            "sum": round(float(numeric_series.sum()), 2),
        }

    return summary


def _fallback_narration(county_name: str, period_text: str) -> Dict[str, str]:
    return {
        "weekly_summary_text": (
            f"This is an automatically generated weekly weather summary for {county_name} "
            f"for the period {period_text}. Observation and map inputs were processed, "
            "but AI narration was unavailable, so this summary is a fallback."
        ),
        "marine_summary_text": (
            "Marine weather details are not currently synthesized in this workflow. "
            "Please consult official marine forecasts where applicable."
        ),
        "source": "fallback",
    }


def _marine_condition_phrase(min_wind: float, max_wind: float) -> str:
    if max_wind <= 7:
        return "Calm to slight"
    if max_wind <= 16:
        return "Slight to moderate"
    if max_wind <= 21:
        return "Moderate"
    # Keep key bulletin guidance aligned with the expected narrative style:
    # e.g. 17-26 knots -> "Moderate to rough".
    if min_wind >= 17 and max_wind <= 30:
        return "Moderate to rough"
    if min_wind >= 22 or max_wind >= 34:
        return "Rough to very rough"
    if min_wind >= 14 and max_wind >= 22:
        return "Moderate to rough"
    return "Slight to rough"


def _build_marine_summary_from_daily_wind(marine_daily_wind: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(marine_daily_wind, dict) or not marine_daily_wind:
        return None

    values: List[float] = []
    for raw in marine_daily_wind.values():
        values += [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(raw))]

    if not values:
        return None

    min_wind = min(values)
    max_wind = max(values)
    condition = _marine_condition_phrase(min_wind, max_wind)
    return (
        f"{condition} ocean conditions are expected this week with wind speeds "
        f"ranging from {min_wind:.0f}-{max_wind:.0f} knots across Kenyan waters. "
        "Marine users are advised to exercise caution."
    )


def _extract_marine_range(text: str) -> Optional[tuple[float, float]]:
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)\s*knots?", text, flags=re.IGNORECASE)
    if not match:
        return None
    start = float(match.group(1))
    end = float(match.group(2))
    return (min(start, end), max(start, end))


def _marine_summary_needs_correction(
    text: str,
    marine_daily_wind: Optional[Dict[str, Any]],
) -> bool:
    if not text:
        return True

    values: List[float] = []
    for raw in (marine_daily_wind or {}).values():
        values += [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(raw))]
    if not values:
        return False

    expected_min = round(min(values))
    expected_max = round(max(values))
    lowered = text.lower()

    # Marine section must refer to Kenyan waters, not county-level context.
    if "kenyan waters" not in lowered:
        return True
    if "county" in lowered:
        return True

    stated = _extract_marine_range(text)
    if not stated:
        return True
    stated_min = round(stated[0])
    stated_max = round(stated[1])
    return stated_min != expected_min or stated_max != expected_max


def _fallback_narration_with_marine(
    county_name: str,
    period_text: str,
    marine_daily_wind: Optional[Dict[str, Any]],
) -> Dict[str, str]:
    fallback = _fallback_narration(county_name, period_text)
    marine_summary = _build_marine_summary_from_daily_wind(marine_daily_wind)
    if marine_summary:
        fallback["marine_summary_text"] = marine_summary
    return fallback


def _extract_json(text: str) -> Dict[str, Any]:
    stripped = text.strip()

    # Direct JSON
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # JSON fenced in markdown
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, flags=re.DOTALL)
    if fence_match:
        return json.loads(fence_match.group(1))

    # First object-looking block
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(stripped[start : end + 1])

    raise ValueError("Could not parse narration JSON response")


async def _generate_openai_narration(
    system_prompt: str,
    user_prompt: str,
) -> Dict[str, str]:
    model = "gpt-4o-mini"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()

    content = result["choices"][0]["message"]["content"]
    parsed = _extract_json(content)

    return {
        "weekly_summary_text": str(parsed.get("weekly_summary_text", "")).strip(),
        "marine_summary_text": str(parsed.get("marine_summary_text", "")).strip(),
        "source": "openai",
    }


async def _generate_anthropic_narration(
    system_prompt: str,
    user_prompt: str,
) -> Dict[str, str]:
    model = "claude-3-5-haiku-latest"
    headers = {
        "x-api-key": settings.ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 800,
        "temperature": 0.3,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt},
        ],
    }

    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()

    blocks = result.get("content", [])
    text = "\n".join(block.get("text", "") for block in blocks if block.get("type") == "text")
    parsed = _extract_json(text)

    return {
        "weekly_summary_text": str(parsed.get("weekly_summary_text", "")).strip(),
        "marine_summary_text": str(parsed.get("marine_summary_text", "")).strip(),
        "source": "anthropic",
    }


async def generate_report_narration(
    county_name: str,
    week_number: int,
    year: int,
    report_start_at: str,
    report_end_at: str,
    selected_variables: List[str],
    observation_summary: Dict[str, Any],
    map_context: List[Dict[str, str]],
    marine_daily_wind: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    period_text = f"{report_start_at} to {report_end_at}"

    system_prompt = (
        "You are a county meteorological analyst. "
        "Write concise, factual weekly weather narration from structured data. "
        "Do not invent unavailable values. "
        "Return only JSON with keys: weekly_summary_text, marine_summary_text."
    )

    prompt_payload = {
        "county_name": county_name,
        "week_number": week_number,
        "year": year,
        "report_period": {
            "start": report_start_at,
            "end": report_end_at,
        },
        "selected_variables": selected_variables,
        "observation_summary": observation_summary,
        "generated_maps": map_context,
        "marine_data": {
            "daily_wind": marine_daily_wind or {},
        },
        "requirements": {
            "weekly_summary_text": (
                "120-220 words. Mention key tendencies for provided variables, "
                "uncertainties when data missing, and practical impacts."
            ),
            "marine_summary_text": (
                "40-90 words. Use marine_data.daily_wind values to summarize marine "
                "conditions and quote the observed weekly wind-speed range in knots. "
                "This section is for Kenyan waters (marine domain), not county-level wording. "
                "If marine_data.daily_wind is empty, state this clearly and provide "
                "a cautious advisory sentence."
            ),
        },
    }
    user_prompt = json.dumps(prompt_payload, ensure_ascii=True)

    try:
        provider = (settings.AI_PROVIDER or "openai").lower().strip()

        if provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            narration = await _generate_anthropic_narration(system_prompt, user_prompt)
        elif settings.OPENAI_API_KEY:
            narration = await _generate_openai_narration(system_prompt, user_prompt)
        else:
            logger.warning("ai_narration_no_provider_or_key_configured")
            return _fallback_narration_with_marine(county_name, period_text, marine_daily_wind)

        if not narration.get("weekly_summary_text"):
            raise ValueError("Missing weekly_summary_text")
        if not narration.get("marine_summary_text"):
            raise ValueError("Missing marine_summary_text")

        marine_summary = _build_marine_summary_from_daily_wind(marine_daily_wind)
        if marine_summary:
            marine_text = narration.get("marine_summary_text", "")
            if (
                not marine_text
                or "no marine data" in marine_text.lower()
                or "not currently synthesized" in marine_text.lower()
                or _marine_summary_needs_correction(marine_text, marine_daily_wind)
            ):
                narration["marine_summary_text"] = marine_summary

        return narration
    except Exception as exc:
        logger.exception("ai_narration_generation_failed", extra={"error": str(exc)})
        return _fallback_narration_with_marine(county_name, period_text, marine_daily_wind)

from __future__ import annotations

from datetime import date
from typing import Dict, List, Tuple

import httpx


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def _iso_date(value: str) -> str:
    return date.fromisoformat(value).isoformat()


def fetch_daily_forecast(
    latitude: float,
    longitude: float,
    report_start_at: str,
    report_end_at: str,
) -> Dict[str, List]:
    params = {
        "latitude": round(float(latitude), 6),
        "longitude": round(float(longitude), 6),
        "start_date": _iso_date(report_start_at),
        "end_date": _iso_date(report_end_at),
        "timezone": "Africa/Nairobi",
        "daily": ",".join(
            [
                "temperature_2m_max",
                "temperature_2m_min",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "wind_direction_10m_dominant",
                "precipitation_sum",
                "precipitation_probability_max",
                "weather_code",
            ]
        ),
    }
    response = httpx.get(OPEN_METEO_FORECAST_URL, params=params, timeout=25.0)
    response.raise_for_status()
    payload = response.json()
    return payload.get("daily", {})


def summarize_daily_forecast_by_day(
    daily_payload: Dict[str, List],
) -> Dict[str, Dict[str, str]]:
    dates = daily_payload.get("time", [])
    tmax = daily_payload.get("temperature_2m_max", [])
    tmin = daily_payload.get("temperature_2m_min", [])
    wind = daily_payload.get("wind_speed_10m_max", [])
    gust = daily_payload.get("wind_gusts_10m_max", [])
    rain = daily_payload.get("precipitation_sum", [])
    rain_prob = daily_payload.get("precipitation_probability_max", [])

    summary: Dict[str, Dict[str, str]] = {}
    for idx, dt in enumerate(dates):
        day = date.fromisoformat(dt)
        day_key = day.strftime("%a")
        tmax_value = tmax[idx] if idx < len(tmax) else None
        tmin_value = tmin[idx] if idx < len(tmin) else None
        wind_value = wind[idx] if idx < len(wind) else None
        gust_value = gust[idx] if idx < len(gust) else None
        rain_value = rain[idx] if idx < len(rain) else None
        rain_prob_value = rain_prob[idx] if idx < len(rain_prob) else None

        summary[day_key] = {
            "maximum_temperature": f"{tmax_value:.1f}°C" if tmax_value is not None else "N/A",
            "minimum_temperature": f"{tmin_value:.1f}°C" if tmin_value is not None else "N/A",
            "winds": (
                f"Max {wind_value:.1f} km/h, Gust {gust_value:.1f} km/h"
                if wind_value is not None and gust_value is not None
                else "N/A"
            ),
            "rainfall_distribution": (
                f"{rain_value:.1f} mm (PoP {rain_prob_value:.0f}%)"
                if rain_value is not None and rain_prob_value is not None
                else "N/A"
            ),
        }
    return summary


def centroid_from_rows(
    latitudes: List[float],
    longitudes: List[float],
) -> Tuple[float, float]:
    if not latitudes or not longitudes:
        raise ValueError("No latitude/longitude values available for centroid")
    return (sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes))

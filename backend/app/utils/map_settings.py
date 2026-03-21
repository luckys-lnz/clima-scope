"""Shared helpers for validating and defaulting map styling preferences."""
from typing import Any, Mapping, Optional, TypedDict

VALID_BORDER_STYLES = {"solid", "dashed", "dotted"}


class MapSettings(TypedDict):
    show_constituencies: bool
    show_wards: bool
    show_labels: bool
    label_font_size: int
    constituency_border_color: str
    constituency_border_width: float
    constituency_border_style: str
    ward_border_color: str
    ward_border_width: float
    ward_border_style: str


DEFAULT_MAP_SETTINGS: MapSettings = {
    "show_constituencies": True,
    "show_wards": True,
    "show_labels": True,
    "label_font_size": 12,
    "constituency_border_color": "#1e293b",
    "constituency_border_width": 1.2,
    "constituency_border_style": "solid",
    "ward_border_color": "#2563eb",
    "ward_border_width": 0.9,
    "ward_border_style": "dashed",
}


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "on"}


def _coerce_positive_float(value: Any, default: float) -> float:
    try:
        candidate = float(value)
    except (TypeError, ValueError):
        return default
    if candidate <= 0:
        return default
    return candidate


def _coerce_int(value: Any, default: int) -> int:
    try:
        candidate = int(float(value))
    except (TypeError, ValueError):
        return default
    if candidate < 6:
        return 6
    if candidate > 48:
        return 48
    return candidate


def _coerce_string(value: Any, default: str) -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _coerce_border_style(value: Any, default: str) -> str:
    style = _coerce_string(value, default).lower()
    return style if style in VALID_BORDER_STYLES else default


def sanitize_map_settings(payload: Optional[Mapping[str, Any]]) -> MapSettings:
    """Normalize raw settings coming from the database or client."""
    row = payload or {}
    return {
        "show_constituencies": _coerce_bool(
            row.get("show_constituencies"), DEFAULT_MAP_SETTINGS["show_constituencies"]
        ),
        "show_wards": _coerce_bool(row.get("show_wards"), DEFAULT_MAP_SETTINGS["show_wards"]),
        "show_labels": _coerce_bool(row.get("show_labels"), DEFAULT_MAP_SETTINGS["show_labels"]),
        "label_font_size": _coerce_int(row.get("label_font_size"), DEFAULT_MAP_SETTINGS["label_font_size"]),
        "constituency_border_color": _coerce_string(
            row.get("constituency_border_color"), DEFAULT_MAP_SETTINGS["constituency_border_color"]
        ),
        "constituency_border_width": _coerce_positive_float(
            row.get("constituency_border_width"), DEFAULT_MAP_SETTINGS["constituency_border_width"]
        ),
        "constituency_border_style": _coerce_border_style(
            row.get("constituency_border_style"), DEFAULT_MAP_SETTINGS["constituency_border_style"]
        ),
        "ward_border_color": _coerce_string(
            row.get("ward_border_color"), DEFAULT_MAP_SETTINGS["ward_border_color"]
        ),
        "ward_border_width": _coerce_positive_float(
            row.get("ward_border_width"), DEFAULT_MAP_SETTINGS["ward_border_width"]
        ),
        "ward_border_style": _coerce_border_style(
            row.get("ward_border_style"), DEFAULT_MAP_SETTINGS["ward_border_style"]
        ),
    }

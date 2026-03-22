"""Utility helpers for loading county metadata from the database."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.supabase import get_supabase_admin

COUNTY_COLUMNS: List[str] = [
    "id",
    "code",
    "name",
    "centroid_lat",
    "centroid_lon",
    "constituencies",
    "wards",
]


def _normalize_name(value: Any) -> str:
    return str(value or "").strip().lower()


def _fetch_all_counties(supabase_admin=None) -> List[Dict[str, Any]]:
    supabase_admin = supabase_admin or get_supabase_admin()
    response = (
        supabase_admin.table("counties")
        .select(",".join(COUNTY_COLUMNS))
        .execute()
    )
    return response.data or []


def _match_county_by_name(name: str, counties: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    normalized = _normalize_name(name)
    if not normalized:
        return None
    for county in counties:
        if _normalize_name(county.get("name")) == normalized:
            return county
    return None


def _match_county_by_code(code: str, counties: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    digits = "".join(ch for ch in str(code or "") if ch.isdigit())
    if not digits:
        return None
    padded = digits.zfill(3)
    for county in counties:
        if str(county.get("code") or "").zfill(3) == padded:
            return county
    return None


def get_county_by_name(name: str, supabase_admin=None) -> Optional[Dict[str, Any]]:
    counties = _fetch_all_counties(supabase_admin)
    return _match_county_by_name(name, counties)


def get_county_by_code(code: str, supabase_admin=None) -> Optional[Dict[str, Any]]:
    counties = _fetch_all_counties(supabase_admin)
    return _match_county_by_code(code, counties)


def get_county_by_identifier(identifier: str, supabase_admin=None) -> Optional[Dict[str, Any]]:
    counties = _fetch_all_counties(supabase_admin)
    county = _match_county_by_code(identifier, counties)
    if county:
        return county
    return _match_county_by_name(identifier, counties)

from app.utils.geospatial_compat import ensure_fiona_path

ensure_fiona_path()

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.setting import (
    SettingsResponse,
    UpdateSettingsRequest,
    SharedFileResponse,
    MapPreviewResponse,
    MapPreviewLabel,
)
from app.api.v1.auth import get_current_user
from app.core.supabase import get_supabase_anon, get_supabase_admin
from app.core.config import settings
from datetime import datetime
import logging
from typing import Any, Dict, Optional, List
import os
import tempfile
import shutil
import geopandas as gpd
from shapely.geometry import mapping

from app.utils.map_settings import DEFAULT_MAP_SETTINGS, sanitize_map_settings

router = APIRouter(tags=["setting"])
logger = logging.getLogger(__name__)



def _resolve_column(columns: List[str], candidates: List[str]) -> Optional[str]:
    lower_to_original = {str(col).strip().lower(): str(col) for col in columns}
    for candidate in candidates:
        key = candidate.lower()
        if key in lower_to_original:
            return lower_to_original[key]
    for candidate in candidates:
        key = candidate.lower()
        for lower_name, original in lower_to_original.items():
            if key in lower_name:
                return original
    return None


def _normalize_county_key(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = " ".join(str(value).strip().split())
    lower = normalized.lower()
    if lower.endswith(" county"):
        lower = lower[:-7].strip()
    return lower


def _simplify_geometry(geometry, tolerance: float):
    if geometry is None or geometry.is_empty:
        return geometry
    if tolerance <= 0:
        return geometry
    try:
        return geometry.simplify(tolerance, preserve_topology=True)
    except Exception:
        return geometry


@router.get("", response_model=SettingsResponse)
async def get_settings(user=Depends(get_current_user)):
    """
    Get user settings and available PDF templates
    """
    supabase = get_supabase_anon()
    user_id = user.id if hasattr(user, "id") else user.get("id")
    
    # Get all templates from shared_files
    try:
        templates_response = supabase.table("shared_files")\
            .select("id, file_name, file_type, upload_date, file_path")\
            .in_("file_type", ["templates", "template"])\
            .execute()
        
        templates_data = templates_response.data or []
        templates = [SharedFileResponse(**t) for t in templates_data]
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        templates_data = []
        templates = []
    
    # Get user's assigned template and map display preferences from user_settings
    try:
        user_settings_response = supabase.table("user_settings")\
            .select(
                "pdf_template_id, show_constituencies, show_wards, "
                "show_constituency_labels, show_ward_labels, "
                "constituency_label_font_size, ward_label_font_size, "
                "constituency_border_color, constituency_border_width, constituency_border_style, "
                "ward_border_color, ward_border_width, ward_border_style"
            )\
            .eq("user_id", user_id)\
            .order("updated_at", desc=True)\
            .limit(1)\
            .execute()
        
        user_settings_results = user_settings_response.data or []
        user_settings_row = user_settings_results[0] if user_settings_results else {}
        selected_template_id = user_settings_row.get("pdf_template_id")
        map_settings = sanitize_map_settings(user_settings_row)
    except Exception as e:
        logger.error(f"Error fetching user settings: {e}")
        selected_template_id = None
        map_settings = dict(DEFAULT_MAP_SETTINGS)
    
    # Find the selected template details
    selected_template = None
    if selected_template_id and templates_data:
        selected_template = next(
            (t for t in templates_data if str(t.get("id")) == str(selected_template_id)), 
            None
        )
    
    # Get shapefile path - assuming there's only one .shp file
    try:
        shapefiles_response = supabase.table("shared_files")\
            .select("id, file_name, file_path")\
            .in_("file_type", ["shapefile", "shapefiles"])\
            .execute()
        
        shapefiles_data = shapefiles_response.data or []
        
        # Prefer the .shp file; fallback to first available shapefile row
        shapefile = next(
            (s for s in shapefiles_data if s.get("file_name", "").endswith('.shp')),
            shapefiles_data[0] if shapefiles_data else None
        )
    except Exception as e:
        logger.error(f"Error fetching shapefiles: {e}")
        shapefile = None
    
    return SettingsResponse(
        shapefile_name=shapefile.get("file_name") if shapefile else "Default Shapefile",
        shapefile_path=shapefile.get("file_path") if shapefile else "",
        templates=templates,
        user_settings={
            "pdf_template_id": selected_template_id,
            "selected_template": SharedFileResponse(**selected_template) if selected_template else None,
            **map_settings,
        },
    )


@router.get("/preview-geometry", response_model=MapPreviewResponse)
async def get_preview_geometry(
    county: Optional[str] = None,
    user=Depends(get_current_user),
):
    """
    Return simplified county boundaries for the settings page preview map.
    """
    supabase_admin = get_supabase_admin()
    user_id = user.id if hasattr(user, "id") else user.get("id")

    if not county:
        try:
            profile_response = supabase_admin.table("profiles")\
                .select("county")\
                .eq("id", user_id)\
                .limit(1)\
                .execute()
            profile_row = profile_response.data[0] if profile_response.data else {}
            county = profile_row.get("county")
        except Exception as exc:
            logger.error("profile_county_fetch_failed", extra={"error": str(exc)})
            county = None

    if not county:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="County not set for this user. Update your profile to enable map preview.",
        )

    shapefile_records = None
    try:
        shapefile_records = supabase_admin.table("shared_files")\
            .select("file_name, file_path, file_type")\
            .in_("file_type", ["shapefile", "shapefiles"])\
            .execute()
    except Exception as exc:
        logger.error("preview_shapefile_fetch_failed", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load shapefile metadata",
        )

    components = shapefile_records.data or []
    if not components:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shapefile found. Please contact an administrator.",
        )

    temp_dir = tempfile.mkdtemp(prefix=f"preview_shapefile_{user_id}_")
    local_shapefile_path = None
    try:
        for component in components:
            file_path = component.get("file_path")
            file_name = component.get("file_name")
            if not file_path or not file_name:
                continue
            try:
                file_bytes = supabase_admin.storage.from_(settings.SUPABASE_STORAGE_BUCKET).download(file_path)
            except Exception as exc:
                logger.warning("preview_shapefile_download_failed", extra={"error": str(exc), "file": file_name})
                continue
            local_path = os.path.join(temp_dir, file_name)
            with open(local_path, "wb") as handle:
                handle.write(file_bytes)
            if file_name.endswith(".shp"):
                local_shapefile_path = local_path

        if not local_shapefile_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shapefile (.shp) component not found in storage.",
            )

        wards = gpd.read_file(local_shapefile_path)
        county_col = _resolve_column(wards.columns, ["county", "county_name", "adm1_name"])
        ward_col = _resolve_column(wards.columns, ["ward", "ward_name", "adm3_name", "name"])
        constituency_col = _resolve_column(
            wards.columns,
            ["sub_county", "subcounty", "const", "constituency", "adm2_name"],
        )

        if not county_col:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="County column not found in shapefile.",
            )

        county_key = _normalize_county_key(county)
        ward_counties = wards[county_col].astype(str).map(_normalize_county_key)
        county_wards = wards[ward_counties == county_key].copy()
        if county_wards.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"County '{county}' not found in shapefile.",
            )

        county_geometry = county_wards.dissolve(by=county_col).geometry.unary_union
        if county_geometry is None or county_geometry.is_empty:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="County geometry could not be derived from shapefile.",
            )

        bbox = list(county_geometry.bounds)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        tolerance = max(width, height) * 0.002 if width > 0 and height > 0 else 0.0

        county_geom = _simplify_geometry(county_geometry, tolerance)
        county_geojson = mapping(county_geom)

        constituency_geojson = None
        if constituency_col:
            constituency_geom = county_wards.dissolve(by=constituency_col).boundary.unary_union
            constituency_geom = _simplify_geometry(constituency_geom, tolerance)
            if constituency_geom and not constituency_geom.is_empty:
                constituency_geojson = mapping(constituency_geom)

        ward_geojson = None
        if ward_col:
            ward_geom = county_wards.boundary.unary_union
            ward_geom = _simplify_geometry(ward_geom, tolerance)
            if ward_geom and not ward_geom.is_empty:
                ward_geojson = mapping(ward_geom)

        labels: List[MapPreviewLabel] = []
        if ward_col:
            for _, row in county_wards.head(40).iterrows():
                try:
                    point = row.geometry.representative_point()
                    name = str(row[ward_col])[:28]
                    labels.append(
                        MapPreviewLabel(name=name, lon=float(point.x), lat=float(point.y), type="ward")
                    )
                except Exception:
                    continue
        if constituency_col:
            constituency_labels = county_wards.dissolve(by=constituency_col)
            for _, row in constituency_labels.iterrows():
                try:
                    centroid = row.geometry.representative_point()
                    name = str(row.name)[:28]
                    labels.append(
                        MapPreviewLabel(
                            name=name,
                            lon=float(centroid.x),
                            lat=float(centroid.y),
                            type="constituency",
                        )
                    )
                except Exception:
                    continue

        return MapPreviewResponse(
            county=str(county),
            bbox=bbox,
            county_geometry=county_geojson,
            constituency_boundaries=constituency_geojson,
            ward_boundaries=ward_geojson,
            labels=labels,
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@router.put("", response_model=dict)
async def update_settings(
    payload: UpdateSettingsRequest,
    user=Depends(get_current_user),
):
    """
    Update user's PDF template and map preferences
    """
    try:
        supabase = get_supabase_anon()
        
        user_id = user.id if hasattr(user, "id") else user.get("id")
        
        # Validate template exists if provided
        if payload.pdf_template_id:
            try:
                template_check = supabase.table("shared_files")\
                    .select("id")\
                    .eq("id", str(payload.pdf_template_id))\
                    .in_("file_type", ["templates", "template"])\
                    .execute()
                
                if not template_check.data:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Selected template not found"
                    )
            except Exception as e:
                logger.error(f"Error validating template: {e}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Selected template not found"
                )

        # Check if user settings exist
        existing_response = supabase.table("user_settings")\
            .select("id")\
            .eq("user_id", user_id)\
            .order("updated_at", desc=True)\
            .limit(1)\
            .execute()
        
        existing = existing_response.data or []
        effective_map_settings = sanitize_map_settings({
            "show_constituencies": payload.show_constituencies,
            "show_wards": payload.show_wards,
            "show_constituency_labels": payload.show_constituency_labels,
            "show_ward_labels": payload.show_ward_labels,
            "constituency_label_font_size": payload.constituency_label_font_size,
            "ward_label_font_size": payload.ward_label_font_size,
            "constituency_border_color": payload.constituency_border_color,
            "constituency_border_width": payload.constituency_border_width,
            "constituency_border_style": payload.constituency_border_style,
            "ward_border_color": payload.ward_border_color,
            "ward_border_width": payload.ward_border_width,
            "ward_border_style": payload.ward_border_style,
        })
        
        update_data = {
            "pdf_template_id": str(payload.pdf_template_id) if payload.pdf_template_id else None,
            "updated_at": datetime.utcnow().isoformat(),
            **effective_map_settings,
        }
        
        if existing:
            # Update existing
            supabase.table("user_settings")\
                .update(update_data)\
                .eq("id", existing[0]["id"])\
                .execute()
        else:
            # Insert new
            insert_data = {
                "user_id": str(user_id),
                **update_data
            }
            supabase.table("user_settings")\
                .insert(insert_data)\
                .execute()

        logger.info(
            f"Updated settings for user {user_id}: template={payload.pdf_template_id}, "
            f"show_constituencies={effective_map_settings['show_constituencies']}, "
            f"show_wards={effective_map_settings['show_wards']}, "
            f"show_constituency_labels={effective_map_settings['show_constituency_labels']}, "
            f"show_ward_labels={effective_map_settings['show_ward_labels']}, "
            f"constituency_label_font_size={effective_map_settings['constituency_label_font_size']}, "
            f"ward_label_font_size={effective_map_settings['ward_label_font_size']}"
        )
        
        return {
            "success": True,
            "message": "Settings updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        user_id_val = user.id if hasattr(user, "id") else getattr(user, "id", "unknown")
        logger.error(f"Failed to update settings for user {user_id_val}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings. Please try again."
        )

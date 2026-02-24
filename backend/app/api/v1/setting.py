from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.setting import (
    SettingsResponse,
    UpdateSettingsRequest,
    UserSettingsResponse,
    SharedFileResponse,
)
from app.api.v1.auth import get_current_user
from app.core.supabase import get_supabase_anon
from uuid import UUID
import logging
from typing import List, Optional

router = APIRouter(tags=["setting"])
logger = logging.getLogger(__name__)


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
            .eq("file_type", "templates")\
            .execute()
        
        templates_data = templates_response.data or []
        templates = [SharedFileResponse(**t) for t in templates_data]
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        templates_data = []
        templates = []
    
    # Get user's assigned template from user_settings
    try:
        user_settings_response = supabase.table("user_settings")\
            .select("pdf_template_id")\
            .eq("user_id", user_id)\
            .execute()
        
        user_settings_results = user_settings_response.data or []
        selected_template_id = user_settings_results[0].get("pdf_template_id") if user_settings_results else None
    except Exception as e:
        logger.error(f"Error fetching user settings: {e}")
        selected_template_id = None
    
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
            .eq("file_type", "shapefile")\
            .execute()
        
        shapefiles_data = shapefiles_response.data or []
        
        # Find the .shp file
        shapefile = next(
            (s for s in shapefiles_data if s.get("file_name", "").endswith('.shp')),
            None
        )
    except Exception as e:
        logger.error(f"Error fetching shapefiles: {e}")
        shapefile = None
    
    return SettingsResponse(
        shapefile_name=shapefile.get("file_name") if shapefile else "Default Shapefile",
        shapefile_path=shapefile.get("file_path") if shapefile else "/default/path.shp",
        templates=templates,
        user_settings={
            "pdf_template_id": selected_template_id,
            "selected_template": SharedFileResponse(**selected_template) if selected_template else None,
        },
    )


@router.put("", response_model=dict)
async def update_settings(
    payload: UpdateSettingsRequest,
    user=Depends(get_current_user),
):
    """
    Update user's PDF template preference
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
                    .eq("file_type", "templates")\
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
            .select("user_id")\
            .eq("user_id", user_id)\
            .execute()
        
        existing = existing_response.data
        
        update_data = {
            "pdf_template_id": str(payload.pdf_template_id) if payload.pdf_template_id else None,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if existing:
            # Update existing
            supabase.table("user_settings")\
                .update(update_data)\
                .eq("user_id", user_id)\
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

        logger.info(f"Updated settings for user {user_id}: template={payload.pdf_template_id}")
        
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

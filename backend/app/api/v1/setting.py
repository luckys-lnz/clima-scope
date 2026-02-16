from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.setting import (
    SettingsResponse,
    UpdateSettingsRequest,
    UserSettingsResponse,
    SharedFileResponse,
)
from app.api.v1.auth import get_current_user
from app.core.supabase import get_db_client
from uuid import UUID
import logging
from typing import List

router = APIRouter(tags=["setting"])
logger = logging.getLogger(__name__)


@router.get("", response_model=SettingsResponse)
async def get_settings(user=Depends(get_current_user)):
    """
    Get user settings and available PDF templates
    """
    db = get_db_client()
    user_id = user.get("id") if isinstance(user, dict) else user.id
    
    # Get all templates from shared_files
    templates_data = await db.select(
        table="shared_files",
        filters={"file_type": "eq.templates"},
        columns="id, file_name, file_type, upload_date, file_path"
    ) or []
    
    templates = [SharedFileResponse(**t) for t in templates_data]
    
    # Get user's assigned template from user_settings
    user_settings_results = await db.select(
        table="user_settings",
        filters={"user_id": f"eq.{user_id}"},
        columns="pdf_template_id"
    ) or []
    
    selected_template_id = user_settings_results[0].get("pdf_template_id") if user_settings_results else None
    
    # Find the selected template details
    selected_template = None
    if selected_template_id:
        selected_template = next(
            (t for t in templates_data if str(t.get("id")) == str(selected_template_id)), 
            None
        )
    
    # Get shapefile path - assuming there's only one .shp file
    shapefiles_data = await db.select(
        table="shared_files",
        filters={"file_type": "eq.shapefile"},
        columns="id, file_name, file_path"
    ) or []
    
    # Find the .shp file
    shapefile = next(
        (s for s in shapefiles_data if s.get("file_name", "").endswith('.shp')),
        None
    )
    
    return SettingsResponse(
        shapefile_name=shapefile.get("file_name") if shapefile else "Default Shapefile",
        shapefile_path=shapefile.get("file_path") if shapefile else "/default/path.shp",
        templates=templates,
        user_settings={
            "pdf_template_id": selected_template_id,
            "selected_template": selected_template
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
        db = get_db_client()
        
        # FIX: Access user as dictionary
        user_id = user.get("id") if isinstance(user, dict) else user.id
        
        # Validate template exists if provided
        if payload.pdf_template_id:
            template_check = await db.select(
                table="shared_files",
                filters={
                    "id": f"eq.{payload.pdf_template_id}",
                    "file_type": "eq.template"
                },
                columns="id"
            )
            
            if not template_check:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Selected template not found"
                )

        # Check if user settings exist
        existing = await db.select(
            table="user_settings",
            filters={"user_id": f"eq.{user_id}"},  # Use user_id variable
            columns="user_id"
        )
        
        if existing:
            # Update existing
            await db.update(
                table="user_settings",
                filters={"user_id": f"eq.{user_id}"},
                data={
                    "pdf_template_id": str(payload.pdf_template_id) if payload.pdf_template_id else None,
                    "updated_at": "now()",
                }
            )
        else:
            # Insert new
            await db.insert(
                table="user_settings",
                data={
                    "user_id": str(user_id),
                    "pdf_template_id": str(payload.pdf_template_id) if payload.pdf_template_id else None,
                    "updated_at": "now()",
                }
            )

        logger.info(f"Updated settings for user {user_id}: template={payload.pdf_template_id}")
        
        return {
            "success": True,
            "message": "Settings updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", "unknown")
        logger.error(f"Failed to update settings for user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update settings. Please try again."
        )

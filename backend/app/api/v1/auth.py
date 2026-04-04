from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from httpx import QueryParams
import logging

from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    RefreshTokenRequest,
    AuthResponse,
    UserResponse,
    ProfileUpdateRequest,
)
from app.core.config import settings
from app.core.supabase import get_supabase_admin, get_supabase_anon
from app.services.profile_service import fetch_profile_for_user, get_user_email
from app.utils.map_settings import DEFAULT_MAP_SETTINGS

router = APIRouter(tags=["authentication"])
security = HTTPBearer()
logger = logging.getLogger(__name__)


def _fetch_user_by_email(supabase_admin, email: str) -> Optional[dict]:
    try:
        response = supabase_admin.auth.admin._request(
            "GET",
            "admin/users",
            query=QueryParams(email=email),
        )
    except Exception:
        return None

    try:
        payload = response.json()
    except ValueError:
        return None

    users = []
    if isinstance(payload, dict):
        if isinstance(payload.get("users"), list):
            users = payload["users"]
        elif isinstance(payload.get("data"), list):
            users = payload["data"]
        elif isinstance(payload.get("list"), list):
            users = payload["list"]
    elif isinstance(payload, list):
        users = payload

    for user in users:
        if not isinstance(user, dict):
            continue
        if user.get("email", "").lower() == email.lower():
            return user
    return None


def _ensure_default_user_settings(supabase_admin, user_id: str) -> None:
    if not user_id:
        return
    user_id = str(user_id)
    default_settings_payload = {
        "show_constituencies": DEFAULT_MAP_SETTINGS["show_constituencies"],
        "show_wards": DEFAULT_MAP_SETTINGS["show_wards"],
        "show_constituency_labels": DEFAULT_MAP_SETTINGS["show_constituency_labels"],
        "show_ward_labels": DEFAULT_MAP_SETTINGS["show_ward_labels"],
        "constituency_label_font_size": DEFAULT_MAP_SETTINGS["constituency_label_font_size"],
        "ward_label_font_size": DEFAULT_MAP_SETTINGS["ward_label_font_size"],
        "constituency_border_color": DEFAULT_MAP_SETTINGS["constituency_border_color"],
        "constituency_border_width": DEFAULT_MAP_SETTINGS["constituency_border_width"],
        "constituency_border_style": DEFAULT_MAP_SETTINGS["constituency_border_style"],
        "ward_border_color": DEFAULT_MAP_SETTINGS["ward_border_color"],
        "ward_border_width": DEFAULT_MAP_SETTINGS["ward_border_width"],
        "ward_border_style": DEFAULT_MAP_SETTINGS["ward_border_style"],
    }

    try:
        existing_response = (
            supabase_admin.table("user_settings")
            .select(
                "id, show_constituencies, show_wards, show_constituency_labels, show_ward_labels, "
                "constituency_label_font_size, ward_label_font_size, "
                "constituency_border_color, constituency_border_width, constituency_border_style, "
                "ward_border_color, ward_border_width, ward_border_style"
            )
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        existing_rows = existing_response.data or []
        if existing_rows:
            row = existing_rows[0]
            update_payload = {}
            for key, default_value in default_settings_payload.items():
                if row.get(key) is None:
                    update_payload[key] = default_value

            if update_payload:
                update_payload["updated_at"] = datetime.utcnow().isoformat()
                (
                    supabase_admin.table("user_settings")
                    .update(update_payload)
                    .eq("id", row["id"])
                    .execute()
                )
            return

        insert_payload = {"user_id": user_id, **default_settings_payload}
        supabase_admin.table("user_settings").insert(insert_payload).execute()
    except Exception as exc:
        message = str(exc).lower()
        # Safe to ignore if a concurrent request inserted the row first.
        if "duplicate" in message or "unique_user_settings" in message:
            return
        raise


def _ensure_profile_exists_for_auth_user(supabase_admin, auth_user: Any) -> Dict[str, Any]:
    profile = fetch_profile_for_user(supabase_admin, auth_user)
    if profile:
        return profile

    user_id = getattr(auth_user, "id", None) if auth_user is not None else None
    email = get_user_email(auth_user)
    if not user_id:
        return {}

    user_metadata = getattr(auth_user, "user_metadata", None) or {}
    full_name = ""
    if isinstance(user_metadata, dict):
        full_name = (
            str(
                user_metadata.get("full_name")
                or user_metadata.get("name")
                or user_metadata.get("display_name")
                or ""
            ).strip()
        )
    if not full_name and email and "@" in email:
        full_name = email.split("@", 1)[0]

    insert_payload: Dict[str, Any] = {
        "id": str(user_id),
        "full_name": full_name or "",
        "organization": "",
        "created_at": datetime.utcnow().isoformat(),
    }

    try:
        supabase_admin.table("profiles").insert(insert_payload).execute()
    except Exception as exc:
        message = str(exc).lower()
        # Another request may have created the profile concurrently.
        if "duplicate" not in message and "unique" not in message:
            raise

    return fetch_profile_for_user(supabase_admin, auth_user)

# -----------------------------
# Dependency: Get current user
# -----------------------------
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    supabase_admin = get_supabase_admin()
    supabase_anon = get_supabase_anon()

    try:
        user = supabase_anon.auth.get_user(credentials.credentials)
        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            _ensure_profile_exists_for_auth_user(supabase_admin, user.user)
        except Exception as exc:
            logger.error(
                "Failed to ensure profile row for user %s during auth dependency: %s",
                getattr(user.user, "id", None),
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize user profile",
            )

        user_id = user.user.id if hasattr(user.user, "id") else None
        if user_id:
            try:
                _ensure_default_user_settings(supabase_admin, user_id)
            except Exception as exc:
                logger.error(
                    "Failed to ensure default user settings for user %s during auth dependency: %s",
                    user_id,
                    str(exc),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to initialize default user settings",
                )
        return user.user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# -----------------------------
# SIGNUP - No session returned (email verification required)
# -----------------------------
@router.post("/signup")
async def signup(user_data: SignupRequest):
    supabase_admin = get_supabase_admin()
    existing_user = _fetch_user_by_email(supabase_admin, user_data.email)
    if existing_user:
        identities = existing_user.get("identities") or []
        oauth_providers = [
            identity.get("provider")
            for identity in identities
            if isinstance(identity, dict)
            and identity.get("provider")
            and identity.get("provider") != "email"
        ]

        if oauth_providers:
            provider_name = oauth_providers[0].replace("_", " ").title()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This email is linked to {provider_name} sign-in. Please continue with {provider_name}.",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account already exists for this email. Please log in instead.",
        )

    try:
        # Create auth user
        auth_resp = supabase_admin.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })

        if not auth_resp.user:
            raise HTTPException(status_code=400, detail="Signup failed")

        # Create profile
        try:
            trial_started_at = datetime.utcnow()
            trial_ends_at = trial_started_at + timedelta(days=settings.TRIAL_DAYS)
            supabase_admin.table("profiles").insert({
                "id": auth_resp.user.id,
                "full_name": user_data.full_name,
                "organization": user_data.organization,
                "county": user_data.county,
                "phone": user_data.phone,
                "created_at": datetime.utcnow().isoformat(),
                "trial_started_at": trial_started_at.isoformat(),
                "trial_ends_at": trial_ends_at.isoformat(),
                "trial_status": "active" if settings.TRIAL_ENABLED else "converted",
                "trial_converted_at": None if settings.TRIAL_ENABLED else datetime.utcnow().isoformat(),
            }).execute()
        except Exception as e:
            # Rollback user creation if profile fails
            supabase_admin.auth.admin.delete_user(auth_resp.user.id)
            raise HTTPException(status_code=400, detail=f"Profile creation failed: {str(e)}")

        try:
            _ensure_default_user_settings(supabase_admin, auth_resp.user.id)
        except Exception as e:
            supabase_admin.auth.admin.delete_user(auth_resp.user.id)
            raise HTTPException(status_code=400, detail=f"Default settings creation failed: {str(e)}")

        return {
            "success": True,
            "message": "Please check your email to verify your account",
            "user": {
                "id": auth_resp.user.id,
                "email": user_data.email,
                "full_name": user_data.full_name,
                "organization": user_data.organization,
                "county": user_data.county,
                "phone": user_data.phone
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Signup failed: {str(e)}")

# -----------------------------
# LOGIN - Returns session (user must be verified)
# -----------------------------
@router.post("/login", response_model=AuthResponse)
async def login(user_data: LoginRequest):
    supabase_admin = get_supabase_admin()
    supabase_anon = get_supabase_anon()

    try:
        auth_resp = supabase_anon.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })

        if not auth_resp.user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # Check if email is verified
        if not auth_resp.user.email_confirmed_at:
            raise HTTPException(
                status_code=401,
                detail="Please verify your email before logging in"
            )

        # Get user profile
        profile = fetch_profile_for_user(supabase_admin, auth_resp.user)

        return AuthResponse(
            success=True,
            access_token=auth_resp.session.access_token,
            refresh_token=auth_resp.session.refresh_token,
            expires_in=auth_resp.session.expires_in,
            user=UserResponse(
                id=auth_resp.user.id,
                email=auth_resp.user.email,
                full_name=profile.get("full_name", ""),
                organization=profile.get("organization", ""),
                prefix=profile.get("prefix"),
                title=profile.get("prefix"),
                county=profile.get("county"),
                phone=profile.get("phone"),
                job_title=profile.get("job_title"),
                station_name=profile.get("station_name"),
                station_address=profile.get("station_address"),
                signoff_email=profile.get("signoff_email"),
                secondary_email=profile.get("secondary_email"),
            )
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# -----------------------------
# LOGOUT
# -----------------------------
@router.post("/logout")
async def logout(user=Depends(get_current_user)):
    supabase = get_supabase_anon()
    try:
        supabase.auth.sign_out()
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Logout failed: {str(e)}")

# -----------------------------
# GET CURRENT USER
# -----------------------------
@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user=Depends(get_current_user)):
    supabase_admin = get_supabase_admin()
    profile = fetch_profile_for_user(supabase_admin, user)
    user_id = user.id if hasattr(user, "id") else user.get("id")

    try:
        _ensure_default_user_settings(supabase_admin, user_id)
    except Exception as exc:
        logger.warning("Failed to ensure default user settings for user %s: %s", user_id, str(exc))

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=profile.get("full_name", ""),
        organization=profile.get("organization", ""),
        prefix=profile.get("prefix"),
        title=profile.get("prefix"),
        county=profile.get("county"),
        phone=profile.get("phone"),
        job_title=profile.get("job_title"),
        station_name=profile.get("station_name"),
        station_address=profile.get("station_address"),
        signoff_email=profile.get("signoff_email"),
        secondary_email=profile.get("secondary_email"),
    )

# -----------------------------
# UPDATE PROFILE
# -----------------------------
@router.put("/profile", response_model=UserResponse)
async def update_profile(updates: ProfileUpdateRequest, user=Depends(get_current_user)):
    supabase_admin = get_supabase_admin()

    update_data = updates.model_dump(exclude_unset=True, exclude_none=True)
    # Accept both title and prefix from the client, but store under prefix.
    if "title" in update_data:
        update_data["prefix"] = update_data.pop("title")

    user_id = user.id if hasattr(user, "id") else user.get("id")
    profile = fetch_profile_for_user(supabase_admin, user)
    profile_id = profile.get("id")

    if update_data:
        try:
            if profile_id:
                supabase_admin.table("profiles")\
                    .update(update_data)\
                    .eq("id", profile_id)\
                    .execute()
            else:
                insert_payload = {"id": user_id}
                insert_payload.update(update_data)
                supabase_admin.table("profiles").insert(insert_payload).execute()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Profile update failed: {str(e)}")

    profile = fetch_profile_for_user(supabase_admin, user)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=profile.get("full_name", ""),
        organization=profile.get("organization", ""),
        prefix=profile.get("prefix"),
        title=profile.get("prefix"),
        county=profile.get("county"),
        phone=profile.get("phone"),
        job_title=profile.get("job_title"),
        station_name=profile.get("station_name"),
        station_address=profile.get("station_address"),
        signoff_email=profile.get("signoff_email"),
    )

# -----------------------------
# REFRESH TOKEN
# -----------------------------
@router.post("/refresh")
async def refresh_token(payload: Optional[RefreshTokenRequest] = None, refresh_token: Optional[str] = Form(None)):
    supabase = get_supabase_anon()

    try:
        token = payload.refresh_token if payload and payload.refresh_token else refresh_token
        if not token:
            raise HTTPException(status_code=400, detail="refresh_token is required")

        result = supabase.auth.refresh_session(token)
        return {
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
            "expires_in": result.session.expires_in,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token refresh failed: {str(e)}")

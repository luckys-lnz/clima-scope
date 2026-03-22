from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from typing import Optional

from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    RefreshTokenRequest,
    AuthResponse,
    UserResponse,
    ProfileUpdateRequest,
)
from app.core.supabase import get_supabase_admin, get_supabase_anon

router = APIRouter(tags=["authentication"])
security = HTTPBearer()

# -----------------------------
# Dependency: Get current user
# -----------------------------
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    supabase = get_supabase_anon()
    
    try:
        user = supabase.auth.get_user(credentials.credentials)
        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user.user
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
            supabase_admin.table("profiles").insert({
                "id": auth_resp.user.id,
                "full_name": user_data.full_name,
                "organization": user_data.organization,
                "county": user_data.county,
                "phone": user_data.phone,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception as e:
            # Rollback user creation if profile fails
            supabase_admin.auth.admin.delete_user(auth_resp.user.id)
            raise HTTPException(status_code=400, detail=f"Profile creation failed: {str(e)}")

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
    supabase = get_supabase_anon()
    
    try:
        auth_resp = supabase.auth.sign_in_with_password({
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
        try:
            profiles = supabase.table("profiles")\
                .select("*")\
                .eq("id", auth_resp.user.id)\
                .execute()
            profile = profiles.data[0] if profiles.data else {}
        except:
            profile = {}

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
    supabase = get_supabase_anon()
    
    try:
        profiles = supabase.table("profiles")\
            .select("*")\
            .eq("id", user.id)\
            .execute()
        profile = profiles.data[0] if profiles.data else {}
    except:
        profile = {}
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=profile.get("full_name", ""),
        organization=profile.get("organization", ""),
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
    supabase = get_supabase_anon()
    
    update_data = updates.model_dump(exclude_unset=True, exclude_none=True)
    
    if update_data:
        try:
            supabase.table("profiles")\
                .update(update_data)\
                .eq("id", user.id)\
                .execute()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Profile update failed: {str(e)}")
    
    # Get updated profile
    try:
        profiles = supabase.table("profiles")\
            .select("*")\
            .eq("id", user.id)\
            .execute()
        profile = profiles.data[0] if profiles.data else {}
    except:
        profile = {}
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=profile.get("full_name", ""),
        organization=profile.get("organization", ""),
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

from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import uuid

from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
    ProfileUpdateRequest,
)
from app.services.supabase import get_auth_client, get_db_client

router = APIRouter(tags=["authentication"])
security = HTTPBearer()

# Get client instances
supabase_auth = get_auth_client()
supabase_db = get_db_client()

# -----------------------------
# Dependency: Get current user
# -----------------------------
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    user_data = await supabase_auth.get_user(credentials.credentials)
    
    if not user_data or not user_data.get("id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_data

# -----------------------------
# Signup
# -----------------------------
@router.post("/signup", response_model=AuthResponse)
async def signup(user_data: SignupRequest):
    # Create auth user
    auth_resp = await supabase_auth.sign_up(
        user_data.email, 
        user_data.password
    )

    user = auth_resp.get("user", {})
    if not user:
        raise HTTPException(status_code=400, detail="Signup failed - no user returned")

    # Create profile in profiles table
    try:
        await supabase_db.insert("profiles", {
            "id": user.get("id"),
            "full_name": user_data.full_name,
            "organization": user_data.organization,
            "county": user_data.county,
            "phone": user_data.phone,
        })
    except Exception as e:
        print(f"Profile creation failed: {e}")

    return AuthResponse(
        success=True,
        access_token=auth_resp.get("access_token", ""),
        refresh_token=auth_resp.get("refresh_token", ""),
        expires_in=3600,
        user=UserResponse(
            id=user.get("id"),
            email=user_data.email,
            full_name=user_data.full_name,
            organization=user_data.organization,
            county=user_data.county,
            phone=user_data.phone,
        ),
    )

# -----------------------------
# Login
# -----------------------------
@router.post("/login", response_model=AuthResponse)
async def login(user_data: LoginRequest):
    auth_resp = await supabase_auth.sign_in(
        user_data.email, 
        user_data.password
    )

    user = auth_resp.get("user", {})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Get user profile
    try:
        profiles = await supabase_db.select(
            "profiles", 
            filters={"id": f"eq.{user.get('id')}"}
        )
        profile = profiles[0] if profiles else {}
    except:
        profile = {}

    return AuthResponse(
        success=True,
        access_token=auth_resp.get("access_token", ""),
        refresh_token=auth_resp.get("refresh_token", ""),
        expires_in=3600,
        user=UserResponse(
            id=user.get("id"),
            email=user.get("email", user_data.email),
            full_name=profile.get("full_name", ""),
            organization=profile.get("organization", ""),
            county=profile.get("county"),
            phone=profile.get("phone"),
        ),
    )

# -----------------------------
# Logout
# -----------------------------
@router.post("/logout")
async def logout(user=Depends(get_current_user)):
    return {"success": True, "message": "Logged out successfully"}

# -----------------------------
# Get current user profile
# -----------------------------
@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user=Depends(get_current_user)):
    try:
        profiles = await supabase_db.select(
            "profiles", 
            filters={"id": f"eq.{user.get('id')}"}
        )
        profile = profiles[0] if profiles else {}
    except:
        profile = {}
    
    return UserResponse(
        id=user.get("id"),
        email=user.get("email", ""),
        full_name=profile.get("full_name", ""),
        organization=profile.get("organization", ""),
        county=profile.get("county"),
        phone=profile.get("phone"),
    )

# -----------------------------
# Update profile
# -----------------------------
@router.put("/profile", response_model=UserResponse)
async def update_profile(updates: ProfileUpdateRequest, user=Depends(get_current_user)):
    update_data = updates.model_dump(exclude_unset=True, exclude_none=True)
    
    if update_data:
        await supabase_db.update(
            "profiles", 
            update_data, 
            filters={"id": f"eq.{user.get('id')}"}
        )
    
    # Get updated profile
    try:
        profiles = await supabase_db.select(
            "profiles", 
            filters={"id": f"eq.{user.get('id')}"}
        )
        profile = profiles[0] if profiles else {}
    except:
        profile = {}
    
    return UserResponse(
        id=user.get("id"),
        email=user.get("email", ""),
        full_name=profile.get("full_name", ""),
        organization=profile.get("organization", ""),
        county=profile.get("county"),
        phone=profile.get("phone"),
    )

# -----------------------------
# Refresh token
# -----------------------------
@router.post("/refresh")
async def refresh_token(refresh_token: str = Form(...)):
    result = await supabase_auth.refresh_session(refresh_token)
    return {
        "access_token": result.get("access_token", ""),
        "refresh_token": result.get("refresh_token", ""),
        "expires_in": result.get("expires_in", 3600),
    }

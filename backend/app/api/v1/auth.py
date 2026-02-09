from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.auth import (
    SignupRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
    ProfileUpdateRequest,
)
from app.config import settings
from supabase import create_client, Client

router = APIRouter(tags=["authentication"])
security = HTTPBearer()

# -------------------------------------------------
# Supabase client (INLINE)
# -------------------------------------------------
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_KEY,
)

# -------------------------------------------------
# Dependency: get current user
# -------------------------------------------------
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    resp = supabase.auth.get_user(token)

    if not resp.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return resp.user

# -------------------------------------------------
# Signup
# -------------------------------------------------
@router.post("/signup", response_model=AuthResponse)
async def signup(user_data: SignupRequest):
    auth_resp = supabase.auth.sign_up({
        "email": user_data.email,
        "password": user_data.password,
    })

    if not auth_resp.user:
        raise HTTPException(status_code=400, detail="Signup failed")

    user_id = auth_resp.user.id
    session = auth_resp.session

    # Create profile
    supabase.table("profiles").insert({
        "id": user_id,
        "full_name": user_data.full_name,
        "organization": user_data.organization,
        "county": user_data.county,
        "phone": user_data.phone,
    }).execute()

    return AuthResponse(
        success=True,
        access_token=session.access_token if session else "",
        refresh_token=session.refresh_token if session else "",
        expires_in=3600,
        user=UserResponse(
            id=user_id,
            email=user_data.email,
            full_name=user_data.full_name,
            organization=user_data.organization,
            county=user_data.county,
            phone=user_data.phone,
        ),
    )

# -------------------------------------------------
# Logout
# -------------------------------------------------
@router.post("/logout")
async def logout(user=Depends(get_current_user)):
    return {"success": True, "message": "Logged out successfully"}

# -------------------------------------------------
# Get current user profile
# -------------------------------------------------
@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user=Depends(get_current_user)):
    profile_resp = (
        supabase.table("profiles")
        .select("*")
        .eq("id", user.id)
        .single()
        .execute()
    )

    profile = profile_resp.data

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=profile["full_name"],
        organization=profile["organization"],
        county=profile.get("county"),
        phone=profile.get("phone"),
    )

# -------------------------------------------------
# Update profile
# -------------------------------------------------
@router.put("/profile", response_model=UserResponse)
async def update_profile(
    updates: ProfileUpdateRequest,
    user=Depends(get_current_user),
):
    update_data = {k: v for k, v in updates.dict().items() if v is not None}

    if update_data:
        supabase.table("profiles") \
            .update(update_data) \
            .eq("id", user.id) \
            .execute()

    profile_resp = (
        supabase.table("profiles")
        .select("*")
        .eq("id", user.id)
        .single()
        .execute()
    )

    profile = profile_resp.data

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=profile["full_name"],
        organization=profile["organization"],
        county=profile.get("county"),
        phone=profile.get("phone"),
    )

# -------------------------------------------------
# Refresh token
# -------------------------------------------------
@router.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        result = supabase.auth.refresh_session(refresh_token)
        return {
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
            "expires_in": 3600,
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

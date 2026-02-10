# backend/app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.schemas.auth import (
    SignupRequest, 
    LoginRequest, 
    AuthResponse,
    UserResponse,
    ProfileUpdateRequest
)
from app.services.auth import auth_service

router = APIRouter(tags=["authentication"])
security = HTTPBearer()

# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user = await auth_service.get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.post("/signup", response_model=AuthResponse)
async def signup(user_data: SignupRequest):
    """Register new user"""
    result = await auth_service.signup(
        email=user_data.email,
        password=user_data.password,
        user_data=user_data.dict()
    )
    
    # Extract tokens safely
    session = result.get("session")
    access_token = ""
    refresh_token = ""
    
    if session and hasattr(session, 'access_token'):
        access_token = session.access_token
    if session and hasattr(session, 'refresh_token'):
        refresh_token = session.refresh_token
    
    return AuthResponse(
        success=True,
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=result["user_id"],
            email=user_data.email,
            full_name=user_data.full_name,
            organization=user_data.organization,
            county=user_data.county,
            phone=user_data.phone
        )
    )

@router.post("/login", response_model=AuthResponse)
async def login(credentials: LoginRequest):
    """Login existing user"""
    result = await auth_service.login(
        email=credentials.email,
        password=credentials.password
    )
    
    # Get user profile
    profile_response = auth_service.client.table("profiles")\
        .select("*")\
        .eq("id", result["user"].id)\
        .single()\
        .execute()
    
    profile = profile_response.data
    
    return AuthResponse(
        success=True,
        access_token=result["session"].access_token,
        refresh_token=result["session"].refresh_token,
        user=UserResponse(
            id=result["user"].id,
            email=result["user"].email,
            full_name=profile["full_name"],
            organization=profile["organization"],
            county=profile.get("county"),
            phone=profile.get("phone")
        )
    )

@router.post("/logout")
async def logout(user = Depends(get_current_user)):
    """Logout user"""
    # Note: Supabase handles session invalidation
    return {"success": True, "message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user = Depends(get_current_user)):
    """Get current user's profile"""
    profile_response = auth_service.client.table("profiles")\
        .select("*")\
        .eq("id", user.id)\
        .single()\
        .execute()
    
    profile = profile_response.data
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=profile["full_name"],
        organization=profile["organization"],
        county=profile.get("county"),
        phone=profile.get("phone")
    )

@router.put("/profile", response_model=UserResponse)
async def update_profile(
    updates: ProfileUpdateRequest,
    user = Depends(get_current_user)
):
    """Update user profile"""
    # Filter out None values
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    if update_data:
        auth_service.client.table("profiles")\
            .update(update_data)\
            .eq("id", user.id)\
            .execute()
    
    # Get updated profile
    profile_response = auth_service.client.table("profiles")\
        .select("*")\
        .eq("id", user.id)\
        .single()\
        .execute()
    
    profile = profile_response.data
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=profile["full_name"],
        organization=profile["organization"],
        county=profile.get("county"),
        phone=profile.get("phone")
    )

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    try:
        result = auth_service.client.auth.refresh_session(refresh_token)
        return {
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token,
            "expires_in": 3600
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

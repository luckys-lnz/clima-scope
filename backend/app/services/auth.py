# backend/app/services/auth_service.py
import supabase
from supabase import create_client
from fastapi import HTTPException
from datetime import datetime, timedelta
from app.config import settings
from typing import Optional, Dict

class AuthService:
    def __init__(self):
        self.admin_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
        self.client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
    
    async def signup(self, email: str, password: str, user_data: Dict) -> Dict:
        """Register new user"""
        try:
            # 1. Create auth user - no duplicate metadata in options
            auth_response = self.admin_client.auth.sign_up({
                "email": email,
                "password": password
            })
            
            user = auth_response.user
            if not user:
                raise HTTPException(status_code=400, detail="Could not create user account")
            
            # 2. Create profile in database
            profile_data = {
                "id": user.id,
                "full_name": user_data.get("full_name", ""),
                "organization": user_data.get("organization", ""),
                "county": user_data.get("county"),
                "phone": user_data.get("phone")
            }
            
            profile_response = self.admin_client.table("profiles").insert(profile_data).execute()
            
            # 3. Create free subscription
            subscription_data = {
                "user_id": user.id,
                "plan_id": await self._get_free_plan_id(),
                "status": "active",
                "current_period_start": datetime.now().isoformat(),
                "current_period_end": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            self.admin_client.table("user_subscriptions").insert(subscription_data).execute()

            session_data = auth_response.session

            if session_data:
                return {
                    "success": True,
                    "user_id": user.id,
                    "email": user.email,
                    "session": session_data
                }
            else:
                return {
                    "success": True,
                    "user_id": user.id,
                    "email": user.email,
                    "session": None,
                    "message": "Check email for confirmation"
                }

        except Exception as e:
            error_msg = str(e).lower()
            
            # Handle Supabase Auth errors
            if "already registered" in error_msg or "user already exists" in error_msg:
                raise HTTPException(status_code=400, detail="This email is already registered. Please sign in instead.")
            elif "invalid email" in error_msg:
                raise HTTPException(status_code=400, detail="Please enter a valid email address.")
            elif "password" in error_msg and ("weak" in error_msg or "length" in error_msg):
                raise HTTPException(status_code=400, detail="Password must be at least 8 characters with uppercase, lowercase, and numbers.")
            elif "rate limit" in error_msg:
                raise HTTPException(status_code=429, detail="Too many attempts. Please wait 10 minutes.")
            elif "duplicate key" in error_msg:
                raise HTTPException(status_code=400, detail="Account already exists.")
            elif "profiles" in error_msg and ("rls" in error_msg or "policy" in error_msg):
                raise HTTPException(status_code=500, detail="System error. Please contact support.")
            elif "profiles" in error_msg and "email" in error_msg:
                raise HTTPException(status_code=500, detail="Database configuration error.")
            else:
                raise HTTPException(status_code=500, detail="Something went wrong. Please try again.")
    
    async def login(self, email: str, password: str) -> Dict:
        """Login existing user"""
        try:
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            return {
                "success": True,
                "user": response.user,
                "session": response.session
            }
        except Exception as e:
            error_msg = str(e).lower()
            
            if "invalid login" in error_msg or "invalid credentials" in error_msg:
                raise HTTPException(status_code=401, detail="Incorrect email or password.")
            elif "email not confirmed" in error_msg:
                raise HTTPException(status_code=401, detail="Please confirm your email before logging in.")
            elif "rate limit" in error_msg:
                raise HTTPException(status_code=429, detail="Too many attempts. Please wait.")
            else:
                raise HTTPException(status_code=401, detail="Login failed. Please try again.")
    
    async def logout(self, access_token: str):
        """Logout user"""
        self.client.auth.sign_out(access_token)
    
    async def get_current_user(self, access_token: str):
        """Validate token and get user"""
        try:
            user = self.client.auth.get_user(access_token)
            return user
        except:
            return None
    
    async def _get_free_plan_id(self) -> str:
        """Get ID of free plan"""
        try:
            response = self.client.table("subscription_plans")\
                .select("id")\
                .eq("name", "Free")\
                .single()\
                .execute()
            
            if response.data:
                return response.data["id"]
            else:
                # Create free plan if it doesn't exist
                free_plan = {
                    "name": "Free",
                    "description": "Free subscription plan",
                    "price": 0,
                    "currency": "KES",
                    "interval": "month"
                }
                
                plan_response = self.client.table("subscription_plans")\
                    .insert(free_plan)\
                    .execute()
                
                return plan_response.data[0]["id"]
                
        except Exception as e:
            # Return a default plan ID or handle error
            return "free_plan_id"

# Singleton instance
auth_service = AuthService()

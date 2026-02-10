# backend/app/schemas/auth.py
from pydantic import BaseModel, EmailStr, constr
from typing import Optional

class SignupRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=100)
    full_name: str
    organization: str
    county: Optional[str] = None
    phone: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "meteorologist@kmd.go.ke",
                "password": "SecurePass123",
                "full_name": "John Kamau",
                "organization": "Kenya Meteorological Department",
                "county": "Nairobi",
                "phone": "+254712345678"
            }
        }

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    organization: str
    county: Optional[str]
    phone: Optional[str]
    
class AuthResponse(BaseModel):
    success: bool
    access_token: str
    refresh_token: str
    user: UserResponse
    expires_in: int = 3600

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    organization: Optional[str] = None
    county: Optional[str] = None
    phone: Optional[str] = None

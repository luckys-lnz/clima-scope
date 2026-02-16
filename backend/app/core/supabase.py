import httpx
from typing import Dict, List, Optional, Any
from fastapi import HTTPException
from app.core.config import settings

class SupabaseStorageClient:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.service_key = settings.SUPABASE_SERVICE_KEY
        self.bucket_name = settings.SUPABASE_STORAGE_BUCKET
        self.headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
        }
    
    async def upload_file(self, file_path: str, content: bytes, upsert: bool = True) -> dict:
        """Upload file to Supabase Storage"""
        async with httpx.AsyncClient() as client:
            headers = self.headers.copy()
            headers["Content-Type"] = "application/octet-stream"
            
            response = await client.post(
                f"{self.url}/storage/v1/object/{self.bucket_name}/{file_path}",
                headers=headers,
                content=content,
                params={"upsert": "true"} if upsert else {}
            )
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Storage upload failed: {response.text}"
                )
            
            return {"path": file_path}
    
    async def delete_file(self, file_path: str) -> dict:
        """Delete file from Supabase Storage"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.url}/storage/v1/object/{self.bucket_name}/{file_path}",
                headers=self.headers
            )
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Storage deletion failed: {response.text}"
                )
            
            return {"success": True}
    
    async def get_public_url(self, file_path: str) -> str:
        """Get public URL for file"""
        return f"{self.url}/storage/v1/object/public/{self.bucket_name}/{file_path}"
    
    async def list_files(self, prefix: str = "") -> List[dict]:
        """List files in bucket with prefix"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/storage/v1/object/list/{self.bucket_name}",
                headers=self.headers,
                json={"prefix": prefix}
            )
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Storage list failed: {response.text}"
                )
            
            return response.json()


class SupabaseDBClient:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.service_key = settings.SUPABASE_SERVICE_KEY
        self.headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }
    
    async def insert(self, table: str, data: dict, returning: bool = True) -> List[dict]:
        """Insert record into table"""
        async with httpx.AsyncClient() as client:
            headers = self.headers.copy()
            if returning:
                headers["Prefer"] = "return=representation"
            
            response = await client.post(
                f"{self.url}/rest/v1/{table}",
                headers=headers,
                json=data
            )
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Database insert failed: {response.text}"
                )
            
            return response.json() if returning else []
    
    async def select(
        self, 
        table: str, 
        filters: Optional[Dict] = None,
        columns: str = "*"
    ) -> List[dict]:
        """Select records from table"""
        async with httpx.AsyncClient() as client:
            headers = self.headers.copy()
            
            params = {"select": columns}
            if filters:
                params.update(filters)
            
            response = await client.get(
                f"{self.url}/rest/v1/{table}",
                headers=headers,
                params=params
            )
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Database select failed: {response.text}"
                )
            
            return response.json()
    
    async def update(
        self, 
        table: str, 
        data: dict, 
        filters: Dict,
        returning: bool = True
    ) -> List[dict]:
        """Update records in table"""
        async with httpx.AsyncClient() as client:
            headers = self.headers.copy()
            if returning:
                headers["Prefer"] = "return=representation"
            
            response = await client.patch(
                f"{self.url}/rest/v1/{table}",
                headers=headers,
                params=filters,
                json=data
            )
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Database update failed: {response.text}"
                )
            
            return response.json() if returning else []
    
    async def delete(
        self, 
        table: str, 
        filters: Dict,
        returning: bool = False
    ) -> List[dict]:
        """Delete records from table"""
        async with httpx.AsyncClient() as client:
            headers = self.headers.copy()
            if returning:
                headers["Prefer"] = "return=representation"
            
            response = await client.delete(
                f"{self.url}/rest/v1/{table}",
                headers=headers,
                params=filters
            )
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Database delete failed: {response.text}"
                )
            
            return response.json() if returning else []
    
    async def rpc(self, function_name: str, params: Dict = None) -> Any:
        """Call Postgres function"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/rest/v1/rpc/{function_name}",
                headers=self.headers,
                json=params or {}
            )
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"RPC call failed: {response.text}"
                )
            
            return response.json()


class SupabaseAuthClient:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.anon_key = settings.SUPABASE_ANON_KEY
        self.headers = {
            "apikey": self.anon_key,
            "Content-Type": "application/json"
        }
    
    async def sign_up(self, email: str, password: str) -> dict:
        """Create new user"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/auth/v1/signup",
                headers=self.headers,
                json={"email": email, "password": password}
            )
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.json().get("error_description", response.json())
                )
            
            return response.json()
    
    async def sign_in(self, email: str, password: str) -> dict:
        """Login user"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/auth/v1/token?grant_type=password",
                headers=self.headers,
                json={"email": email, "password": password}
            )
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Invalid email or password"
                )
            
            return response.json()
    
    async def get_user(self, token: str) -> dict:
        """Get user by token"""
        async with httpx.AsyncClient() as client:
            headers = self.headers.copy()
            headers["Authorization"] = f"Bearer {token}"
            
            response = await client.get(
                f"{self.url}/auth/v1/user",
                headers=headers
            )
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Invalid authentication credentials"
                )
            
            return response.json()
    
    async def refresh_session(self, refresh_token: str) -> dict:
        """Refresh access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/auth/v1/token?grant_type=refresh_token",
                headers=self.headers,
                json={"refresh_token": refresh_token}
            )
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Invalid refresh token"
                )
            
            return response.json()
    
    async def sign_out(self, token: str) -> dict:
        """Sign out user"""
        async with httpx.AsyncClient() as client:
            headers = self.headers.copy()
            headers["Authorization"] = f"Bearer {token}"
            
            response = await client.post(
                f"{self.url}/auth/v1/logout",
                headers=headers
            )
            
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Sign out failed"
                )
            
            return {"success": True}


# Singleton instances
_storage_client = None
_db_client = None
_auth_client = None

def get_storage_client() -> SupabaseStorageClient:
    global _storage_client
    if _storage_client is None:
        _storage_client = SupabaseStorageClient()
    return _storage_client

def get_db_client() -> SupabaseDBClient:
    global _db_client
    if _db_client is None:
        _db_client = SupabaseDBClient()
    return _db_client

def get_auth_client() -> SupabaseAuthClient:
    global _auth_client
    if _auth_client is None:
        _auth_client = SupabaseAuthClient()
    return _auth_client

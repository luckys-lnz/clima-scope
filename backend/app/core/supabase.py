from supabase import create_client, Client
from app.core.config import settings

_supabase_admin: Client = None
_supabase_anon: Client = None

def get_supabase_admin() -> Client:
    """Get Supabase admin client (uses service key - bypasses RLS)"""
    global _supabase_admin
    if _supabase_admin is None:
        _supabase_admin = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
    return _supabase_admin

def get_supabase_anon() -> Client:
    """Get Supabase anon client (uses anon key - respects RLS)"""
    global _supabase_anon
    if _supabase_anon is None:
        _supabase_anon = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
    return _supabase_anon
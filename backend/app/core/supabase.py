from supabase import create_client, Client
from app.core.config import settings

_supabase_admin: Client = None

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
    """Get Supabase anon client (uses anon key - respects RLS).

    Important: return a fresh client instance per call.
    The anon auth client maintains session state; sharing one global instance
    across requests can leak/overwrite auth context and cause intermittent
    401/403 behavior between concurrent users/requests.
    """
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY
    )

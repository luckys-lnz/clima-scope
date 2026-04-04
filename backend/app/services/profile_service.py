from typing import Any, Dict, Optional


def _extract_user_id(user: Any) -> Optional[str]:
    if not user:
        return None

    if hasattr(user, "id"):
        user_id = getattr(user, "id")
        if isinstance(user_id, str) and user_id.strip():
            return user_id.strip()

    if isinstance(user, dict):
        user_id = user.get("id")
        if isinstance(user_id, str) and user_id.strip():
            return user_id.strip()

    return None


def _extract_user_email(user: Any) -> Optional[str]:
    if not user:
        return None

    if hasattr(user, "email"):
        email = getattr(user, "email")
        if isinstance(email, str) and email.strip():
            return email.strip()

    if isinstance(user, dict):
        email = user.get("email")
        if isinstance(email, str) and email.strip():
            return email.strip()

    return None


def fetch_profile_for_user(
    supabase_client,
    user: Any,
    *,
    raise_on_error: bool = False,
) -> Dict[str, Any]:
    if not supabase_client or not user:
        return {}

    user_id = _extract_user_id(user)
    if user_id:
        try:
            profile_response = supabase_client.table("profiles")\
                .select("*")\
                .eq("id", user_id)\
                .limit(1)\
                .execute()
            rows = profile_response.data or []
            if rows:
                return rows[0]
        except Exception as exc:
            if raise_on_error:
                raise exc

    return {}


def get_user_email(user: Any) -> Optional[str]:
    return _extract_user_email(user)

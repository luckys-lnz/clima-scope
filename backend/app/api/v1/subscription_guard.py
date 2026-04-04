from fastapi import Depends, HTTPException, status

from app.api.v1.auth import get_current_user
from app.core.config import settings
from app.core.supabase import get_supabase_admin
from app.services.subscription_service import get_user_access_state


async def require_paid_or_trial_access(user=Depends(get_current_user)):
    """Allow access only for active trial or paid subscription when gate enforcement is enabled."""
    if not settings.ENFORCE_SUBSCRIPTION_GATE:
        return user

    supabase_admin = get_supabase_admin()
    state = get_user_access_state(supabase_admin=supabase_admin, user=user)
    access_status = str(state.get("access_status") or "payment_required")

    if access_status in {"subscribed", "trial_active"}:
        return user

    trial = state.get("trial") or {}
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "code": "PAYMENT_REQUIRED",
            "message": "Trial period has ended. Upgrade to continue using this feature.",
            "trial_ended_at": trial.get("ends_at"),
            "upgrade_path": "/pricing",
            "access_status": access_status,
        },
    )

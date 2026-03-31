import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from dateutil.relativedelta import relativedelta

from app.core.config import settings
from app.services.pesapal_service import PesapalService, PesapalServiceError

logger = logging.getLogger(__name__)


class SubscriptionError(RuntimeError):
    pass


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_user_id(user: Any) -> str:
    if hasattr(user, "id"):
        return str(user.id)
    if isinstance(user, dict) and user.get("id"):
        return str(user["id"])
    raise SubscriptionError("Could not resolve user id from auth context.")


def _get_cycle_end(start: datetime, billing_cycle: str) -> datetime:
    cycle = (billing_cycle or "monthly").strip().lower()
    if cycle == "yearly":
        return start + relativedelta(years=1)
    if cycle == "weekly":
        return start + relativedelta(weeks=1)
    if cycle == "daily":
        return start + relativedelta(days=1)
    return start + relativedelta(months=1)


def _map_payment_status(provider_status: str) -> str:
    normalized = str(provider_status or "").strip().upper()
    if normalized in {"COMPLETED", "PAID", "SUCCESS", "SUCCESSFUL"}:
        return "COMPLETED"
    if normalized in {"FAILED", "INVALID", "CANCELLED", "REVERSED"}:
        return "FAILED"
    return "PENDING"


def list_public_plans(supabase_admin) -> list[Dict[str, Any]]:
    try:
        response = (
            supabase_admin.table("subscription_plans")
            .select("id,name,description,price,currency,billing_cycle,features,is_active,is_public")
            .eq("is_active", True)
            .eq("is_public", True)
            .order("price", desc=False)
            .execute()
        )
        return response.data or []
    except Exception as exc:
        logger.exception("subscription_plans_fetch_failed", extra={"error": str(exc)})
        raise SubscriptionError("Failed to fetch subscription plans.") from exc


def _get_active_plan_or_raise(supabase_admin, plan_id: str) -> Dict[str, Any]:
    try:
        response = (
            supabase_admin.table("subscription_plans")
            .select("id,name,description,price,currency,billing_cycle,is_active,is_public")
            .eq("id", plan_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        logger.exception("subscription_plan_fetch_failed", extra={"error": str(exc), "plan_id": plan_id})
        raise SubscriptionError("Failed to fetch selected plan.") from exc

    rows = response.data or []
    if not rows:
        raise SubscriptionError("Selected plan does not exist or is inactive.")
    return rows[0]


def _create_pending_payment(supabase_admin, user_id: str, plan: Dict[str, Any]) -> Dict[str, Any]:
    merchant_reference = f"SUB-{user_id[:8]}-{uuid4().hex[:12]}".upper()
    now = _utc_now_iso()
    payload = {
        "provider": "Pesapal",
        "amount": float(plan.get("price") or 0),
        "currency": str(plan.get("currency") or "KES"),
        "status": "PENDING",
        "merchant_reference": merchant_reference,
        "ipn_received": False,
        "user_id": user_id,
        "plan_id": plan["id"],
        "created_at": now,
        "updated_at": now,
    }
    try:
        response = supabase_admin.table("payments").insert(payload).execute()
    except Exception as exc:
        logger.exception("payment_insert_failed", extra={"error": str(exc), "user_id": user_id, "plan_id": plan["id"]})
        raise SubscriptionError("Failed to create pending payment.") from exc

    rows = response.data or []
    if not rows:
        raise SubscriptionError("Payment creation failed: no row returned.")
    return rows[0]


def _build_billing_address(user: Any) -> Dict[str, str]:
    full_name = ""
    if hasattr(user, "user_metadata") and isinstance(user.user_metadata, dict):
        full_name = str(user.user_metadata.get("full_name") or "").strip()
    if not full_name and hasattr(user, "email") and user.email:
        full_name = str(user.email).split("@")[0].replace(".", " ").title()
    parts = [p for p in full_name.split() if p]
    first_name = parts[0] if parts else "Customer"
    last_name = " ".join(parts[1:]) if len(parts) > 1 else "User"

    email = str(getattr(user, "email", "") or "")
    return {
        "email_address": email or "customer@example.com",
        "phone_number": "",
        "country_code": "KE",
        "first_name": first_name,
        "middle_name": "",
        "last_name": last_name,
        "line_1": "",
        "line_2": "",
        "city": "",
        "state": "",
        "postal_code": "",
        "zip_code": "",
    }


def create_checkout(supabase_admin, user: Any, plan_id: str, return_url: Optional[str], description: Optional[str]) -> Dict[str, Any]:
    user_id = _safe_user_id(user)
    plan = _get_active_plan_or_raise(supabase_admin, plan_id)
    payment = _create_pending_payment(supabase_admin, user_id, plan)

    callback_url = return_url or settings.PESAPAL_CALLBACK_URL
    if not callback_url:
        raise SubscriptionError("Missing callback URL. Set PESAPAL_CALLBACK_URL or pass return_url.")
    if not settings.PESAPAL_IPN_ID:
        raise SubscriptionError("Missing PESAPAL_IPN_ID configuration.")

    order_payload = {
        "id": payment["merchant_reference"],
        "currency": payment["currency"],
        "amount": float(payment["amount"]),
        "description": description or f"{plan.get('name', 'Subscription plan')} subscription",
        "callback_url": callback_url,
        "notification_id": settings.PESAPAL_IPN_ID,
        "billing_address": _build_billing_address(user),
    }

    pesapal = PesapalService()
    try:
        order = pesapal.submit_order_request(order_payload)
    except PesapalServiceError as exc:
        try:
            supabase_admin.table("payments").update(
                {"status": "FAILED", "updated_at": _utc_now_iso()}
            ).eq("id", payment["id"]).execute()
        except Exception:
            logger.exception("payment_mark_failed_after_order_error", extra={"payment_id": payment["id"]})
        raise SubscriptionError(str(exc)) from exc

    order_tracking_id = str(order.get("order_tracking_id") or "")
    merchant_reference = str(order.get("merchant_reference") or payment["merchant_reference"])
    redirect_url = str(order.get("redirect_url") or "")

    try:
        supabase_admin.table("payments").update(
            {
                "merchant_reference": merchant_reference,
                "confirmation_code": order_tracking_id,
                "updated_at": _utc_now_iso(),
            }
        ).eq("id", payment["id"]).execute()
    except Exception as exc:
        logger.exception("payment_update_after_order_failed", extra={"error": str(exc), "payment_id": payment["id"]})
        raise SubscriptionError("Failed to update payment with Pesapal order details.") from exc

    return {
        "payment_id": str(payment["id"]),
        "merchant_reference": merchant_reference,
        "order_tracking_id": order_tracking_id,
        "redirect_url": redirect_url,
    }


def _validate_ipn_origin(secret: Optional[str], client_host: Optional[str]) -> None:
    if settings.PESAPAL_IPN_ALLOWED_IPS.strip():
        allowed = {ip.strip() for ip in settings.PESAPAL_IPN_ALLOWED_IPS.split(",") if ip.strip()}
        if client_host not in allowed:
            raise SubscriptionError("IPN request host is not allowlisted.")

    configured_secret = settings.PESAPAL_IPN_SECRET.strip()
    if configured_secret and secret != configured_secret:
        raise SubscriptionError("Invalid IPN secret token.")


def _extract_status_payload(status_payload: Dict[str, Any]) -> Dict[str, Any]:
    provider_status = (
        status_payload.get("payment_status_description")
        or status_payload.get("payment_status")
        or status_payload.get("status")
        or "PENDING"
    )
    return {
        "status": _map_payment_status(str(provider_status)),
        "provider_status": str(provider_status),
        "confirmation_code": status_payload.get("confirmation_code")
        or status_payload.get("order_tracking_id")
        or "",
        "payment_method": status_payload.get("payment_method") or status_payload.get("payment_type") or "",
        "payment_account": status_payload.get("payment_account") or status_payload.get("msisdn") or "",
    }


def _upsert_active_subscription(
    supabase_admin,
    *,
    user_id: str,
    plan_id: str,
    billing_cycle: str,
    order_tracking_id: str,
    merchant_reference: str,
) -> None:
    now_dt = datetime.now(timezone.utc)
    start_iso = now_dt.isoformat()
    end_iso = _get_cycle_end(now_dt, billing_cycle).isoformat()
    payload = {
        "user_id": user_id,
        "plan_id": plan_id,
        "status": "active",
        "current_period_start": start_iso,
        "current_period_end": end_iso,
        "cancel_at_period_end": False,
        "pesapal_order_tracking_id": order_tracking_id,
        "pesapal_merchant_reference": merchant_reference,
        "updated_at": _utc_now_iso(),
    }

    active_rows = (
        supabase_admin.table("user_subscriptions")
        .select("id")
        .eq("user_id", user_id)
        .eq("status", "active")
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
    ).data or []

    if active_rows:
        supabase_admin.table("user_subscriptions").update(payload).eq("id", active_rows[0]["id"]).execute()
        return

    payload["created_at"] = _utc_now_iso()
    supabase_admin.table("user_subscriptions").insert(payload).execute()


def handle_pesapal_ipn(
    supabase_admin,
    *,
    order_tracking_id: str,
    merchant_reference: str,
    secret: Optional[str],
    client_host: Optional[str],
) -> Dict[str, Any]:
    _validate_ipn_origin(secret=secret, client_host=client_host)
    if not order_tracking_id:
        raise SubscriptionError("Missing order tracking id in IPN.")
    if not merchant_reference:
        raise SubscriptionError("Missing merchant reference in IPN.")

    payment_rows = (
        supabase_admin.table("payments")
        .select("id,user_id,plan_id,merchant_reference,status")
        .eq("merchant_reference", merchant_reference)
        .limit(1)
        .execute()
    ).data or []

    if not payment_rows:
        raise SubscriptionError("No payment record found for merchant reference.")
    payment = payment_rows[0]

    pesapal = PesapalService()
    status_payload = pesapal.get_transaction_status(order_tracking_id=order_tracking_id)

    resolved = _extract_status_payload(status_payload)
    payment_update = {
        "status": resolved["status"],
        "ipn_received": True,
        "confirmation_code": resolved["confirmation_code"],
        "payment_method": resolved["payment_method"],
        "payment_account": resolved["payment_account"],
        "updated_at": _utc_now_iso(),
    }

    # Ensure IPN corresponds to the expected payment reference.
    status_reference = (
        status_payload.get("merchant_reference")
        or status_payload.get("order_merchant_reference")
        or merchant_reference
    )
    if str(status_reference) != str(payment["merchant_reference"]):
        raise SubscriptionError("Merchant reference mismatch during IPN verification.")

    supabase_admin.table("payments").update(payment_update).eq("id", payment["id"]).execute()

    if resolved["status"] == "COMPLETED":
        plan_rows = (
            supabase_admin.table("subscription_plans")
            .select("id,billing_cycle")
            .eq("id", payment["plan_id"])
            .limit(1)
            .execute()
        ).data or []
        if not plan_rows:
            raise SubscriptionError("Plan linked to payment not found.")
        plan = plan_rows[0]
        _upsert_active_subscription(
            supabase_admin,
            user_id=str(payment["user_id"]),
            plan_id=str(payment["plan_id"]),
            billing_cycle=str(plan.get("billing_cycle") or "monthly"),
            order_tracking_id=order_tracking_id,
            merchant_reference=merchant_reference,
        )

    return {
        "payment_id": str(payment["id"]),
        "merchant_reference": str(payment["merchant_reference"]),
        "order_tracking_id": order_tracking_id,
        "status": resolved["status"],
        "provider_status": resolved["provider_status"],
    }


def get_user_subscription_state(supabase_admin, user: Any) -> Dict[str, Any]:
    user_id = _safe_user_id(user)
    sub_rows = (
        supabase_admin.table("user_subscriptions")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
    ).data or []

    payment_rows = (
        supabase_admin.table("payments")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .limit(1)
        .execute()
    ).data or []

    return {
        "subscription": sub_rows[0] if sub_rows else None,
        "latest_payment": payment_rows[0] if payment_rows else None,
    }


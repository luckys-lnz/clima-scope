import logging
from typing import Any, Dict
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.v1.auth import get_current_user
from app.core.config import settings
from app.core.supabase import get_supabase_admin
from app.schemas.subscription import (
    CheckoutRequest,
    CheckoutResponse,
    PlanListOut,
    SubscriptionPlanOut,
    SubscriptionStateOut,
)
from app.services.subscription_service import (
    SubscriptionError,
    create_checkout,
    get_user_subscription_state,
    handle_pesapal_ipn,
    list_public_plans,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["subscriptions"])


@router.get("/plans", response_model=PlanListOut)
async def get_plans(user=Depends(get_current_user)):
    _ = user  # authenticated listing
    supabase_admin = get_supabase_admin()
    try:
        plans = list_public_plans(supabase_admin)
        public_plans = []
        for p in plans:
            try:
                plan = SubscriptionPlanOut(
                    id=str(p.get("id") or ""),
                    name=str(p.get("name") or ""),
                    description=p.get("description"),
                    price=float(p.get("price") or 0),
                    currency=str(p.get("currency") or "KES"),
                    billing_cycle=str(p.get("billing_cycle") or "monthly"),
                    features=p.get("features") if p.get("features") is not None else {},
                )
            except Exception as row_exc:
                logger.warning(
                    "subscription_plan_row_invalid",
                    extra={"error": str(row_exc), "row": p},
                )
                continue

            if plan.id and plan.name:
                public_plans.append(plan)
        return PlanListOut(plans=public_plans)
    except SubscriptionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("list_plans_unexpected_error", extra={"error": str(exc)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list plans.") from exc


def _pick_ipn_field(request: Request, payload: Dict[str, Any], *names: str) -> str:
    for name in names:
        value = request.query_params.get(name)
        if value:
            return str(value)
    for name in names:
        value = payload.get(name)
        if value:
            return str(value)
    return ""


def _is_allowed_callback_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False

    allowed_origins = set(settings.cors_origins_list or [])
    if not allowed_origins:
        return True

    callback_origin = f"{parsed.scheme}://{parsed.netloc}"
    return callback_origin in allowed_origins


def _resolve_checkout_return_url(request: Request, explicit_return_url: str) -> str:
    if explicit_return_url and _is_allowed_callback_url(explicit_return_url):
        return explicit_return_url

    referer = request.headers.get("referer", "").strip()
    if referer and _is_allowed_callback_url(referer):
        return referer

    configured = settings.PESAPAL_CALLBACK_URL.strip()
    if configured and _is_allowed_callback_url(configured):
        return configured

    raise SubscriptionError(
        "No valid callback URL found. Pass return_url from the page URL or set PESAPAL_CALLBACK_URL."
    )


@router.post("/pesapal/ipn")
async def pesapal_ipn(
    request: Request,
    token: str = Query(default=""),
):
    supabase_admin = get_supabase_admin()

    try:
        payload = await request.json()
        if not isinstance(payload, dict):
            payload = {}
    except Exception:
        payload = {}

    order_tracking_id = _pick_ipn_field(
        request,
        payload,
        "OrderTrackingId",
        "orderTrackingId",
        "order_tracking_id",
    )
    merchant_reference = _pick_ipn_field(
        request,
        payload,
        "OrderMerchantReference",
        "orderMerchantReference",
        "merchant_reference",
    )
    if not merchant_reference:
        merchant_reference = _pick_ipn_field(request, payload, "MerchantReference", "id")

    client_host = request.client.host if request.client else None

    try:
        result = handle_pesapal_ipn(
            supabase_admin=supabase_admin,
            order_tracking_id=order_tracking_id,
            merchant_reference=merchant_reference,
            secret=token,
            client_host=client_host,
        )
        return {"status": "ok", **result}
    except SubscriptionError as exc:
        logger.warning("pesapal_ipn_rejected", extra={"error": str(exc), "client_host": client_host})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("pesapal_ipn_unexpected_error", extra={"error": str(exc)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process IPN.") from exc


@router.get("/me", response_model=SubscriptionStateOut)
async def my_subscription_state(user=Depends(get_current_user)):
    supabase_admin = get_supabase_admin()
    try:
        state = get_user_subscription_state(supabase_admin=supabase_admin, user=user)
        return SubscriptionStateOut(**state)
    except SubscriptionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("subscription_state_unexpected_error", extra={"error": str(exc)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load subscription state.") from exc


@router.post("/checkout", response_model=CheckoutResponse)
async def start_checkout(payload: CheckoutRequest, request: Request, user=Depends(get_current_user)):
    supabase_admin = get_supabase_admin()
    try:
        callback_url = _resolve_checkout_return_url(request, payload.return_url or "")
        result = create_checkout(
            supabase_admin=supabase_admin,
            user=user,
            plan_id=payload.plan_id,
            return_url=callback_url,
            description=payload.description,
        )
        return CheckoutResponse(**result)
    except SubscriptionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("checkout_unexpected_error", extra={"error": str(exc)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create checkout.") from exc

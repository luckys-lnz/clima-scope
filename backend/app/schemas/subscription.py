from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class SubscriptionPlanOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: float
    currency: str = "KES"
    billing_cycle: str = "monthly"
    features: Any = Field(default_factory=dict)


class CheckoutRequest(BaseModel):
    plan_id: str
    return_url: Optional[str] = None
    description: Optional[str] = None


class CheckoutResponse(BaseModel):
    payment_id: str
    merchant_reference: str
    redirect_url: str
    order_tracking_id: str


class PaymentStatusOut(BaseModel):
    payment_id: str
    status: str
    merchant_reference: str
    order_tracking_id: Optional[str] = None
    confirmation_code: Optional[str] = None
    payment_method: Optional[str] = None
    payment_account: Optional[str] = None
    ipn_received: bool = False
    updated_at: Optional[datetime] = None


class UserSubscriptionOut(BaseModel):
    id: str
    user_id: str
    plan_id: str
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    pesapal_order_tracking_id: Optional[str] = None
    pesapal_merchant_reference: Optional[str] = None


class TrialStateOut(BaseModel):
    status: str
    started_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    days_remaining: int = 0
    grace_days: int = 0


class SubscriptionStateOut(BaseModel):
    subscription: Optional[UserSubscriptionOut] = None
    latest_payment: Optional[PaymentStatusOut] = None
    trial: Optional[TrialStateOut] = None
    access_status: str = "payment_required"


class PlanListOut(BaseModel):
    plans: List[SubscriptionPlanOut]

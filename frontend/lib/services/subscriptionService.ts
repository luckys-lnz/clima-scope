"use client";

import { authService } from "@/lib/services/authService";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiErrorBody {
  detail?: string;
  message?: string;
}

const getResponseErrorMessage = async (
  response: Response,
  fallback: string,
): Promise<string> => {
  const error = await response.json().catch(() => null as ApiErrorBody | null);
  return error?.detail || error?.message || fallback;
};

export interface SubscriptionPlan {
  id: string;
  name: string;
  description?: string;
  price: number;
  currency: string;
  billing_cycle: string;
  features: Record<string, unknown>;
}

export interface CheckoutRequest {
  plan_id: string;
  return_url?: string;
  description?: string;
}

export interface CheckoutResponse {
  payment_id: string;
  merchant_reference: string;
  redirect_url: string;
  order_tracking_id: string;
}

export interface PaymentStatus {
  payment_id: string;
  status: string;
  merchant_reference: string;
  order_tracking_id?: string | null;
  confirmation_code?: string | null;
  payment_method?: string | null;
  payment_account?: string | null;
  ipn_received: boolean;
  updated_at?: string | null;
}

export interface UserSubscription {
  id: string;
  user_id: string;
  plan_id: string;
  status: string;
  current_period_start?: string | null;
  current_period_end?: string | null;
  cancel_at_period_end: boolean;
  pesapal_order_tracking_id?: string | null;
  pesapal_merchant_reference?: string | null;
}

export interface SubscriptionState {
  subscription: UserSubscription | null;
  latest_payment: PaymentStatus | null;
  trial?: {
    status: string;
    started_at?: string | null;
    ends_at?: string | null;
    days_remaining: number;
    grace_days: number;
  } | null;
  access_status?: "trial_active" | "subscribed" | "payment_required" | string;
}

export const subscriptionService = {
  async getPlans(
    token: string | null | undefined,
  ): Promise<SubscriptionPlan[]> {
    const response = await authService.fetchWithAuth(
      `${API_BASE}/api/v1/subscriptions/plans`,
      {
        method: "GET",
        token,
      },
    );
    if (!response.ok) {
      throw new Error(
        await getResponseErrorMessage(
          response,
          "Failed to load subscription plans",
        ),
      );
    }
    const payload = (await response.json()) as { plans?: SubscriptionPlan[] };
    return payload.plans || [];
  },

  async getMySubscription(
    token: string | null | undefined,
  ): Promise<SubscriptionState> {
    const response = await authService.fetchWithAuth(
      `${API_BASE}/api/v1/subscriptions/me`,
      {
        method: "GET",
        token,
      },
    );
    if (!response.ok) {
      throw new Error(
        await getResponseErrorMessage(
          response,
          "Failed to load subscription state",
        ),
      );
    }

    const payload = (await response.json()) as SubscriptionState;
    return {
      subscription: payload.subscription || null,
      latest_payment: payload.latest_payment || null,
      trial: payload.trial || null,
      access_status: payload.access_status || "payment_required",
    };
  },

  async startCheckout(
    token: string | null | undefined,
    payload: CheckoutRequest,
  ): Promise<CheckoutResponse> {
    const response = await authService.fetchWithAuth(
      `${API_BASE}/api/v1/subscriptions/checkout`,
      {
        method: "POST",
        token,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
    if (!response.ok) {
      throw new Error(
        await getResponseErrorMessage(
          response,
          "Failed to initialize payment checkout",
        ),
      );
    }
    return (await response.json()) as CheckoutResponse;
  },
};

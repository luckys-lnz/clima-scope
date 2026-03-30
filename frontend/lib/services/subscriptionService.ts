"use client"

import { authService } from "@/lib/services/authService"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface ApiErrorBody {
  detail?: string
  message?: string
}

const getResponseErrorMessage = async (
  response: Response,
  fallback: string,
): Promise<string> => {
  const error = await response.json().catch(
    () => null as ApiErrorBody | null,
  )
  return error?.detail || error?.message || fallback
}

export interface SubscriptionPlan {
  id: string
  name: string
  description?: string
  price: number
  currency: string
  billing_cycle: string
  features: Record<string, unknown>
}

export interface CheckoutRequest {
  plan_id: string
  return_url?: string
  description?: string
}

export interface CheckoutResponse {
  payment_id: string
  merchant_reference: string
  redirect_url: string
  order_tracking_id: string
}

export const subscriptionService = {
  async getPlans(token: string | null | undefined): Promise<SubscriptionPlan[]> {
    const response = await authService.fetchWithAuth(`${API_BASE}/api/v1/subscriptions/plans`, {
      method: "GET",
      token,
    })
    if (!response.ok) {
      throw new Error(await getResponseErrorMessage(response, "Failed to load subscription plans"))
    }
    const payload = (await response.json()) as { plans?: SubscriptionPlan[] }
    return payload.plans || []
  },

  async startCheckout(
    token: string | null | undefined,
    payload: CheckoutRequest,
  ): Promise<CheckoutResponse> {
    const response = await authService.fetchWithAuth(`${API_BASE}/api/v1/subscriptions/checkout`, {
      method: "POST",
      token,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    if (!response.ok) {
      throw new Error(await getResponseErrorMessage(response, "Failed to initialize payment checkout"))
    }
    return (await response.json()) as CheckoutResponse
  },
}


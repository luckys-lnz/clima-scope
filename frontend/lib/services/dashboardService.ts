import { DashboardOverviewData } from "@/lib/models/dashboard"
import { getAuthHeaders, handleTokenExpired } from "@/lib/utils/auth"

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export class DashboardService {
  static async getOverview(
    token: string
  ): Promise<DashboardOverviewData> {
    const res = await fetch(
      `${API_BASE}/api/v1/dashboard/overview`,
      {
        headers: getAuthHeaders(token),
      }
    )

    if (res.status === 401) {
      handleTokenExpired()
    }

    if (!res.ok) {
      const error = await res.json().catch(() => ({}))
      throw new Error(error.detail || "Failed to load dashboard")
    }

    return res.json()
  }
}

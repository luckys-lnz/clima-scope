import { DashboardOverviewData } from "@/lib/models/dashboard"
import { handleTokenExpired } from "@/lib/utils/auth"
import { authService } from "@/lib/services/authService"

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export class DashboardService {
  static async getOverview(
    token: string
  ): Promise<DashboardOverviewData> {
    const accessToken = await authService.getValidAccessToken(token)
    const res = await fetch(
      `${API_BASE}/api/v1/dashboard/overview`,
      {
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
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

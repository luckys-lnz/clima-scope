import type { DashboardOverviewData } from "@/lib/models/dashboard"
import { authService } from "@/lib/services/authService"

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export class DashboardService {
  static async getOverview(
    token?: string | null
  ): Promise<DashboardOverviewData> {
    return authService.requestJsonWithAuth<DashboardOverviewData>(
      `${API_BASE}/api/v1/dashboard/overview`,
      {
        method: "GET",
        token,
      },
    )
  }
}

import { ReportArchiveItem, ReportDetailResponse } from "@/lib/models/report"
import { handleTokenExpired } from "@/lib/utils/auth"
import { authService } from "@/lib/services/authService"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export class ReportService {
  /**
   * Fetch all reports for the current user
   */
  static async getReports(token?: string | null): Promise<ReportArchiveItem[]> {
    return authService.requestJsonWithAuth<ReportArchiveItem[]>(
      `${API_BASE}/api/v1/reports`,
      {
        method: "GET",
        token,
      },
    )
  }

  /**
   * Download a report PDF via secure backend route
   */
  static async downloadReport(token: string | null | undefined, reportId: string) {
    const res = await authService.fetchWithAuth(
      `${API_BASE}/api/v1/reports/download/${reportId}`,
      {
        method: "GET",
        token,
      },
    )

    if (!res.ok) {
      const error = await res.json().catch(
        () => null as { detail?: string; message?: string } | null,
      )
      throw new Error(error?.detail || error?.message || "Failed to download report")
    }

    // Convert to blob for download
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${reportId}.pdf`
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  }

  /**
   * Fetch detailed dynamic metadata for one generated report
   */
  static async getReportDetail(token: string, reportId: string): Promise<ReportDetailResponse> {
    const accessToken = await authService.getValidAccessToken(token)
    const res = await fetch(`${API_BASE}/api/v1/reports/detail/${reportId}`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
    })

    if (res.status === 401) {
      handleTokenExpired()
    }

    if (!res.ok) {
      const error = await res.json().catch(() => ({}))
      throw new Error(error.detail || "Failed to load report detail")
    }

    return res.json()
  }
}

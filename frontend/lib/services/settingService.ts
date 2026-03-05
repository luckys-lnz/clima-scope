import { SettingsResponse } from "@/lib/models/setting"
import { handleTokenExpired } from "@/lib/utils/auth"
import { authService } from "@/lib/services/authService"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export class SettingsService {
  static async getSettings(token: string): Promise<SettingsResponse> {
    const accessToken = await authService.getValidAccessToken(token)
    const res = await fetch(`${API_BASE}/api/v1/setting`, {
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
      throw new Error(error.detail || "Failed to load settings")
    }

    return res.json()
  }

  static async updateTemplate(token: string, pdfTemplateId: string | null) {
    const accessToken = await authService.getValidAccessToken(token)
    const res = await fetch(`${API_BASE}/api/v1/setting`, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        pdf_template_id: pdfTemplateId,
      }),
    })

    if (res.status === 401) {
      handleTokenExpired()
    }

    if (!res.ok) {
      const error = await res.json().catch(() => ({}))
      throw new Error(error.detail || "Failed to update settings")
    }
  }
}

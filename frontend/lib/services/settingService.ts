import { SettingsResponse } from "@/lib/models/setting"
import { getAuthHeaders, handleTokenExpired } from "@/lib/utils/auth"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export class SettingsService {
  static async getSettings(token: string): Promise<SettingsResponse> {
    const res = await fetch(`${API_BASE}/api/v1/setting`, {
      headers: getAuthHeaders(token),
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
    const res = await fetch(`${API_BASE}/api/v1/setting`, {
      method: "PUT",
      headers: getAuthHeaders(token),
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

import type { SettingsResponse } from "@/lib/models/setting"
import { authService } from "@/lib/services/authService"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export class SettingsService {
  static async getSettings(token?: string | null): Promise<SettingsResponse> {
    return authService.requestJsonWithAuth<SettingsResponse>(
      `${API_BASE}/api/v1/setting`,
      {
        method: "GET",
        token,
      },
    )
  }

  static async updateTemplate(
    token: string | null | undefined,
    pdfTemplateId: string | null,
  ) {
    const res = await authService.fetchWithAuth(`${API_BASE}/api/v1/setting`, {
      method: "PUT",
      token,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        pdf_template_id: pdfTemplateId,
      }),
    })

    if (!res.ok) {
      const error = await res.json().catch(
        () => null as { detail?: string; message?: string } | null,
      )
      throw new Error(error?.detail || error?.message || "Failed to update settings")
    }
  }
}

import type { SettingsResponse, UpdateSettingsPayload, MapPreviewResponse } from "@/lib/models/setting"
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

  static async updateSettings(
    token: string | null | undefined,
    payload: UpdateSettingsPayload,
  ) {
    const res = await authService.fetchWithAuth(`${API_BASE}/api/v1/setting`, {
      method: "PUT",
      token,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })

    if (!res.ok) {
      const error = await res.json().catch(
        () => null as { detail?: string; message?: string } | null,
      )
      throw new Error(error?.detail || error?.message || "Failed to update settings")
    }
  }

  static async getCountyPreview(
    token: string | null | undefined,
    county?: string,
  ): Promise<MapPreviewResponse> {
    const query = county ? `?county=${encodeURIComponent(county)}` : ""
    return authService.requestJsonWithAuth<MapPreviewResponse>(
      `${API_BASE}/api/v1/setting/preview-geometry${query}`,
      {
        method: "GET",
        token,
      },
    )
  }
}

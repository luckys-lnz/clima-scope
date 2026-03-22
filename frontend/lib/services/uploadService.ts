// lib/services/uploadService.ts
import type { Upload } from "@/lib/models/upload"
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

export interface ReportingPeriod {
  report_week: number
  report_year: number
  report_start_at: string // YYYY-MM-DD
  report_end_at: string   // YYYY-MM-DD
}

export const uploadService = {
  // -----------------------
  // UPLOAD FILES
  // -----------------------
  uploadFiles: async (
    files: File[] | File,
    file_type = "observations",
    period: ReportingPeriod
  ): Promise<Upload[]> => {
    const formData = new FormData()
    formData.append("file_type", file_type)

    // ✅ reporting period
    formData.append("report_week", String(period.report_week))
    formData.append("report_year", String(period.report_year))
    formData.append("report_start_at", period.report_start_at)
    formData.append("report_end_at", period.report_end_at)

    // files
    if (Array.isArray(files)) {
      files.forEach((f) => formData.append("files", f))
    } else {
      formData.append("files", files)
    }

    const response = await authService.fetchWithAuth(`${API_BASE}/api/v1/uploads/`, {
      method: "POST",
      body: formData,
    })

    if (!response.ok) {
      throw new Error(await getResponseErrorMessage(response, "File upload failed"))
    }

    return (await response.json()) as Upload[]
  },

  // -----------------------
  // GET ALL UPLOADS
  // -----------------------
  getAll: async (): Promise<Upload[]> => {
    const response = await authService.fetchWithAuth(`${API_BASE}/api/v1/uploads/`, {
      method: "GET",
    })

    if (!response.ok) {
      throw new Error(await getResponseErrorMessage(response, "Failed to fetch uploads"))
    }

    return (await response.json()) as Upload[]
  },

  // -----------------------
  // GET SINGLE UPLOAD
  // -----------------------
  getOne: async (id: string): Promise<Upload> => {
    const response = await authService.fetchWithAuth(`${API_BASE}/api/v1/uploads/${id}`, {
      method: "GET",
    })

    if (!response.ok) {
      throw new Error(await getResponseErrorMessage(response, "Failed to fetch upload"))
    }

    return (await response.json()) as Upload
  },

  // -----------------------
  // UPDATE UPLOAD STATUS
  // -----------------------
  updateStatus: async (id: string, status: Upload["status"]): Promise<Upload> => {
    const formData = new FormData()
    formData.append("status", status)

    const response = await authService.fetchWithAuth(`${API_BASE}/api/v1/uploads/${id}`, {
      method: "PATCH",
      body: formData,
    })

    if (!response.ok) {
      throw new Error(await getResponseErrorMessage(response, "Failed to update status"))
    }

    return (await response.json()) as Upload
  },
}

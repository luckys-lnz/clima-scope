// lib/services/uploadService.ts
import type { Upload } from "@/lib/models/upload"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

function getToken(): string {
  const token = localStorage.getItem("access_token")
  if (!token) throw new Error("No active session")
  return token
}

export const uploadService = {
  // -----------------------
  // UPLOAD FILES
  // -----------------------
  uploadFiles: async (files: File[] | File, file_type = "observations"): Promise<Upload[]> => {
    const token = getToken()

    const formData = new FormData()
    formData.append("file_type", file_type)

    if (Array.isArray(files)) {
      files.forEach((f) => {
        formData.append("files", f)
      })
    } else {
      formData.append("files", files)
    }

    const response = await fetch(`${API_BASE}/api/v1/uploads`, {
      method: "POST",
      body: formData,
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })

    const resData = await response.json()
    if (!response.ok) {
      throw new Error(resData.detail || resData.message || "File upload failed")
    }

    return resData as Upload[]
  },

  // -----------------------
  // GET ALL UPLOADS
  // -----------------------
  getAll: async (): Promise<Upload[]> => {
    const token = getToken()
    const response = await fetch(`${API_BASE}/api/v1/uploads`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    })

    const resData = await response.json()
    if (!response.ok) {
      throw new Error(resData.detail || resData.message || "Failed to fetch uploads")
    }

    return resData as Upload[]
  },

  // -----------------------
  // GET SINGLE UPLOAD
  // -----------------------
  getOne: async (id: string): Promise<Upload> => {
    const token = getToken()
    const response = await fetch(`${API_BASE}/api/v1/uploads/${id}`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    })

    const resData = await response.json()
    if (!response.ok) {
      throw new Error(resData.detail || resData.message || "Failed to fetch upload")
    }

    return resData as Upload
  },

  // -----------------------
  // UPDATE UPLOAD STATUS
  // -----------------------
  updateStatus: async (id: string, status: Upload["status"]): Promise<Upload> => {
    const token = getToken()
    const formData = new FormData()
    formData.append("status", status)

    const response = await fetch(`${API_BASE}/api/v1/uploads/${id}`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    })

    const resData = await response.json()
    if (!response.ok) {
      throw new Error(resData.detail || resData.message || "Failed to update status")
    }

    return resData as Upload
  },
}

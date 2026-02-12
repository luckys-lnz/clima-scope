// lib/services/uploadService.ts
import { supabase } from "@/lib/supabaseClient"
import type { Upload } from "@/lib/models/upload"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

async function getToken(): Promise<string> {
  const {
    data: { session },
    error,
  } = await supabase.auth.getSession()

  if (error) throw new Error(error.message)
  if (!session?.access_token) throw new Error("No active session")
  return session.access_token
}

export const uploadService = {
  // -----------------------
  // UPLOAD SINGLE OR MULTIPLE FILES
  // -----------------------
  uploadFiles: async (files: File[] | File, file_type = "observations"): Promise<Upload[]> => {
    const token = await getToken()

    const formData = new FormData()
    formData.append("file_type", file_type)

    // FIXED: Always use 'files' field name for BOTH single and multiple
    if (Array.isArray(files)) {
      // Multiple files - append each with field name 'files'
      files.forEach((f) => {
        formData.append("files", f)
      })
    } else {
      // Single file - also append with field name 'files'
      formData.append("files", files)
    }

    const response = await fetch(`${API_BASE}/api/v1/uploads/`, {
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
    const token = await getToken()
    const response = await fetch(`${API_BASE}/api/v1/uploads/`, {
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
    const token = await getToken()
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
    const token = await getToken()
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

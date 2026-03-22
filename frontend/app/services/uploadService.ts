// app/services/uploadService.ts
"use client"

import { supabase } from "../../lib/supabaseClient"
import type { Upload } from "../models/upload"

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
  // UPLOAD FILE
  // -----------------------
  uploadFile: async (file: File): Promise<Upload> => {
    const token = await getToken()
    const formData = new FormData()
    formData.append("file", file)
    formData.append("file_type", "observations")

    const response = await fetch(`${API_BASE}/api/v1/upload/`, {
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

    return resData.upload as Upload
  },

  // -----------------------
  // GET ALL UPLOADS
  // -----------------------
  getAll: async (): Promise<Upload[]> => {
    const token = await getToken()
    const response = await fetch(`${API_BASE}/api/v1/upload/`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    })

    const resData = await response.json()
    if (!response.ok) {
      throw new Error(resData.detail || resData.message || "Failed to fetch uploads")
    }

    return resData.uploads as Upload[]
  },

  // -----------------------
  // GET SINGLE UPLOAD
  // -----------------------
  getOne: async (id: string): Promise<Upload> => {
    const token = await getToken()
    const response = await fetch(`${API_BASE}/api/v1/upload/${id}`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
    })

    const resData = await response.json()
    if (!response.ok) {
      throw new Error(resData.detail || resData.message || "Failed to fetch upload")
    }

    return resData.upload as Upload
  },

  // -----------------------
  // UPDATE UPLOAD STATUS
  // -----------------------
  updateStatus: async (id: string, status: Upload["status"]): Promise<Upload> => {
    const token = await getToken()
    const response = await fetch(`${API_BASE}/api/v1/upload/${id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ status }),
    })

    const resData = await response.json()
    if (!response.ok) {
      throw new Error(resData.detail || resData.message || "Failed to update status")
    }

    return resData.upload as Upload
  },
}

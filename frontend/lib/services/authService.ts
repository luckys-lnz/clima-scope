// app/services/authService.ts
"use client"

import type { 
  SignUpData, 
  LoginData, 
  User 
} from "@/lib/models/auth"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface LoginResponse {
  user: User
  access_token: string
}

export interface Session {
  user: User
  access_token: string
}

export const authService = {
  // -----------------------
  // LOGIN - Calls your backend
  // -----------------------
  login: async (data: LoginData): Promise<LoginResponse> => {
    const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })

    const result = await response.json()
    if (!response.ok) {
      throw new Error(result.detail || "Login failed")
    }

    // Store in localStorage
    localStorage.setItem("access_token", result.access_token)
    localStorage.setItem("user", JSON.stringify(result.user))

    return result
  },

  // -----------------------
  // SIGNUP via Backend
  // -----------------------
  signup: async (data: SignUpData): Promise<{ message: string }> => {
    const response = await fetch(`${API_BASE}/api/v1/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })

    const resData = await response.json()
    if (!response.ok) {
      throw new Error(resData.detail || resData.message || "Signup failed")
    }

    return resData
  },

  // -----------------------
  // LOGOUT
  // -----------------------
  logout: async (token: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/api/v1/auth/logout`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || "Logout failed")
    }

    localStorage.removeItem("access_token")
    localStorage.removeItem("user")
  },

  // -----------------------
  // GET CURRENT USER FROM TOKEN
  // -----------------------
  getCurrentUser: async (token: string): Promise<User> => {
    const response = await fetch(`${API_BASE}/api/v1/auth/me`, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    })

    if (!response.ok) {
      throw new Error("Failed to get user")
    }

    return response.json()
  },

  // -----------------------
  // GET SESSION FROM LOCALSTORAGE
  // -----------------------
  getSession: async (): Promise<Session | null> => {
    const token = localStorage.getItem("access_token")
    const userStr = localStorage.getItem("user")
    
    if (!token || !userStr) {
      return null
    }

    try {
      const user = JSON.parse(userStr) as User
      return {
        user,
        access_token: token
      }
    } catch {
      return null
    }
  }
}

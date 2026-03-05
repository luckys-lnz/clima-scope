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
  refresh_token: string  // ← ADD THIS
  expires_in: number
}

export interface RefreshResponse {
  access_token: string
  refresh_token: string  // ← ADD THIS
  expires_in: number
}

export interface Session {
  user: User
  access_token: string
  refresh_token: string  // ← ADD THIS
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

    // Store BOTH tokens in localStorage
    localStorage.setItem("access_token", result.access_token)
    localStorage.setItem("refresh_token", result.refresh_token)  // ← ADD THIS
    localStorage.setItem("user", JSON.stringify(result.user))

    return result
  },

  // -----------------------
  // REFRESH TOKEN - NEW METHOD!
  // -----------------------
  refreshToken: async (refresh_token: string): Promise<RefreshResponse> => {
    const response = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token }),
    })

    const result = await response.json()
    if (!response.ok) {
      throw new Error(result.detail || "Token refresh failed")
    }

    // Update stored tokens
    localStorage.setItem("access_token", result.access_token)
    localStorage.setItem("refresh_token", result.refresh_token)

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

    // Clear ALL tokens
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")  // ← ADD THIS
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

    const user = await response.json()
    localStorage.setItem("user", JSON.stringify(user))
    return user
  },

  // -----------------------
  // GET SESSION FROM LOCALSTORAGE
  // -----------------------
  getSession: async (): Promise<Session | null> => {
    let access_token = localStorage.getItem("access_token")
    let refresh_token = localStorage.getItem("refresh_token")
    const userStr = localStorage.getItem("user")
    
    if (!access_token || !refresh_token || !userStr) {
      return null
    }

    try {
      if (authService.isTokenExpired(access_token)) {
        const refreshed = await authService.refreshToken(refresh_token)
        access_token = refreshed.access_token
        refresh_token = refreshed.refresh_token
      }

      const user = JSON.parse(userStr) as User
      return {
        user,
        access_token,
        refresh_token
      }
    } catch {
      return null
    }
  },

  // -----------------------
  // CHECK IF TOKEN IS EXPIRED (utility)
  // -----------------------
  isTokenExpired: (token: string): boolean => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.exp * 1000 < Date.now()
    } catch {
      return true
    }
  },

  getValidAccessToken: async (token?: string | null): Promise<string> => {
    const accessToken = token || localStorage.getItem("access_token")
    if (!accessToken) {
      throw new Error("No active session")
    }

    if (!authService.isTokenExpired(accessToken)) {
      return accessToken
    }

    const refreshToken = localStorage.getItem("refresh_token")
    if (!refreshToken) {
      throw new Error("Session expired. Please sign in again.")
    }

    const refreshed = await authService.refreshToken(refreshToken)
    return refreshed.access_token
  }
}

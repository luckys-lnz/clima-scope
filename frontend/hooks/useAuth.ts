// hooks/useAuth.ts
"use client"

import { useEffect, useState } from "react"
import { authService } from "@/lib/services/authService"
import type { User } from "@/lib/models/auth"

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
}

// Helper to check if token is expired
function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    // exp is in seconds, Date.now() is in milliseconds
    return payload.exp * 1000 < Date.now()
  } catch {
    return true // If can't parse, consider expired
  }
}

export function useAuth() {
  const [auth, setAuth] = useState<AuthState>({
    user: null,
    token: null,
    isLoading: true
  })

  useEffect(() => {
    const initAuth = async () => {
      try {
        // Get token from localStorage directly
        const token = localStorage.getItem("access_token")
        const userStr = localStorage.getItem("user")
        
        if (!token || !userStr) {
          setAuth({ user: null, token: null, isLoading: false })
          return
        }

        // Check if token is expired
        if (isTokenExpired(token)) {
          console.log("Token expired")
          localStorage.removeItem("access_token")
          localStorage.removeItem("user")
          setAuth({ user: null, token: null, isLoading: false })
          return
        }

        // Verify token is still valid by getting user from backend
        try {
          const user = await authService.getCurrentUser(token)
          setAuth({
            user,
            token,
            isLoading: false
          })
        } catch (error) {
          // Token invalid - clear storage
          console.error("Token validation failed:", error)
          localStorage.removeItem("access_token")
          localStorage.removeItem("user")
          setAuth({ user: null, token: null, isLoading: false })
        }
      } catch (error) {
        console.error("Auth initialization error:", error)
        setAuth({ user: null, token: null, isLoading: false })
      }
    }

    initAuth()
  }, [])

  const login = async (email: string, password: string) => {
    const response = await authService.login({ email, password })
    
    // Store in localStorage
    localStorage.setItem("access_token", response.access_token)
    localStorage.setItem("user", JSON.stringify(response.user))
    
    setAuth({
      user: response.user,
      token: response.access_token,
      isLoading: false
    })
    
    return response.user
  }

  const logout = async () => {
    const token = auth.token
    if (token) {
      try {
        await authService.logout(token)
      } catch (error) {
        console.error("Logout error:", error)
      }
    }
    
    // Clear localStorage
    localStorage.removeItem("access_token")
    localStorage.removeItem("user")
    
    setAuth({ user: null, token: null, isLoading: false })
  }

  return {
    user: auth.user,
    token: auth.token,
    isLoading: auth.isLoading,
    login,
    logout
  }
}
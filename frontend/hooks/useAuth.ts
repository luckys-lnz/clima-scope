// hooks/useAuth.ts
"use client"

import { useEffect, useState } from "react"
import { authService } from "@/lib/services/authService"
import type { User } from "@/lib/models/auth"

interface AuthState {
  user: User | null
  access_token: string | null
  refresh_token: string | null  // ← ADD THIS
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
    access_token: null,
    refresh_token: null,  // ← ADD THIS
    isLoading: true
  })

  useEffect(() => {
    const initAuth = async () => {
      try {
        // Get tokens from localStorage
        const access_token = localStorage.getItem("access_token")
        const refresh_token = localStorage.getItem("refresh_token")  // ← ADD THIS
        const userStr = localStorage.getItem("user")
        
        if (!access_token || !refresh_token || !userStr) {  // ← UPDATE CONDITION
          setAuth({ user: null, access_token: null, refresh_token: null, isLoading: false })
          return
        }

        // Check if token is expired
        if (isTokenExpired(access_token)) {
          console.log("Access token expired, attempting refresh...")
          
          // TRY TO REFRESH THE TOKEN!
          try {
            const refreshResponse = await authService.refreshToken(refresh_token)
            
            // Store new tokens
            localStorage.setItem("access_token", refreshResponse.access_token)
            localStorage.setItem("refresh_token", refreshResponse.refresh_token)
            
            // Get user with new token
            const user = await authService.getCurrentUser(refreshResponse.access_token)
            
            setAuth({
              user,
              access_token: refreshResponse.access_token,
              refresh_token: refreshResponse.refresh_token,
              isLoading: false
            })
            return
          } catch (refreshError) {
            console.error("Token refresh failed:", refreshError)
            // Clear everything if refresh fails
            localStorage.removeItem("access_token")
            localStorage.removeItem("refresh_token")
            localStorage.removeItem("user")
            setAuth({ user: null, access_token: null, refresh_token: null, isLoading: false })
            return
          }
        }

        // Token still valid - verify with backend
        try {
          const user = await authService.getCurrentUser(access_token)
          setAuth({
            user,
            access_token,
            refresh_token,  // ← ADD THIS
            isLoading: false
          })
        } catch (error) {
          // Token invalid - clear storage
          console.error("Token validation failed:", error)
          localStorage.removeItem("access_token")
          localStorage.removeItem("refresh_token")  // ← ADD THIS
          localStorage.removeItem("user")
          setAuth({ user: null, access_token: null, refresh_token: null, isLoading: false })
        }
      } catch (error) {
        console.error("Auth initialization error:", error)
        setAuth({ user: null, access_token: null, refresh_token: null, isLoading: false })
      }
    }

    initAuth()
  }, [])

  const login = async (email: string, password: string) => {
    const response = await authService.login({ email, password })
    
    // Store BOTH tokens in localStorage
    localStorage.setItem("access_token", response.access_token)
    localStorage.setItem("refresh_token", response.refresh_token)  // ← ADD THIS
    localStorage.setItem("user", JSON.stringify(response.user))
    
    setAuth({
      user: response.user,
      access_token: response.access_token,
      refresh_token: response.refresh_token,  // ← ADD THIS
      isLoading: false
    })
    
    return response.user
  }

  const logout = async () => {
    const token = auth.access_token
    if (token) {
      try {
        await authService.logout(token)
      } catch (error) {
        console.error("Logout error:", error)
      }
    }
    
    // Clear ALL tokens from localStorage
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")  // ← ADD THIS
    localStorage.removeItem("user")
    
    setAuth({ user: null, access_token: null, refresh_token: null, isLoading: false })
  }

  return {
    user: auth.user,
    token: auth.access_token,
    access_token: auth.access_token,
    refresh_token: auth.refresh_token,  // ← ADD THIS
    isLoading: auth.isLoading,
    login,
    logout
  }
}

"use client"

import { useCallback, useEffect, useState } from "react"
import {
  AUTH_STATE_EVENT,
  authService,
  type AuthStateEventDetail,
} from "@/lib/services/authService"
import type { User } from "@/lib/models/auth"

interface AuthState {
  user: User | null
  access_token: string | null
  refresh_token: string | null
  isLoading: boolean
}

const EMPTY_AUTH_STATE: Readonly<Omit<AuthState, "isLoading">> = {
  user: null,
  access_token: null,
  refresh_token: null,
}

export function useAuth() {
  const [auth, setAuth] = useState<AuthState>({
    ...EMPTY_AUTH_STATE,
    isLoading: true,
  })

  useEffect(() => {
    let isMounted = true

    const initializeAuth = async (): Promise<void> => {
      try {
        const session = await authService.getSession()
        if (!session) {
          if (isMounted) {
            setAuth({
              ...EMPTY_AUTH_STATE,
              isLoading: false,
            })
          }
          return
        }

        if (isMounted) {
          setAuth({
            user: session.user,
            access_token: session.access_token,
            refresh_token: session.refresh_token,
            isLoading: false,
          })
        }
      } catch (error) {
        console.error("Auth initialization error:", error)
        authService.clearSession()
        if (isMounted) {
          setAuth({
            ...EMPTY_AUTH_STATE,
            isLoading: false,
          })
        }
      }
    }

    void initializeAuth()

    return () => {
      isMounted = false
    }
  }, [])

  useEffect(() => {
    const handleAuthStateChanged = (
      event: Event,
    ): void => {
      const customEvent = event as CustomEvent<AuthStateEventDetail>
      const detail = customEvent.detail
      if (!detail) return

      if (detail.type === "session_cleared") {
        setAuth({
          ...EMPTY_AUTH_STATE,
          isLoading: false,
        })
        return
      }

      setAuth((prev) => ({
        user: detail.user ?? prev.user,
        access_token: detail.access_token ?? prev.access_token,
        refresh_token: detail.refresh_token ?? prev.refresh_token,
        isLoading: false,
      }))
    }

    window.addEventListener(AUTH_STATE_EVENT, handleAuthStateChanged as EventListener)

    return () => {
      window.removeEventListener(
        AUTH_STATE_EVENT,
        handleAuthStateChanged as EventListener,
      )
    }
  }, [])

  const login = useCallback(async (email: string, password: string): Promise<User> => {
    const response = await authService.login({ email, password })
    setAuth({
      user: response.user,
      access_token: response.access_token,
      refresh_token: response.refresh_token,
      isLoading: false,
    })
    return response.user
  }, [])

  const logout = useCallback(async (): Promise<void> => {
    const token = auth.access_token

    try {
      if (token) {
        await authService.logout(token)
      } else {
        authService.clearSession()
      }
    } catch (error) {
      console.error("Logout error:", error)
      authService.clearSession()
    } finally {
      setAuth({
        ...EMPTY_AUTH_STATE,
        isLoading: false,
      })
    }
  }, [auth.access_token])

  return {
    user: auth.user,
    token: auth.access_token,
    access_token: auth.access_token,
    refresh_token: auth.refresh_token,
    isLoading: auth.isLoading,
    login,
    logout,
  }
}

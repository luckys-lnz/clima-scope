"use client"

import { useCallback, useEffect, useState } from "react"
import {
  AUTH_STATE_EVENT,
  authService,
  type AuthStateEventDetail,
  type AuthClearReason,
} from "@/lib/services/authService"
import type { User } from "@/lib/models/auth"

type AuthStatus = "loading" | "authenticated" | "unauthenticated" | "expired"

interface AuthState {
  user: User | null
  access_token: string | null
  refresh_token: string | null
  isLoading: boolean
  status: AuthStatus
  clearReason: AuthClearReason | null
}

const EMPTY_AUTH_STATE: Readonly<Omit<AuthState, "isLoading">> = {
  user: null,
  access_token: null,
  refresh_token: null,
  status: "unauthenticated",
  clearReason: null,
}

const resolveStatus = (reason?: AuthClearReason | null): AuthStatus =>
  reason === "expired" ? "expired" : "unauthenticated"

export function useAuth() {
  const [auth, setAuth] = useState<AuthState>({
    ...EMPTY_AUTH_STATE,
    isLoading: true,
    status: "loading",
  })

  useEffect(() => {
    let isMounted = true

    const initializeAuth = async (): Promise<void> => {
      try {
        const session = await authService.getSession()
        if (!session) {
          const reason = authService.getLastClearReason()
          if (isMounted) {
            setAuth({
              ...EMPTY_AUTH_STATE,
              isLoading: false,
              status: resolveStatus(reason),
              clearReason: reason,
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
            status: "authenticated",
            clearReason: null,
          })
        }
      } catch (error) {
        console.error("Auth initialization error:", error)
        authService.clearSession("manual")
        if (isMounted) {
          setAuth({
            ...EMPTY_AUTH_STATE,
            isLoading: false,
            status: "unauthenticated",
            clearReason: "manual",
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
        const reason = detail.reason ?? null
        setAuth({
          ...EMPTY_AUTH_STATE,
          isLoading: false,
          status: resolveStatus(reason),
          clearReason: reason,
        })
        return
      }

      setAuth((prev) => ({
        user: detail.user ?? prev.user,
        access_token: detail.access_token ?? prev.access_token,
        refresh_token: detail.refresh_token ?? prev.refresh_token,
        isLoading: false,
        status: "authenticated",
        clearReason: null,
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
      status: "authenticated",
      clearReason: null,
    })
    return response.user
  }, [])

  const logout = useCallback(async (): Promise<void> => {
    const token = auth.access_token

    try {
      if (token) {
        await authService.logout(token)
      } else {
        authService.clearSession("logout")
      }
    } catch (error) {
      console.error("Logout error:", error)
      authService.clearSession("logout")
    }
  }, [auth.access_token])

  return {
    user: auth.user,
    token: auth.access_token,
    access_token: auth.access_token,
    refresh_token: auth.refresh_token,
    isLoading: auth.isLoading,
    status: auth.status,
    clearReason: auth.clearReason,
    login,
    logout,
  }
}

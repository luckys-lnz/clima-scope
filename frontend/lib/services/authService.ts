"use client"

import type { LoginData, SignUpData, User } from "@/lib/models/auth"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
const DASHBOARD_CACHE_KEY = "dashboard_overview_cache_v1"
const REPORTS_CACHE_KEY = "report_archive_cache_v1"
const SETTINGS_CACHE_KEY = "system_settings_cache"
const TOKEN_REFRESH_LEEWAY_MS = 60_000
export const AUTH_STATE_EVENT = "clima:auth-state-changed"

const STORAGE_KEYS = {
  accessToken: "access_token",
  refreshToken: "refresh_token",
  user: "user",
} as const

type CacheKey =
  | typeof DASHBOARD_CACHE_KEY
  | typeof REPORTS_CACHE_KEY
  | typeof SETTINGS_CACHE_KEY

interface JwtPayload {
  exp?: number
}

interface ApiErrorBody {
  detail?: string
  message?: string
}

export interface LoginResponse {
  user: User
  access_token: string
  refresh_token: string
  expires_in: number
}

export interface RefreshResponse {
  access_token: string
  refresh_token: string
  expires_in: number
}

export interface Session {
  user: User
  access_token: string
  refresh_token: string
}

export type AuthStateEventType = "session_updated" | "session_cleared"
export type AuthClearReason = "logout" | "expired" | "manual"

export interface AuthStateEventDetail {
  type: AuthStateEventType
  access_token: string | null
  refresh_token: string | null
  user: User | null
  reason?: AuthClearReason
}

export interface AuthFetchOptions extends Omit<RequestInit, "headers"> {
  headers?: HeadersInit
  token?: string | null
  retryOnUnauthorized?: boolean
}

export interface JsonAuthRequestOptions<TBody>
  extends Omit<AuthFetchOptions, "body"> {
  body?: TBody
}

let refreshInFlight: Promise<RefreshResponse> | null = null
let lastClearReason: AuthClearReason | null = null

const clearCacheEntries = (keys: readonly CacheKey[]): void => {
  if (typeof window === "undefined") return
  keys.forEach((key) => sessionStorage.removeItem(key))
}

const emitAuthState = (detail: AuthStateEventDetail): void => {
  if (typeof window === "undefined") return
  window.dispatchEvent(
    new CustomEvent<AuthStateEventDetail>(AUTH_STATE_EVENT, { detail }),
  )
}

const setSession = (
  accessToken: string,
  refreshToken: string,
  user?: User,
): void => {
  if (typeof window === "undefined") return
  lastClearReason = null
  localStorage.setItem(STORAGE_KEYS.accessToken, accessToken)
  localStorage.setItem(STORAGE_KEYS.refreshToken, refreshToken)
  if (user) {
    localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(user))
  }
  const resolvedUser = user ?? getStoredUser()
  emitAuthState({
    type: "session_updated",
    access_token: accessToken,
    refresh_token: refreshToken,
    user: resolvedUser,
  })
}

const getStoredAccessToken = (): string | null =>
  typeof window === "undefined"
    ? null
    : localStorage.getItem(STORAGE_KEYS.accessToken)

const getStoredRefreshToken = (): string | null =>
  typeof window === "undefined"
    ? null
    : localStorage.getItem(STORAGE_KEYS.refreshToken)

const getStoredUser = (): User | null => {
  if (typeof window === "undefined") return null
  const raw = localStorage.getItem(STORAGE_KEYS.user)
  if (!raw) return null

  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}

const clearSessionStorage = (reason: AuthClearReason = "manual"): void => {
  if (typeof window === "undefined") return
  lastClearReason = reason
  localStorage.removeItem(STORAGE_KEYS.accessToken)
  localStorage.removeItem(STORAGE_KEYS.refreshToken)
  localStorage.removeItem(STORAGE_KEYS.user)
  emitAuthState({
    type: "session_cleared",
    access_token: null,
    refresh_token: null,
    user: null,
    reason,
  })
}

const decodeJwtPayload = (token: string): JwtPayload | null => {
  try {
    const [, payloadB64 = ""] = token.split(".")
    if (!payloadB64) return null
    const payload = JSON.parse(atob(payloadB64)) as JwtPayload
    return payload
  } catch {
    return null
  }
}

const isTokenExpired = (token: string, leewayMs = 0): boolean => {
  const payload = decodeJwtPayload(token)
  if (!payload?.exp) return true
  return payload.exp * 1000 - leewayMs <= Date.now()
}

const parseJsonSafe = async <T>(response: Response): Promise<T | null> => {
  try {
    return (await response.json()) as T
  } catch {
    return null
  }
}

const getErrorMessage = async (
  response: Response,
  fallback: string,
): Promise<string> => {
  const body = await parseJsonSafe<ApiErrorBody>(response)
  return body?.detail || body?.message || fallback
}

const withAuthorizationHeader = (
  token: string,
  headers?: HeadersInit,
): Headers => {
  const resolvedHeaders = new Headers(headers)
  resolvedHeaders.set("Authorization", `Bearer ${token}`)
  return resolvedHeaders
}

const createJsonHeaders = (headers?: HeadersInit): Headers => {
  const resolvedHeaders = new Headers(headers)
  if (!resolvedHeaders.has("Content-Type")) {
    resolvedHeaders.set("Content-Type", "application/json")
  }
  return resolvedHeaders
}

const refreshWithToken = (refreshToken: string): Promise<RefreshResponse> => {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      const response = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
        method: "POST",
        headers: createJsonHeaders(),
        body: JSON.stringify({ refresh_token: refreshToken }),
      })

      const result = await parseJsonSafe<RefreshResponse & ApiErrorBody>(response)
      if (!response.ok || !result?.access_token || !result.refresh_token) {
        throw new Error(result?.detail || "Session expired. Please sign in again.")
      }

      setSession(result.access_token, result.refresh_token)
      return {
        access_token: result.access_token,
        refresh_token: result.refresh_token,
        expires_in: result.expires_in,
      }
    })().finally(() => {
      refreshInFlight = null
    })
  }

  return refreshInFlight
}

export const authService = {
  clearSession(reason: AuthClearReason = "manual"): void {
    clearSessionStorage(reason)
    clearCacheEntries([DASHBOARD_CACHE_KEY, REPORTS_CACHE_KEY, SETTINGS_CACHE_KEY])
  },

  getLastClearReason(): AuthClearReason | null {
    return lastClearReason
  },

  isTokenExpired(token: string, leewayMs = 0): boolean {
    return isTokenExpired(token, leewayMs)
  },

  async login(data: LoginData): Promise<LoginResponse> {
    const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
      method: "POST",
      headers: createJsonHeaders(),
      body: JSON.stringify(data),
    })

    const result = await parseJsonSafe<LoginResponse & ApiErrorBody>(response)
    if (!response.ok || !result?.access_token || !result.refresh_token || !result.user) {
      throw new Error(result?.detail || "Login failed")
    }

    setSession(result.access_token, result.refresh_token, result.user)
    clearCacheEntries([DASHBOARD_CACHE_KEY, REPORTS_CACHE_KEY, SETTINGS_CACHE_KEY])

    return {
      user: result.user,
      access_token: result.access_token,
      refresh_token: result.refresh_token,
      expires_in: result.expires_in,
    }
  },

  async refreshToken(refreshToken: string): Promise<RefreshResponse> {
    return refreshWithToken(refreshToken)
  },

  async signup(data: SignUpData): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE}/api/v1/auth/signup`, {
      method: "POST",
      headers: createJsonHeaders(),
      body: JSON.stringify(data),
    })

    const result = await parseJsonSafe<{ message?: string } & ApiErrorBody>(response)
    if (!response.ok) {
      throw new Error(result?.detail || result?.message || "Signup failed")
    }

    return { message: result?.message ?? "Signup successful" }
  },

  async logout(token: string): Promise<void> {
    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/logout`, {
        method: "POST",
        headers: withAuthorizationHeader(token, createJsonHeaders()),
      })

      if (!response.ok) {
        throw new Error(await getErrorMessage(response, "Logout failed"))
      }
    } finally {
      authService.clearSession("logout")
    }
  },

  async getCurrentUser(token: string): Promise<User> {
    const response = await authService.fetchWithAuth(`${API_BASE}/api/v1/auth/me`, {
      token,
      method: "GET",
    })

    if (!response.ok) {
      throw new Error(await getErrorMessage(response, "Failed to get user"))
    }

    const user = (await response.json()) as User
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(user))
      emitAuthState({
        type: "session_updated",
        access_token: getStoredAccessToken(),
        refresh_token: getStoredRefreshToken(),
        user,
      })
    }
    return user
  },

  async getSession(): Promise<Session | null> {
    const refreshToken = getStoredRefreshToken()

    if (!refreshToken) {
      return null
    }

    try {
      const accessToken = await authService.getValidAccessToken()
      let user = getStoredUser()

      // Recover session identity even if localStorage user payload is missing/stale.
      if (!user) {
        user = await authService.getCurrentUser(accessToken)
      }

      if (!user) {
        authService.clearSession("expired")
        return null
      }

      return {
        user,
        access_token: accessToken,
        refresh_token: getStoredRefreshToken() ?? refreshToken,
      }
    } catch {
      authService.clearSession("expired")
      return null
    }
  },

  async getValidAccessToken(
    token?: string | null,
    options: Readonly<{ forceRefresh?: boolean }> = {},
  ): Promise<string> {
    const { forceRefresh = false } = options
    const storedAccessToken = getStoredAccessToken()
    const accessToken = storedAccessToken ?? token ?? null

    if (
      accessToken &&
      !forceRefresh &&
      !authService.isTokenExpired(accessToken, TOKEN_REFRESH_LEEWAY_MS)
    ) {
      return accessToken
    }

    const refreshToken = getStoredRefreshToken()
    if (!refreshToken) {
      throw new Error("Session expired. Please sign in again.")
    }

    const refreshed = await refreshWithToken(refreshToken)
    return refreshed.access_token
  },

  async fetchWithAuth(
    input: RequestInfo | URL,
    options: AuthFetchOptions = {},
  ): Promise<Response> {
    const { token, retryOnUnauthorized = true, headers, ...rest } = options

    const execute = async (accessToken: string): Promise<Response> =>
      fetch(input, {
        ...rest,
        headers: withAuthorizationHeader(accessToken, headers),
      })

    try {
      const currentAccessToken = await authService.getValidAccessToken(token)
      let response = await execute(currentAccessToken)

      if (response.status !== 401 || !retryOnUnauthorized) {
        return response
      }

      const refreshedToken = await authService.getValidAccessToken(undefined, {
        forceRefresh: true,
      })
      response = await execute(refreshedToken)

      return response
    } catch (error) {
      if (error instanceof Error && error.message.includes("Session expired")) {
        authService.clearSession("expired")
      }
      throw error
    }
  },

  async requestJsonWithAuth<TResponse, TBody = undefined>(
    input: RequestInfo | URL,
    options: JsonAuthRequestOptions<TBody> = {},
  ): Promise<TResponse> {
    const { body, headers, ...rest } = options
    const response = await authService.fetchWithAuth(input, {
      ...rest,
      headers: createJsonHeaders(headers),
      body: body === undefined ? undefined : JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error(await getErrorMessage(response, "Request failed"))
    }

    return (await response.json()) as TResponse
  },
}

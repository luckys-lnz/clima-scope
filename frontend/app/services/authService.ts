// app/services/authService.ts
"use client"

import { supabase } from "../../lib/supabaseClient"
import type { SignUpData, LoginData, User } from "../models/auth"


export const authService = {
  // -----------------------
  // LOGIN
  // -----------------------
  login: async (data: LoginData): Promise<User> => {
    const { email, password } = data

    const { data: { session }, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) throw new Error(error.message)
    if (!session) throw new Error("No session returned")

    return session.user as unknown as User
  },

  // -----------------------
  // SIGNUP via Backend
  // -----------------------
  signup: async (data: SignUpData): Promise<{ message: string }> => {
    // Here we call your backend API, which uses service key
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/signup`, {
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
  logout: async (): Promise<void> => {
    const { error } = await supabase.auth.signOut()
    if (error) throw new Error(error.message)
  },

  // -----------------------
  // GET CURRENT SESSION
  // -----------------------
  getSession: async () => {
    const { data: { session }, error } = await supabase.auth.getSession()
    if (error) throw new Error(error.message)
    return session
  }
}

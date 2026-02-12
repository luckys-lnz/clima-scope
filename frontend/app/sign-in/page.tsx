"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Cloud, AlertCircle, CheckCircle } from "lucide-react"
import { authService } from "@/lib/services/authService"
import type { LoginData } from "@/lib/models/auth"

export default function SignIn() {
  const router = useRouter()
  const [formData, setFormData] = useState<LoginData>({ email: "", password: "" })
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")
    setSuccess("")

    try {
      // Validate form
      if (!formData.email || !formData.password) throw new Error("Please fill in all fields")
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(formData.email)) throw new Error("Please enter a valid email address")

      // Call login via AuthService
      await authService.login(formData)

      setSuccess("Login successful! Redirecting...")
      setFormData({ email: "", password: "" })

      setTimeout(() => router.push("/dashboard"), 1000)
    } catch (err: any) {
      console.error("Login error:", err)
      setFormData(prev => ({ ...prev, password: "" }))

      if (err.message.includes("Invalid login")) {
        setError("Invalid email or password")
      } else if (err.message.includes("Email not confirmed")) {
        setError("Please confirm your email before logging in")
      } else {
        setError(err.message || "An error occurred. Please try again.")
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center px-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-6 hover:opacity-80 transition-opacity">
            <Cloud className="w-8 h-8 text-accent-blue" />
            <span className="text-xl font-bold">Weather Reports</span>
          </Link>
          <h1 className="text-3xl font-bold mb-2">Sign In</h1>
          <p className="text-muted-foreground">Access your weather reporting dashboard</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 bg-card border border-border/40 p-6 rounded-lg">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex gap-3 items-start">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-500">{error}</p>
            </div>
          )}

          {success && (
            <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 flex gap-3 items-start">
              <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-500">{success}</p>
            </div>
          )}

          {/* Email */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="you@example.com"
              className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
              required
              disabled={isLoading}
            />
          </div>

          {/* Password */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="••••••••"
              className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
              required
              disabled={isLoading}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2 bg-accent-blue text-white rounded-lg font-medium hover:bg-accent-blue/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Signing in...
              </span>
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="space-y-4 mt-6 text-center">
          <p className="text-sm text-muted-foreground">
            Don't have an account?{" "}
            <Link href="/sign-up" className="text-accent-blue hover:underline font-medium">
              Sign up
            </Link>
          </p>
          <Link href="/forgot-password" className="text-sm text-muted-foreground hover:text-accent-blue transition-colors">
            Forgot your password?
          </Link>
        </div>
      </div>
    </div>
  )
}

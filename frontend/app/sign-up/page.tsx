"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Cloud, AlertCircle, CheckCircle } from "lucide-react"
import { authService } from "../services/authService"
import type { SignUpData } from "../models/auth"

export default function SignUp() {
  const router = useRouter()
  const [formData, setFormData] = useState<SignUpData & { confirmPassword: string }>({
    full_name: "",
    email: "",
    password: "",
    confirmPassword: "",
    organization: "",
    county: "",
    phone: "",
  })
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const validateForm = (): string | null => {
    // Required fields
    if (!formData.full_name || !formData.email || !formData.password || !formData.confirmPassword || !formData.organization) {
      return "Please fill in all required fields"
    }

    // Email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) {
      return "Please enter a valid email address"
    }

    // Password length
    if (formData.password.length < 8) {
      return "Password must be at least 8 characters"
    }

    // Password strength
    const hasUpperCase = /[A-Z]/.test(formData.password)
    const hasLowerCase = /[a-z]/.test(formData.password)
    const hasNumber = /\d/.test(formData.password)
    if (!hasUpperCase || !hasLowerCase || !hasNumber) {
      return "Password must contain at least one uppercase letter, one lowercase letter, and one number"
    }

    // Password match
    if (formData.password !== formData.confirmPassword) {
      return "Passwords do not match"
    }

    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSuccess("")

    const validationError = validateForm()
    if (validationError) {
      setError(validationError)
      return
    }

    setIsLoading(true)

    try {
      // Use AuthService for signup
      await authService.signup({
        full_name: formData.full_name,
        email: formData.email,
        password: formData.password,
        organization: formData.organization,
        county: formData.county || undefined,
        phone: formData.phone || undefined,
      })

      setSuccess(
        "Account created! Please check your email to confirm your account. The confirmation link expires in 24 hours."
      )

      setFormData({
        full_name: "",
        email: "",
        password: "",
        confirmPassword: "",
        organization: "",
        county: "",
        phone: "",
      })

      // Redirect to login after a short delay
      setTimeout(() => router.push("/sign-in"), 2000)
    } catch (err: any) {
      const msg = err.message.toLowerCase()
      if (msg.includes("already registered") || msg.includes("already exists")) {
        setError("This email is already registered. Please sign in instead.")
      } else if (msg.includes("weak") || msg.includes("password")) {
        setError("Password does not meet security requirements. Please use a stronger password.")
      } else if (msg.includes("rate limit") || msg.includes("too many")) {
        setError("Too many attempts. Please wait a few minutes and try again.")
      } else if (msg.includes("network") || msg.includes("fetch")) {
        setError("Network error. Please check your connection and try again.")
      } else {
        setError(err.message || "An error occurred during registration. Please try again.")
      }
    } finally {
      setIsLoading(false)
    }
  }

  const kenyanCounties = [
    "Mombasa","Kwale","Kilifi","Tana River","Lamu","Taita Taveta","Garissa",
    "Wajir","Mandera","Marsabit","Isiolo","Meru","Tharaka Nithi","Embu",
    "Kitui","Machakos","Makueni","Nyandarua","Nyeri","Kirinyaga","Murang'a",
    "Kiambu","Turkana","West Pokot","Samburu","Trans Nzoia","Uasin Gishu",
    "Elgeyo Marakwet","Nandi","Baringo","Laikipia","Nakuru","Narok","Kajiado",
    "Kericho","Bomet","Kakamega","Vihiga","Bungoma","Busia","Siaya",
    "Kisumu","Homa Bay","Migori","Kisii","Nyamira","Nairobi"
  ].sort()

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center px-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-6 hover:opacity-80 transition-opacity">
            <Cloud className="w-8 h-8 text-accent-blue" />
            <span className="text-xl font-bold">Weather Reports</span>
          </Link>
          <h1 className="text-3xl font-bold mb-2">Create Account</h1>
          <p className="text-muted-foreground">Join Kenya's automated weather reporting system</p>
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
              <div>
                <p className="text-sm text-green-500 font-medium">{success}</p>
                <p className="text-xs text-green-600 mt-1">Redirecting to login in a few seconds...</p>
              </div>
            </div>
          )}

          {/* Full Name */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Full Name <span className="text-red-500">*</span></label>
            <input type="text" name="full_name" value={formData.full_name} onChange={handleChange}
              placeholder="John Doe" className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
              required disabled={isLoading} />
          </div>

          {/* Email */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Email <span className="text-red-500">*</span></label>
            <input type="email" name="email" value={formData.email} onChange={handleChange}
              placeholder="you@example.com" className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
              required disabled={isLoading} />
          </div>

          {/* Password */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Password <span className="text-red-500">*</span></label>
            <input type="password" name="password" value={formData.password} onChange={handleChange}
              placeholder="••••••••" className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
              required minLength={8} disabled={isLoading} />
            <p className="text-xs text-muted-foreground">At least 8 characters with uppercase, lowercase, and numbers</p>
          </div>

          {/* Confirm Password */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Confirm Password <span className="text-red-500">*</span></label>
            <input type="password" name="confirmPassword" value={formData.confirmPassword} onChange={handleChange}
              placeholder="••••••••" className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
              required minLength={8} disabled={isLoading} />
          </div>

          {/* Organization */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Organization <span className="text-red-500">*</span></label>
            <input type="text" name="organization" value={formData.organization} onChange={handleChange}
              placeholder="Your organization" className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
              required disabled={isLoading} />
          </div>

          {/* County */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">County</label>
            <select name="county" value={formData.county} onChange={handleChange}
              className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
              disabled={isLoading}>
              <option value="">Select a county (optional)</option>
              {kenyanCounties.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          {/* Phone */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">Phone</label>
            <input type="tel" name="phone" value={formData.phone} onChange={handleChange}
              placeholder="+254 712 345 678 (optional)"
              className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
              disabled={isLoading} />
          </div>

          <button type="submit" disabled={isLoading}
            className="w-full py-2 bg-accent-blue text-white rounded-lg font-medium hover:bg-accent-blue/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {isLoading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <p className="text-center text-sm text-muted-foreground mt-6">
          Already have an account?{" "}
          <Link href="/sign-in" className="text-accent-blue hover:underline font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}

"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { AlertCircle, CheckCircle, ArrowLeft } from "lucide-react"
import { authService } from "@/lib/services/authService"
import type { User } from "@/lib/models/auth"

type ProfileForm = {
  title: string
  full_name: string
  job_title: string
  county: string
  phone: string
  personal_email: string
  signoff_email: string
  station_name: string
  station_address: string
}

const emptyForm: ProfileForm = {
  title: "",
  full_name: "",
  job_title: "",
  county: "",
  phone: "",
  personal_email: "",
  signoff_email: "",
  station_name: "",
  station_address: "",
}

export default function ProfilePage() {
  const router = useRouter()
  const [formData, setFormData] = useState<ProfileForm>(emptyForm)
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  useEffect(() => {
    const loadProfile = async () => {
      setIsLoading(true)
      setError("")

      try {
        const session = await authService.getSession()

        if (!session) {
          router.replace("/sign-in")
          return
        }

        const user = await authService.getCurrentUser(session.access_token)

        setFormData({
          title: user.title || user.prefix || "",
          full_name: user.full_name || "",
          job_title: user.job_title || "",
          county: user.county || "",
          phone: user.phone || "",
          personal_email: user.email || "",
          signoff_email: user.signoff_email || "",
          station_name: user.station_name || "",
          station_address: user.station_address || "",
        })
      } catch (err: any) {
        setError(err.message || "Failed to load profile")
      } finally {
        setIsLoading(false)
      }
    }

    loadProfile()
  }, [router])

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    setError("")
    setSuccess("")
    setIsSaving(true)

    try {
      const token = await authService.getValidAccessToken()

      const updates: Partial<User> = {
        prefix: formData.title || undefined,
        title: formData.title || undefined,
        full_name: formData.full_name || undefined,
        job_title: formData.job_title || undefined,
        county: formData.county || undefined,
        phone: formData.phone || undefined,
        email: formData.personal_email || undefined,
        signoff_email: formData.signoff_email || undefined,
        station_name: formData.station_name || undefined,
        station_address: formData.station_address || undefined,
      }

      await authService.updateProfile(token, updates)

      setSuccess("Profile updated successfully.")
    } catch (err: any) {
      setError(err.message || "Failed to update profile")
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col items-center px-4 py-8">
      <div className="w-full max-w-2xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold">Update Profile</h1>
            <p className="text-muted-foreground">
              Manage sign-off details used in weekly forecast PDFs.
            </p>
          </div>

          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to dashboard
          </Link>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-6 bg-card border border-border/40 p-6 rounded-lg"
        >
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex gap-3 items-start">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-500">{error}</p>
            </div>
          )}

          {success && (
            <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 flex gap-3 items-start">
              <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-600">{success}</p>
            </div>
          )}

          {/* Prefix */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">
              Title <span className="text-red-500">*</span>
            </label>

            <select
              name="title"
              value={formData.title}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
              disabled={isLoading || isSaving}
            >
              <option value="">Select title</option>
              <option value="Mr">Mr</option>
              <option value="Mrs">Mrs</option>
              <option value="Ms">Ms</option>
              <option value="Dr">Dr</option>
              <option value="Prof">Prof</option>
            </select>
          </div>

          {/* Full Name */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">
              Full Name <span className="text-red-500">*</span>
            </label>

            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              placeholder="Emmanuel Daiddoh"
              className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
              disabled={isLoading || isSaving}
            />
          </div>

          {/* Job Title */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">
              Job Title <span className="text-red-500">*</span>
            </label>

            <input
              type="text"
              name="job_title"
              value={formData.job_title}
              onChange={handleChange}
              placeholder="County Director of Meteorological Services, Kilifi County"
              className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
              disabled={isLoading || isSaving}
            />
          </div>

          {/* Phone & County */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="block text-sm font-medium">
                Phone <span className="text-red-500">*</span>
              </label>

              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="0716157768"
                className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
                disabled={isLoading || isSaving}
              />
            </div>

            <div className="space-y-2">
            <label className="block text-sm font-medium">
              County <span className="text-red-500">*</span>
            </label>

              <input
                type="text"
                name="county"
                value={formData.county}
                onChange={handleChange}
                placeholder="Kilifi"
                className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
                disabled={isLoading || isSaving}
              />
            </div>
          </div>

          {/* Personal Email & Work Email */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="block text-sm font-medium">
                Personal Email <span className="text-red-500">*</span>
              </label>

              <input
                type="email"
                name="personal_email"
                value={formData.personal_email}
                onChange={handleChange}
                placeholder="emmanueldaiddoh@gmail.com"
                className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
                disabled={isLoading || isSaving}
              />
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium">
                Work Email <span className="text-red-500">*</span>
              </label>

              <input
                type="email"
                name="signoff_email"
                value={formData.signoff_email}
                onChange={handleChange}
                placeholder="cdmkilifi@meteo.go.ke"
                className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
                disabled={isLoading || isSaving}
              />
            </div>
          </div>

          {/* Station Name */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">
              Station Name <span className="text-red-500">*</span>
            </label>

            <input
              type="text"
              name="station_name"
              value={formData.station_name}
              onChange={handleChange}
              placeholder="Mtwapa Agrometeorological Station"
              className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
              disabled={isLoading || isSaving}
            />
          </div>

          {/* Station Address */}
          <div className="space-y-2">
            <label className="block text-sm font-medium">
              Station Address <span className="text-red-500">*</span>
            </label>

            <input
              type="text"
              name="station_address"
              value={formData.station_address}
              onChange={handleChange}
              placeholder="P.O. BOX 113-80109, Mtwapa"
              className="w-full px-3 py-2 border border-border/40 rounded-lg bg-background focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue/50"
              disabled={isLoading || isSaving}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading || isSaving}
            className="w-full py-2 bg-accent-blue text-white rounded-lg font-medium hover:bg-accent-blue/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSaving ? "Saving..." : "Save Profile"}
          </button>
        </form>
      </div>
    </div>
  )
}

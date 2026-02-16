"use client"

import { ChevronLeft, AlertCircle } from "lucide-react"
import { TextInput } from "@/components/text-input"
import { SelectInput } from "@/components/select-input"
import { useState, useEffect } from "react"
import { SettingsService } from "@/lib/services/settingService"
import { useAuth } from "@/hooks/useAuth"

interface Template {
  id: string
  file_name: string
  file_type: string
  upload_date: string
  is_default?: boolean
}

interface SystemConfigurationProps {
  onBack: () => void
}

const STORAGE_KEY = "system_settings_cache"

export function SystemConfiguration({ onBack }: SystemConfigurationProps) {
  const { token, isLoading: authLoading } = useAuth()

  // Load from cache immediately
  const getCachedData = () => {
    if (typeof window === "undefined") return null
    try {
      const cached = sessionStorage.getItem(STORAGE_KEY)
      return cached ? JSON.parse(cached) : null
    } catch {
      return null
    }
  }

  const cached = getCachedData()

  const [loading, setLoading] = useState(!cached)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [shapefilePath, setShapefilePath] = useState(cached?.shapefilePath || "")
  const [templates, setTemplates] = useState<Template[]>(cached?.templates || [])
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(cached?.selectedTemplateId || null)

  // Fetch only if no cache
  useEffect(() => {
    if (cached || authLoading || !token) return

    const fetchSettings = async () => {
      try {
        const data = await SettingsService.getSettings(token)

        const settingsData = {
          shapefilePath: data.shapefile_path || "",
          templates: data.templates || [],
          selectedTemplateId: data.user_settings?.pdf_template_id || null,
        }

        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(settingsData))

        setShapefilePath(settingsData.shapefilePath)
        setTemplates(settingsData.templates)
        setSelectedTemplateId(settingsData.selectedTemplateId)
        setLoading(false)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load settings")
        setLoading(false)
      }
    }

    fetchSettings()
  }, [token, authLoading, cached])

  const handleTemplateChange = async (templateId: string) => {
    if (!token) return

    try {
      setSaving(true)
      await SettingsService.updateTemplate(token, templateId)

      setSelectedTemplateId(templateId)

      const updatedCache = { shapefilePath, templates, selectedTemplateId: templateId }
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(updatedCache))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings")
    } finally {
      setSaving(false)
    }
  }

  const templateOptions = templates.map((t) => ({
    value: t.id,
    label: t.is_default ? `${t.file_name} (Default)` : t.file_name,
  }))

  if (loading || authLoading) {
    return (
      <div className="p-8 max-w-3xl">
        <div className="bg-card rounded-xl border border-border p-10 text-center">
          <div className="animate-spin w-6 h-6 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-muted-foreground">Loading system settings...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 max-w-3xl">
        <div className="bg-card rounded-xl border border-destructive/30 p-8 text-center">
          <AlertCircle className="w-8 h-8 text-destructive mx-auto mb-4" />
          <p className="text-destructive font-medium mb-2">Unable to Load Settings</p>
          <p className="text-sm text-muted-foreground mb-6">{error}</p>
          <button
            onClick={() => {
              setError(null)
              sessionStorage.removeItem(STORAGE_KEY)
              window.location.reload()
            }}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-8 max-w-3xl">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-primary hover:text-primary/80 transition-colors"
      >
        <ChevronLeft className="w-4 h-4" />
        <span className="text-sm font-medium">Back to Dashboard</span>
      </button>

      <div>
        <h1 className="text-2xl font-bold">System Settings</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Configure core system resources used for geographic analysis and report generation.
        </p>
      </div>

      <div className="bg-card rounded-xl border border-border p-6 space-y-4">
        <div>
          <h2 className="text-lg font-semibold">Geographic Data Configuration</h2>
          <p className="text-sm text-muted-foreground">
            This shapefile defines the Kenya administrative boundaries used in spatial analysis.
          </p>
        </div>

        <TextInput label="Default Boundary Shapefile" value={shapefilePath} readOnly />
      </div>

      <div className="bg-card rounded-xl border border-border p-6 space-y-4">
        <div>
          <h2 className="text-lg font-semibold">Report Generation Settings</h2>
          <p className="text-sm text-muted-foreground">
            Select the PDF template used when generating analytical reports.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Default Report Template
          </label>
          <SelectInput
            value={selectedTemplateId ?? ""}
            onChange={handleTemplateChange}
            options={templateOptions}
          />
        </div>

        {saving && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <div className="animate-spin w-3 h-3 border-2 border-primary border-t-transparent rounded-full" />
            Saving changes...
          </div>
        )}
      </div>

      <div>
        <button
          disabled
          onClick={() => handleTemplateChange(selectedTemplateId || "")}
          className="w-full bg-primary hover:bg-primary/90 text-primary-foreground py-3 rounded-lg font-medium disabled:opacity-50 transition-colors"
        >
          {saving ? "Saving..." : "Save Configuration"}
        </button>
      </div>
    </div>
  )
}
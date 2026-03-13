"use client"

import { ChevronLeft, AlertCircle } from "lucide-react"
import { TextInput } from "@/components/text-input"
import { SelectInput } from "@/components/select-input"
import { useState, useEffect } from "react"
import { SettingsService } from "@/lib/services/settingService"
import { useAuth } from "@/hooks/useAuth"
import type { MapPreviewResponse, MapPreviewGeometry } from "@/lib/models/setting"

interface Template {
  id: string
  file_name: string
  file_type: string
  upload_date: string
  file_path?: string | null
  is_default?: boolean
}

interface SystemConfigurationProps {
  onBack: () => void
}

const STORAGE_KEY = "system_settings_cache"
const STORAGE_VERSION = 3

interface CachedSettings {
  version: number
  shapefilePath: string
  templates: Template[]
  selectedTemplateId: string | null
  showConstituencies: boolean
  showWards: boolean
  showLabels: boolean
  labelFontSize: number
}

function clampFontSize(value: number): number {
  if (Number.isNaN(value)) return 12
  return Math.max(6, Math.min(48, Math.round(value)))
}

const PREVIEW_WIDTH = 340
const PREVIEW_HEIGHT = 220
const PREVIEW_PADDING = 14

type Projector = (point: [number, number]) => [number, number]

function createProjector(bbox: [number, number, number, number]): Projector {
  const [minX, minY, maxX, maxY] = bbox
  const width = Math.max(maxX - minX, 1e-6)
  const height = Math.max(maxY - minY, 1e-6)
  const scale = Math.min(
    (PREVIEW_WIDTH - PREVIEW_PADDING * 2) / width,
    (PREVIEW_HEIGHT - PREVIEW_PADDING * 2) / height
  )
  const offsetX = (PREVIEW_WIDTH - width * scale) / 2
  const offsetY = (PREVIEW_HEIGHT - height * scale) / 2

  return ([lon, lat]) => [
    (lon - minX) * scale + offsetX,
    (maxY - lat) * scale + offsetY,
  ]
}

function lineToPath(coords: [number, number][], project: Projector): string {
  if (!coords || coords.length === 0) return ""
  return coords
    .map((point, index) => {
      const [x, y] = project(point)
      return `${index === 0 ? "M" : "L"}${x.toFixed(2)} ${y.toFixed(2)}`
    })
    .join(" ")
}

function polygonToPath(rings: [number, number][][], project: Projector): string {
  if (!rings || rings.length === 0) return ""
  return rings
    .map((ring) => `${lineToPath(ring, project)} Z`)
    .filter(Boolean)
    .join(" ")
}

function geometryToPath(geometry: MapPreviewGeometry | null | undefined, project: Projector): string {
  if (!geometry) return ""
  switch (geometry.type) {
    case "Polygon":
      return polygonToPath(geometry.coordinates as [number, number][][], project)
    case "MultiPolygon":
      return (geometry.coordinates as [number, number][][][])
        .map((polygon) => polygonToPath(polygon, project))
        .filter(Boolean)
        .join(" ")
    case "LineString":
      return lineToPath(geometry.coordinates as [number, number][], project)
    case "MultiLineString":
      return (geometry.coordinates as [number, number][][])
        .map((line) => lineToPath(line, project))
        .filter(Boolean)
        .join(" ")
    case "GeometryCollection":
      return (geometry.geometries as MapPreviewGeometry[] | undefined)
        ?.map((geom) => geometryToPath(geom, project))
        .filter(Boolean)
        .join(" ") || ""
    default:
      return ""
  }
}

function MapSettingsPreview({
  showConstituencies,
  showWards,
  showLabels,
  labelFontSize,
  preview,
  previewLoading,
  previewError,
}: {
  showConstituencies: boolean
  showWards: boolean
  showLabels: boolean
  labelFontSize: number
  preview: MapPreviewResponse | null
  previewLoading: boolean
  previewError: string | null
}) {
  const hasPreview = Boolean(
    preview?.county_geometry &&
      Array.isArray(preview?.bbox) &&
      preview?.bbox.length === 4
  )
  const projector = hasPreview ? createProjector(preview!.bbox) : null
  const countyPath = hasPreview && projector ? geometryToPath(preview!.county_geometry, projector) : ""
  const constituencyPath =
    hasPreview && projector && showConstituencies
      ? geometryToPath(preview!.constituency_boundaries || null, projector)
      : ""
  const wardPath =
    hasPreview && projector && showWards
      ? geometryToPath(preview!.ward_boundaries || null, projector)
      : ""
  const safeFontSize = clampFontSize(labelFontSize)
  const labels = hasPreview && showLabels ? preview?.labels || [] : []
  const previewTitle = preview?.county
    ? `Live Map Preview (${preview.county} County)`
    : "Live Map Preview (no weather data)"

  return (
    <div className="rounded-lg border border-border bg-muted/20 p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-muted-foreground">{previewTitle}</p>
        {previewLoading && <span className="text-xs text-muted-foreground">Loading...</span>}
      </div>
      {previewError && (
        <p className="text-xs text-amber-600 mb-2">{previewError}</p>
      )}
      <svg
        viewBox={`0 0 ${PREVIEW_WIDTH} ${PREVIEW_HEIGHT}`}
        className="w-full h-auto rounded-md bg-slate-50 border border-slate-200"
      >
        <rect x="0" y="0" width={PREVIEW_WIDTH} height={PREVIEW_HEIGHT} fill="#f8fafc" />

        {hasPreview ? (
          <>
            <path
              d={countyPath}
              fill="#e2e8f0"
              stroke="#0f172a"
              strokeWidth="2.2"
              fillRule="evenodd"
            />

            {constituencyPath && (
              <path
                d={constituencyPath}
                fill="none"
                stroke="#1e293b"
                strokeWidth="1.2"
                opacity="0.9"
              />
            )}

            {wardPath && (
              <path
                d={wardPath}
                fill="none"
                stroke="#2563eb"
                strokeWidth="0.9"
                strokeDasharray="3 2"
                opacity="0.8"
              />
            )}

            {showLabels && labels.length > 0 && (
              <g fill="#0f172a" textAnchor="middle" style={{ fontSize: `${safeFontSize}px` }}>
                {labels.slice(0, 35).map((label, idx) => {
                  if (!projector) return null
                  const [x, y] = projector([label.lon, label.lat])
                  return (
                    <text key={`${label.name}-${idx}`} x={x} y={y} dominantBaseline="middle">
                      {label.name}
                    </text>
                  )
                })}
              </g>
            )}
          </>
        ) : (
          <>
            <path
              d="M30,120 L65,70 L120,45 L185,40 L245,62 L305,95 L290,160 L240,188 L165,197 L95,182 L48,152 Z"
              fill="#e2e8f0"
              stroke="#0f172a"
              strokeWidth="2.2"
            />

            {showConstituencies && (
              <g stroke="#1e293b" strokeWidth="1.4" opacity="0.9">
                <path d="M84,66 L88,176" />
                <path d="M136,52 L140,193" />
                <path d="M188,46 L192,198" />
                <path d="M238,58 L246,184" />
              </g>
            )}

            {showWards && (
              <g stroke="#2563eb" strokeWidth="1" strokeDasharray="3 2" opacity="0.8">
                <path d="M52,102 L286,104" />
                <path d="M48,132 L292,136" />
                <path d="M70,82 L272,85" />
                <path d="M116,58 L120,184" />
                <path d="M166,46 L168,198" />
                <path d="M218,54 L224,190" />
              </g>
            )}

            {showLabels && (
              <g fill="#0f172a" textAnchor="middle" style={{ fontSize: `${safeFontSize}px` }}>
                <text x="95" y="94">Ward A</text>
                <text x="170" y="96">Ward B</text>
                <text x="246" y="100">Ward C</text>
                <text x="116" y="152">Ward D</text>
                <text x="203" y="160">Ward E</text>
              </g>
            )}
          </>
        )}
      </svg>
    </div>
  )
}

export function SystemConfiguration({ onBack }: SystemConfigurationProps) {
  const { access_token: token, isLoading: authLoading, user } = useAuth()

  const getCachedData = (): CachedSettings | null => {
    if (typeof window === "undefined") return null
    try {
      const cached = sessionStorage.getItem(STORAGE_KEY)
      const parsed = cached ? JSON.parse(cached) : null
      if (!parsed || parsed.version !== STORAGE_VERSION) return null
      return parsed as CachedSettings
    } catch {
      return null
    }
  }

  const cached = getCachedData()

  const [loading, setLoading] = useState(!cached)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)

  const [shapefilePath, setShapefilePath] = useState(cached?.shapefilePath || "")
  const [templates, setTemplates] = useState<Template[]>(cached?.templates || [])
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(cached?.selectedTemplateId || null)
  const [showConstituencies, setShowConstituencies] = useState(cached?.showConstituencies ?? true)
  const [showWards, setShowWards] = useState(cached?.showWards ?? true)
  const [showLabels, setShowLabels] = useState(cached?.showLabels ?? true)
  const [labelFontSize, setLabelFontSize] = useState(cached?.labelFontSize ?? 12)
  const [previewData, setPreviewData] = useState<MapPreviewResponse | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !token) {
      setLoading(false)
      setError("Session expired. Please sign in again.")
      return
    }

    if (authLoading || !token) return

    const fetchSettings = async () => {
      try {
        if (!cached) setLoading(true)
        const data = await SettingsService.getSettings(token)

        const settingsData: CachedSettings = {
          version: STORAGE_VERSION,
          shapefilePath: data.shapefile_path || "",
          templates: data.templates || [],
          selectedTemplateId: data.user_settings?.pdf_template_id || null,
          showConstituencies: data.user_settings?.show_constituencies ?? true,
          showWards: data.user_settings?.show_wards ?? true,
          showLabels: data.user_settings?.show_labels ?? true,
          labelFontSize: clampFontSize(data.user_settings?.label_font_size ?? 12),
        }

        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(settingsData))

        setShapefilePath(settingsData.shapefilePath)
        setTemplates(settingsData.templates)
        setSelectedTemplateId(settingsData.selectedTemplateId)
        setShowConstituencies(settingsData.showConstituencies)
        setShowWards(settingsData.showWards)
        setShowLabels(settingsData.showLabels)
        setLabelFontSize(settingsData.labelFontSize)
        if (!cached) setLoading(false)
      } catch (err) {
        if (!cached) {
          setError(err instanceof Error ? err.message : "Failed to load settings")
          setLoading(false)
        }
      }
    }

    if (cached) {
      setLoading(false)
    }

    fetchSettings()
  }, [token, authLoading])

  useEffect(() => {
    if (authLoading) return
    if (!token) {
      setPreviewData(null)
      return
    }
    const county = user?.county
    if (!county) {
      setPreviewError("Set your county in profile to see a map preview.")
      setPreviewData(null)
      return
    }

    let active = true
    setPreviewLoading(true)
    setPreviewError(null)

    SettingsService.getCountyPreview(token, county)
      .then((data) => {
        if (!active) return
        setPreviewData(data)
      })
      .catch((err) => {
        if (!active) return
        setPreviewError(err instanceof Error ? err.message : "Failed to load map preview")
      })
      .finally(() => {
        if (!active) return
        setPreviewLoading(false)
      })

    return () => {
      active = false
    }
  }, [token, authLoading, user?.county])

  const handleSaveConfiguration = async () => {
    if (!token) return

    try {
      setSaving(true)
      setSaveMessage(null)
      setError(null)

      const safeFontSize = clampFontSize(labelFontSize)
      await SettingsService.updateSettings(token, {
        pdf_template_id: selectedTemplateId,
        show_constituencies: showConstituencies,
        show_wards: showWards,
        show_labels: showLabels,
        label_font_size: safeFontSize,
      })

      setLabelFontSize(safeFontSize)
      const updatedCache: CachedSettings = {
        version: STORAGE_VERSION,
        shapefilePath,
        templates,
        selectedTemplateId,
        showConstituencies,
        showWards,
        showLabels,
        labelFontSize: safeFontSize,
      }
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(updatedCache))
      setSaveMessage("Settings saved")
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
          Configure core resources and county map display options used in report generation.
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
            onChange={(value) => setSelectedTemplateId(value || null)}
            options={templateOptions}
          />
        </div>
      </div>

      <div className="bg-card rounded-xl border border-border p-6 space-y-4">
        <div>
          <h2 className="text-lg font-semibold">County Map Settings</h2>
          <p className="text-sm text-muted-foreground">
            These options control boundary overlays and labels for generated county-level maps.
          </p>
        </div>

        <label className="flex items-center gap-3 text-sm text-foreground">
          <input
            type="checkbox"
            checked={showConstituencies}
            onChange={(e) => setShowConstituencies(e.target.checked)}
            className="h-4 w-4 rounded border-border"
          />
          Show Constituencies
        </label>

        <label className="flex items-center gap-3 text-sm text-foreground">
          <input
            type="checkbox"
            checked={showWards}
            onChange={(e) => setShowWards(e.target.checked)}
            className="h-4 w-4 rounded border-border"
          />
          Show Wards
        </label>

        <label className="flex items-center gap-3 text-sm text-foreground">
          <input
            type="checkbox"
            checked={showLabels}
            onChange={(e) => setShowLabels(e.target.checked)}
            className="h-4 w-4 rounded border-border"
          />
          Show Labels
        </label>

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">Label Font Size</label>
          <input
            type="number"
            min={6}
            max={48}
            value={labelFontSize}
            onChange={(e) => setLabelFontSize(clampFontSize(Number(e.target.value)))}
            className="w-40 px-4 py-2 rounded-lg border border-border bg-card text-card-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <MapSettingsPreview
          showConstituencies={showConstituencies}
          showWards={showWards}
          showLabels={showLabels}
          labelFontSize={labelFontSize}
          preview={previewData}
          previewLoading={previewLoading}
          previewError={previewError}
        />
      </div>

      <div className="space-y-2">
        <button
          disabled={saving}
          onClick={handleSaveConfiguration}
          className="w-full bg-primary hover:bg-primary/90 text-primary-foreground py-3 rounded-lg font-medium disabled:opacity-50 transition-colors"
        >
          {saving ? "Saving..." : "Save Configuration"}
        </button>

        {saveMessage && <p className="text-xs text-emerald-600">{saveMessage}</p>}
      </div>
    </div>
  )
}

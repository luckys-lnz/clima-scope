"use client"

import { useEffect, useState } from "react"
import { ChevronLeft, Download, RefreshCw, Eye, TrendingUp, TrendingDown } from "lucide-react"
import { MapPlaceholder } from "@/components/map-placeholder"
import { useAuth } from "@/hooks/useAuth"
import { ReportService } from "@/lib/services/reportService"
import type { ReportDetailResponse } from "@/lib/models/report"

interface CountyDetailProps {
  county: string
  reportId?: string
  onBack: () => void
}

const COUNTY_DETAIL_CACHE_PREFIX = "county_detail_cache_v2"

export function CountyDetail({ county, reportId, onBack }: CountyDetailProps) {
  const { access_token: token, isLoading: authLoading } = useAuth()
  const [detail, setDetail] = useState<ReportDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState("")

  useEffect(() => {
    if (authLoading) return

    const countyCacheKey = `${COUNTY_DETAIL_CACHE_PREFIX}:county:${String(county).toLowerCase()}`
    const reportCacheKey = reportId ? `${COUNTY_DETAIL_CACHE_PREFIX}:report:${reportId}` : null
    const readCache = (key: string): ReportDetailResponse | null => {
      if (typeof window === "undefined") return null
      try {
        const raw = sessionStorage.getItem(key)
        return raw ? (JSON.parse(raw) as ReportDetailResponse) : null
      } catch {
        return null
      }
    }
    const writeCache = (key: string, value: ReportDetailResponse) => {
      if (typeof window === "undefined") return
      try {
        sessionStorage.setItem(key, JSON.stringify(value))
      } catch {
        // Ignore cache write failures.
      }
    }

    const cached = reportCacheKey ? readCache(reportCacheKey) : readCache(countyCacheKey)
    if (cached) {
      setDetail(cached)
      setLoading(false)
      setErrorMessage("")
      return
    }

    let cancelled = false
    const load = async () => {
      try {
        setLoading(true)
        setErrorMessage("")

        let resolvedReportId = reportId
        if (!resolvedReportId) {
          const reports = await ReportService.getReports(token || "")
          const countyMatch = reports.find(
            (r) => String(r.county).toLowerCase() === String(county).toLowerCase()
          )
          resolvedReportId = countyMatch?.id || reports[0]?.id
        }

        if (!resolvedReportId) {
          throw new Error("No generated report found")
        }

        const payload = await ReportService.getReportDetail(token || "", resolvedReportId)
        if (!cancelled) {
          setDetail(payload)
          writeCache(`${COUNTY_DETAIL_CACHE_PREFIX}:report:${resolvedReportId}`, payload)
          writeCache(countyCacheKey, payload)
        }
      } catch (e: any) {
        if (!cancelled) setErrorMessage(e?.message || "Failed to load report detail")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [token, authLoading, reportId, county])

  const vars = detail?.observation_summary?.variables || {}
  const rainfallTotal = vars.rainfall?.sum ?? detail?.forecast_summary?.rainfall_sum
  const tmaxMean = vars.tmax?.mean
  const tminMean = vars.tmin?.mean
  const meanTemp =
    detail?.forecast_summary?.mean_temperature ??
    (typeof tmaxMean === "number" && typeof tminMean === "number"
      ? (tmaxMean + tminMean) / 2
      : undefined)
  const maxWind = detail?.forecast_summary?.max_wind_speed ?? vars.wind?.max
  const wk = detail?.observation?.report_week
  const yr = detail?.observation?.report_year
  const periodStart = detail?.observation?.report_start_at || "N/A"
  const periodEnd = detail?.observation?.report_end_at || "N/A"
  const maps = detail?.maps || []
  const reportMeta = detail?.report
  const aiSummary = detail?.ai_narration?.weekly_summary_text?.trim()
  const aiSummarySource = detail?.ai_narration?.source

  const formatDate = (value?: string) => {
    if (!value) return "N/A"
    const dt = new Date(value)
    return Number.isNaN(dt.getTime()) ? value : dt.toLocaleDateString()
  }

  const mapColorFromVariable = (variable: string): "rainfall" | "temperature" | "wind" => {
    const v = variable.toLowerCase()
    if (v.includes("rain")) return "rainfall"
    if (v.includes("wind")) return "wind"
    return "temperature"
  }

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-primary hover:text-primary/80 transition-colors mb-4"
        >
          <ChevronLeft className="w-4 h-4" />
          <span className="text-sm">Back to Archive</span>
        </button>
        <div className="bg-card rounded-lg border border-border p-4 text-sm text-muted-foreground">
          Loading report detail...
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-primary hover:text-primary/80 transition-colors mb-4"
      >
        <ChevronLeft className="w-4 h-4" />
        <span className="text-sm">Back to Archive</span>
      </button>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card rounded-lg border border-border p-6">
          <div className="flex items-start justify-between mb-2">
            <h3 className="text-sm text-muted-foreground font-medium">Total Rainfall</h3>
            <TrendingUp className="w-4 h-4 text-weather-rainfall" />
          </div>
          <p className="text-3xl font-bold text-card-foreground">
            {typeof rainfallTotal === "number" ? `${rainfallTotal.toFixed(1)} mm` : "N/A"}
          </p>
          <p className="text-xs text-muted-foreground mt-2">Station aggregate for selected period</p>
        </div>

        <div className="bg-card rounded-lg border border-border p-6">
          <div className="flex items-start justify-between mb-2">
            <h3 className="text-sm text-muted-foreground font-medium">Mean Temperature</h3>
            <TrendingDown className="w-4 h-4 text-weather-temperature" />
          </div>
          <p className="text-3xl font-bold text-card-foreground">
            {typeof meanTemp === "number" ? `${meanTemp.toFixed(1)}°C` : "N/A"}
          </p>
          <p className="text-xs text-muted-foreground mt-2">Average across forecast days</p>
        </div>

        <div className="bg-card rounded-lg border border-border p-6">
          <div className="flex items-start justify-between mb-2">
            <h3 className="text-sm text-muted-foreground font-medium">Max Wind Speed</h3>
            <TrendingUp className="w-4 h-4 text-weather-wind" />
          </div>
          <p className="text-3xl font-bold text-card-foreground">
            {typeof maxWind === "number" ? `${maxWind.toFixed(1)} km/h` : "N/A"}
          </p>
          <p className="text-xs text-muted-foreground mt-2">Maximum across forecast days</p>
        </div>
      </div>

      {/* Narrative Text */}
      <div className="bg-card rounded-lg border border-border p-6">
        <h2 className="font-bold text-lg text-card-foreground mb-4">Weekly Narrative Summary</h2>
        <div className="prose prose-invert max-w-none">
          {aiSummary ? (
            <p className="text-sm text-card-foreground leading-relaxed whitespace-pre-line">{aiSummary}</p>
          ) : (
            <p className="text-sm text-card-foreground leading-relaxed">
              {wk && yr ? `Week ${wk}, ${yr}` : "Current reporting week"} in {county} county
              ({formatDate(periodStart)} to {formatDate(periodEnd)}) indicates total rainfall of{" "}
              {typeof rainfallTotal === "number" ? `${rainfallTotal.toFixed(1)} mm` : "N/A"}, mean temperature of{" "}
              {typeof meanTemp === "number" ? `${meanTemp.toFixed(1)}°C` : "N/A"}, and peak wind of{" "}
              {typeof maxWind === "number" ? `${maxWind.toFixed(1)} km/h` : "N/A"}.
            </p>
          )}
          <p className="text-sm text-card-foreground leading-relaxed mt-3">
            Source: {aiSummarySource || "computed summary"}.
            Report status: {reportMeta?.status || "N/A"}. Generated on: {formatDate(reportMeta?.generated_at)}.
          </p>
        </div>
      </div>

      {/* Ward-Level Maps */}
      <div>
        <h2 className="font-bold text-lg text-card-foreground mb-4">Ward-Level Map Visualizations</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {maps.slice(0, 3).map((map) => (
            <div key={`${map.variable}-${map.created_at}`} className="bg-card rounded-lg border border-border overflow-hidden">
              <MapPlaceholder title={`${map.variable} map`} color={mapColorFromVariable(map.variable)} />
              <div className="p-4 flex justify-between items-center">
                <div className="text-xs text-muted-foreground capitalize">{map.variable}</div>
                <a
                  href={map.map_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-primary hover:text-primary/80 transition-colors text-xs font-medium"
                >
                  <Eye className="w-3 h-3" />
                  View
                </a>
              </div>
            </div>
          ))}
          {maps.length === 0 && (
            <>
              <div className="bg-card rounded-lg border border-border overflow-hidden">
                <MapPlaceholder title="Rainfall Distribution" color="rainfall" />
              </div>
              <div className="bg-card rounded-lg border border-border overflow-hidden">
                <MapPlaceholder title="Temperature Avg" color="temperature" />
              </div>
              <div className="bg-card rounded-lg border border-border overflow-hidden">
                <MapPlaceholder title="Wind Speed" color="wind" />
              </div>
            </>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={async () => {
            const resolvedReportId = reportId || detail?.report?.id
            if (!resolvedReportId) {
              setErrorMessage("No report selected for PDF download")
              return
            }
            try {
              setErrorMessage("")
              await ReportService.downloadReport(token || "", resolvedReportId)
            } catch (e: any) {
              setErrorMessage(e?.message || "Failed to download report PDF")
            }
          }}
          className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground py-2 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
        >
          <Download className="w-4 h-4" />
          Download PDF
        </button>
        <button className="flex-1 bg-card hover:bg-muted border border-border text-card-foreground py-2 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4" />
          Regenerate Report
        </button>
      </div>
      {errorMessage && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-sm text-red-600">
          {errorMessage}
        </div>
      )}
    </div>
  )
}

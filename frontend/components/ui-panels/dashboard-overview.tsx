"use client"

import { useEffect, useState } from "react"
import { BarChart3, CheckCircle, Circle, Database, Calendar } from "lucide-react"

import { DashboardOverviewData } from "@/lib/models/dashboard"
import { DashboardService } from "@/lib/services/dashboardService"
import { AlertCard } from "@/components/ui/alert-card"
import { InfoCard } from "@/components/ui/info-card"
import { ActionButton } from "@/components/ui/action-button"
import { SecondaryButton } from "@/components/ui/secondary-button"
import { UsageRow } from "@/components/ui/usage-row"
import { StatCard } from "@/components/stat-card"
import { formatRelativeDate } from "@/lib/utils/date"
import { useAuth } from "@/hooks/useAuth"
import { StatusPanel } from "@/components/ui/status-panel"

interface DashboardOverviewProps {
  onNavigate: (screen: string) => void
}

const DASHBOARD_CACHE_KEY = "dashboard_overview_cache_v1"
const REPORT_JOB_ACTIVE_KEY = "report_job_active"

export function DashboardOverview({ onNavigate }: DashboardOverviewProps) {
  const getCachedData = (): DashboardOverviewData | null => {
    if (typeof window === "undefined") return null
    try {
      const raw = sessionStorage.getItem(DASHBOARD_CACHE_KEY)
      return raw ? (JSON.parse(raw) as DashboardOverviewData) : null
    } catch {
      return null
    }
  }

  const { access_token: token, isLoading: authLoading } = useAuth()
  const [data, setData] = useState<DashboardOverviewData | null>(() => getCachedData())
  const [loading, setLoading] = useState(() => !getCachedData())
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (authLoading) return
    if (!token) {
      setError("Session expired. Please sign in again.")
      setLoading(false)
      return
    }

    let cancelled = false
    let pollHandle: ReturnType<typeof setInterval> | null = null

    async function fetchDashboard(isInitial = false) {
      try {
        // Only show blocking loader if we have no cached data.
        if (isInitial && !data) setLoading(true)

        const result = await DashboardService.getOverview(token)
        if (cancelled) return
        setData(result)
        sessionStorage.setItem(DASHBOARD_CACHE_KEY, JSON.stringify(result))
        setError(null)
      } catch (e: any) {
        if (cancelled) return
        if (!data) {
          setError(e.message || "Error")
        }
      } finally {
        if (isInitial && !data) setLoading(false)
      }
    }

    if (data) {
      setLoading(false)
    }

    fetchDashboard(true)

    const isJobActive = typeof window !== "undefined" &&
      sessionStorage.getItem(REPORT_JOB_ACTIVE_KEY) === "true"
    if (isJobActive) {
      // Poll only when a background report job is active.
      pollHandle = setInterval(() => {
        fetchDashboard(false)
      }, 5000)
    }

    return () => {
      cancelled = true
      if (pollHandle) clearInterval(pollHandle)
    }
  }, [token, authLoading])

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center p-6">
        <div className="w-full max-w-md rounded-lg border border-border/60 bg-card/95 p-6 shadow-2xl backdrop-blur">
          <StatusPanel
            icon={BarChart3}
            title="Loading dashboard"
            description="Fetching the latest metrics and activity."
          />
        </div>
      </div>
    )
  }
  if (error || !data) return <div className="p-6 text-red-500">{error || "No data"}</div>

  const { stats, workflow_step, workflow_progress: workflowProgress } = data
  if (typeof window !== "undefined") {
    const latestStatus = String(workflowProgress?.status || "").toLowerCase()
    if (workflow_step === "completed" || latestStatus === "error" || latestStatus === "failed") {
      sessionStorage.setItem(REPORT_JOB_ACTIVE_KEY, "false")
    }
  }
  const currentWindowText = `Week ${data.current_window.week}, ${data.current_window.year} (${data.current_window.start} to ${data.current_window.end})`

  const steps = [
    { key: "uploaded", label: "Historical Station Data" },
    { key: "aggregated", label: "Spatial Aggregation" },
    { key: "mapped", label: "Generate Map" },
    { key: "generated", label: "Generate Report" },
    { key: "completed", label: "Complete" },
  ] as const

  const activeIndex =
    workflow_step !== null
      ? steps.findIndex((s) => s.key === workflow_step)
      : -1

  const progressPercent =
    activeIndex >= 0 ? ((activeIndex + 1) / steps.length) * 100 : 0

  const lastGenRelative = stats.lastGeneration
    ? formatRelativeDate(stats.lastGeneration)
    : "None"

  return (
    <div className="p-6 space-y-6">
      {/* Alerts */}
      <div className="space-y-3">
        <AlertCard
          title="Observation Data Reminder"
          text="Make sure your observation data for your county is uploaded and complete for this week."
        />
        <InfoCard
          title="Template Upload Reminder"
          text="You can upload a custom report template. If none is uploaded, the default template will be used."
        />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Counties Processed"
          value={`${stats.countiesProcessed} / ${stats.totalCounties}`}
          icon={Database}
          status="neutral"
        />
        <StatCard
          label="Last Generation"
          value={lastGenRelative}
          icon={Calendar}
          status="neutral"
        />
        <StatCard
          label="All Reports Done"
          value={stats.allReportsDone.toString()}
          icon={CheckCircle}
          status="neutral"
        />
      </div>

      {/* Main */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-card border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">
            Report Generation Process
          </h2>
          <p className="text-sm text-muted-foreground mb-4">
            Tracking current reporting period: {currentWindowText}
          </p>
          {workflowProgress && (
            <div className="mb-4 rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm">
              <span className="font-medium capitalize">Latest: </span>
              <span>{workflowProgress.message}</span>
              <span
                className={`ml-2 rounded px-2 py-0.5 text-xs font-semibold ${
                  workflowProgress.status === "error"
                    ? "bg-red-100 text-red-700"
                    : workflowProgress.status === "success"
                      ? "bg-green-100 text-green-700"
                      : "bg-blue-100 text-blue-700"
                }`}
              >
                {workflowProgress.status}
              </span>
            </div>
          )}

          {/* Progress */}
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-2">
              <span>Progress</span>
              <span className="font-semibold">
                {activeIndex + 1} / {steps.length}
              </span>
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>

          {/* Steps */}
          <div className="space-y-3">
            {steps.map((step, i) => {
              const completed = i <= activeIndex
              return (
                <div key={step.key} className="flex items-center gap-3">
                  {completed ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <Circle className="w-5 h-5 text-gray-400" />
                  )}
                  <span
                    className={`font-medium ${
                      completed
                        ? "text-base md:text-lg font-semibold"
                        : "text-sm text-gray-400"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="font-semibold mb-4">Quick Actions</h3>
            <div className="space-y-2">
              <ActionButton onClick={() => onNavigate("generate")}>
                Generate Reports
              </ActionButton>
              <SecondaryButton onClick={() => onNavigate("archive")}>
                View Archive
              </SecondaryButton>
              <SecondaryButton onClick={() => onNavigate("logs")}>
                View Logs
              </SecondaryButton>
            </div>
          </div>

          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="font-semibold mb-4">App Usage</h3>
            <div className="space-y-3 text-sm">
              <UsageRow
                label="Reports Generated"
                value={stats.userReportsGenerated}
              />
              <UsageRow
                label="Last Activity"
                value={lastGenRelative}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

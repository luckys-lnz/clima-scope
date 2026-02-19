"use client"

import { useEffect, useState } from "react"
import { CheckCircle, Circle, Database, Calendar } from "lucide-react"

import { DashboardOverviewData } from "@/lib/models/dashboard"
import { DashboardService } from "@/lib/services/dashboardService"
import { AlertCard } from "@/components/ui/alert-card"
import { InfoCard } from "@/components/ui/info-card"
import { ActionButton } from "@/components/ui/action-button"
import { SecondaryButton } from "@/components/ui/secondary-button"
import { UsageRow } from "@/components/ui/usage-row"
import { StatCard } from "@/components/stat-card"
import { formatRelativeDate } from "@/lib/utils/date"

interface DashboardOverviewProps {
  onNavigate: (screen: string) => void
}

export function DashboardOverview({ onNavigate }: DashboardOverviewProps) {
  const [data, setData] = useState<DashboardOverviewData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchDashboard() {
      try {
        setLoading(true)

        const token = localStorage.getItem("access_token")
        if (!token) throw new Error("No token")

        const result = await DashboardService.getOverview(token)
        setData(result)
      } catch (e: any) {
        setError(e.message || "Error")
      } finally {
        setLoading(false)
      }
    }

    fetchDashboard()
  }, [])

  if (loading) return <div className="p-6">Loading dashboard…</div>
  if (error || !data) return <div className="p-6 text-red-500">{error || "No data"}</div>

  const { stats, workflow_step } = data

  const steps = [
    { key: "uploaded", label: "Upload Observation Data" },
    { key: "aggregated", label: "Spatial Aggregation" },
    { key: "mapped", label: "Generate Map" },
    { key: "generated", label: "Generate Report" },
  ] as const

  const activeIndex =
    workflow_step !== null
      ? steps.findIndex((s) => s.key === workflow_step)
      : -1

  const progressPercent =
    activeIndex >= 0 ? ((activeIndex + 1) / steps.length) * 100 : 0

  const lastGenRelative = formatRelativeDate(stats.lastGeneration)

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
                label="Your Last Activity"
                value={lastGenRelative}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

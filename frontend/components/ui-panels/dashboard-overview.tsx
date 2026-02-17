"use client"

import { ArrowRight, CheckCircle, Circle, AlertTriangle, Clock } from "lucide-react"

interface DashboardOverviewProps {
  onNavigate: (screen: string) => void
}

type WorkflowStep = "uploaded" | "aggregated" | "mapped" | "generated" | "completed" | null

// Dummy backend data
const dashboardData: {
  stats: {
    countiesProcessed: number
    totalCounties: number
    allReportsDone: number
    lastGeneration: string
    userReportsGenerated: number
  }
  workflow_step: WorkflowStep
} = {
  stats: {
    countiesProcessed: 32,
    totalCounties: 47,
    allReportsDone: 152,
    lastGeneration: "Feb 16",
    userReportsGenerated: 12,
  },
  workflow_step: "aggregated", // set current workflow step here
}

export function DashboardOverview({ onNavigate }: DashboardOverviewProps) {
  const { stats, workflow_step } = dashboardData

  // Steps array in order
  const steps: { key: WorkflowStep; label: string }[] = [
    { key: "uploaded", label: "Upload Observation Data" },
    { key: "aggregated", label: "Spatial Aggregation" },
    { key: "mapped", label: "Generate Map" },
    { key: "generated", label: "Generate Report" },
  ]

  // Determine active index (find by key)
  const activeIndex = workflow_step
    ? steps.findIndex(step => step.key === workflow_step)
    : -1

  const progressPercent = ((activeIndex + 1) / steps.length) * 100

  return (
    <div className="p-6 space-y-6">
      {/* Alerts / Reminders */}
      <div className="space-y-3">
        <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm">Observation Data Reminder</p>
              <p className="text-xs text-muted-foreground mt-1">
                Make sure your observation data for your county is uploaded and complete for this week.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-blue-900/20 border border-blue-700/40 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm">Template Upload Reminder</p>
              <p className="text-xs text-muted-foreground mt-1">
                You can upload a custom report template. If none is uploaded, the default template will be used.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Counties Processed"
          value={`${stats.countiesProcessed} / ${stats.totalCounties}`}
        />
        <StatCard
          label="Last Generation"
          value={stats.lastGeneration}
        />
        <StatCard
          label="All Reports Done"
          value={stats.allReportsDone}
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Workflow Steps with Progress */}
        <div className="lg:col-span-2 bg-card border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Report Generation Process</h2>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-2">
              <span>Progress</span>
              <span className="font-semibold">{activeIndex + 1} / {steps.length}</span>
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full"
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
                    className={`text-gray-400 font-medium transition-all ${
                      completed ? "text-base md:text-lg font-semibold" : "text-sm"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* Sidebar Quick Actions + App Usage */}
        <div className="space-y-4">
          {/* Quick Actions */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="font-semibold mb-4">Quick Actions</h3>
            <div className="space-y-2">
              <button
                onClick={() => onNavigate("generate")}
                className="w-full bg-primary text-primary-foreground py-2 px-4 rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
              >
                Generate Reports <ArrowRight className="w-4 h-4" />
              </button>
              <button
                onClick={() => onNavigate("archive")}
                className="w-full bg-muted text-foreground py-2 px-4 rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
              >
                View Archive
              </button>
              <button
                onClick={() => onNavigate("logs")}
                className="w-full bg-muted text-foreground py-2 px-4 rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
              >
                View Logs
              </button>
            </div>
          </div>

          {/* App Usage */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="font-semibold mb-4">App Usage</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span>Reports Generated</span>
                <span className="font-semibold">{stats.userReportsGenerated}</span>
              </div>
              <div className="flex justify-between">
                <span>Your Last Activity</span>
                <span className="font-semibold">{stats.lastGeneration}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  )
}

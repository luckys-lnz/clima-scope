"use client"

import { BarChart3, AlertTriangle, CheckCircle, Clock, ArrowRight } from "lucide-react"

interface DashboardOverviewProps {
  onNavigate: (screen: string) => void
}

export function DashboardOverview({ onNavigate }: DashboardOverviewProps) {
  return (
    <div className="p-6 space-y-6">
      {/* Alert Cards */}
      <div className="space-y-3">
        <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm">GRIB Data Mismatch</p>
              <p className="text-xs text-muted-foreground mt-1">
                GFS data from Dec 8 missing 4 wards. Archive data restored.
              </p>
            </div>
          </div>
        </div>
        <div className="bg-blue-900/20 border border-blue-700/40 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <Clock className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-sm">Weekly Schedule</p>
              <p className="text-xs text-muted-foreground mt-1">
                Next automated run: Tomorrow at 00:00 UTC
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-lg p-4">
          <p className="text-xs text-muted-foreground mb-1">Counties Processed</p>
          <p className="text-2xl font-bold">32/47</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <p className="text-xs text-muted-foreground mb-1">Last Generation</p>
          <p className="text-2xl font-bold">Dec 9</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <p className="text-xs text-muted-foreground mb-1">Success Rate</p>
          <p className="text-2xl font-bold text-primary">98.2%</p>
        </div>
        <div className="bg-card border border-border rounded-lg p-4">
          <p className="text-xs text-muted-foreground mb-1">Pending</p>
          <p className="text-2xl font-bold text-accent">15</p>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Processing Pipeline */}
        <div className="lg:col-span-2 bg-card border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Weekly Batch Processing</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>Progress</span>
                <span className="font-semibold">68%</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div className="bg-primary h-2 rounded-full" style={{ width: "68%" }} />
              </div>
            </div>

            {/* Steps */}
            <div className="space-y-3 mt-6">
              {[
                { name: "Fetch GFS Data", status: "done" },
                { name: "Parse GRIB Files", status: "done" },
                { name: "Spatial Aggregation", status: "active" },
                { name: "Generate Maps", status: "pending" },
                { name: "Create PDFs", status: "pending" },
              ].map((step, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-semibold flex-shrink-0 ${
                      step.status === "done"
                        ? "bg-green-900/40 text-green-400"
                        : step.status === "active"
                          ? "bg-primary/30 text-primary"
                          : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {step.status === "done" ? "✓" : step.status === "active" ? "→" : "○"}
                  </div>
                  <span className="text-sm">{step.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar Actions */}
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

          {/* System Health */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="font-semibold mb-4">System Health</h3>
            <div className="space-y-4 text-sm">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-muted-foreground">GRIB Storage</span>
                  <span className="font-semibold">847 GB / 1 TB</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="bg-primary h-2 rounded-full" style={{ width: "85%" }} />
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-muted-foreground">Uptime</span>
                  <span className="font-semibold">99.8%</span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{ width: "99.8%" }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

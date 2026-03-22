"use client"

import { useState } from "react"
import { ChevronLeft, Download } from "lucide-react"
import { SelectInput } from "@/components/select-input"

interface LogsDiagnosticsProps {
  onBack: () => void
}

interface LogEntry {
  timestamp: string
  step: string
  county: string
  status: "success" | "error"
  message: string
}

const SAMPLE_LOGS: LogEntry[] = [
  {
    timestamp: "2024-12-08 14:32:45",
    step: "PDF Creation",
    county: "Nairobi",
    status: "success",
    message: "Successfully created PDF report",
  },
  {
    timestamp: "2024-12-08 14:31:20",
    step: "Mapping",
    county: "Nairobi",
    status: "success",
    message: "Generated 45 ward-level maps",
  },
  {
    timestamp: "2024-12-08 14:25:10",
    step: "Spatial Aggregation",
    county: "Mombasa",
    status: "success",
    message: "Aggregated GFS data to 156 wards",
  },
  {
    timestamp: "2024-12-08 14:20:33",
    step: "GRIB Parsing",
    county: "Kisumu",
    status: "error",
    message: "Missing variable: wind_gust",
  },
  {
    timestamp: "2024-12-08 14:15:22",
    step: "GRIB Download",
    county: "Nakuru",
    status: "success",
    message: "Downloaded 2.4 GB of forecast data",
  },
]

export function LogsDiagnostics({ onBack }: LogsDiagnosticsProps) {
  const [filterCounty, setFilterCounty] = useState("")
  const [filterStep, setFilterStep] = useState("")
  const [filterStatus, setFilterStatus] = useState("")

  const filteredLogs = SAMPLE_LOGS.filter((log) => {
    if (filterCounty && !log.county.toLowerCase().includes(filterCounty.toLowerCase())) return false
    if (filterStep && log.step !== filterStep) return false
    if (filterStatus && log.status !== filterStatus) return false
    return true
  })

  return (
    <div className="p-6 space-y-6">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-primary hover:text-primary/80 transition-colors mb-4"
      >
        <ChevronLeft className="w-4 h-4" />
        <span className="text-sm">Back to Dashboard</span>
      </button>

      {/* Filters */}
      <div className="bg-card rounded-lg border border-border p-4">
        <h3 className="font-semibold text-card-foreground mb-4">Filters & Export</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <SelectInput
            value={filterCounty}
            onChange={setFilterCounty}
            options={[
              { value: "", label: "All Counties" },
              { value: "nairobi", label: "Nairobi" },
              { value: "mombasa", label: "Mombasa" },
            ]}
            placeholder="Filter by county..."
          />
          <SelectInput
            value={filterStep}
            onChange={setFilterStep}
            options={[
              { value: "", label: "All Steps" },
              { value: "GRIB Download", label: "GRIB Download" },
              { value: "GRIB Parsing", label: "GRIB Parsing" },
              { value: "Spatial Aggregation", label: "Spatial Aggregation" },
              { value: "Mapping", label: "Mapping" },
              { value: "PDF Creation", label: "PDF Creation" },
            ]}
            placeholder="Filter by step..."
          />
          <SelectInput
            value={filterStatus}
            onChange={setFilterStatus}
            options={[
              { value: "", label: "All Status" },
              { value: "success", label: "Success" },
              { value: "error", label: "Error" },
            ]}
            placeholder="Filter by status..."
          />
          <button className="bg-primary hover:bg-primary/90 text-primary-foreground py-2 px-4 rounded-lg text-sm font-medium transition-colors">
            <Download className="w-4 h-4 inline mr-2" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-card rounded-lg border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border bg-muted">
                <th className="px-6 py-3 text-left text-sm font-semibold text-card-foreground">Timestamp</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-card-foreground">Step</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-card-foreground">County</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-card-foreground">Status</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-card-foreground">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredLogs.map((log, idx) => (
                <tr key={idx} className="hover:bg-muted/50 transition-colors">
                  <td className="px-6 py-4 text-sm text-card-foreground font-mono">{log.timestamp}</td>
                  <td className="px-6 py-4 text-sm text-card-foreground">{log.step}</td>
                  <td className="px-6 py-4 text-sm text-card-foreground">{log.county}</td>
                  <td className="px-6 py-4 text-sm">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${
                        log.status === "success" ? "bg-green-500/20 text-green-600" : "bg-red-500/20 text-red-600"
                      }`}
                    >
                      {log.status === "success" ? "✓" : "✗"} {log.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-card-foreground">{log.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

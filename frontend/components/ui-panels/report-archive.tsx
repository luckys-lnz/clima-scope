"use client"

import { useEffect, useState } from "react"
import { Download, MapPin, Calendar, CheckCircle, XCircle } from "lucide-react"
import { motion } from "framer-motion"
import { SelectInput } from "@/components/select-input"
import { ReportService } from "@/lib/services/reportService"
import { useAuth } from "@/hooks/useAuth"
import type { ReportArchiveItem } from "@/lib/models/report"

const API_BASE = process.env.NEXT_PUBLIC_API_URL

interface ReportArchiveProps {
  onSelectCounty: (county: string) => void
}

const REPORTS_CACHE_KEY = "report_archive_cache_v1"

export function ReportArchive({ onSelectCounty }: ReportArchiveProps) {
  const getCachedReports = (): ReportArchiveItem[] | null => {
    if (typeof window === "undefined") return null
    try {
      const raw = sessionStorage.getItem(REPORTS_CACHE_KEY)
      return raw ? (JSON.parse(raw) as ReportArchiveItem[]) : null
    } catch {
      return null
    }
  }

  const { access_token: token, isLoading: authLoading } = useAuth()

  const [reports, setReports] = useState<ReportArchiveItem[]>(() => getCachedReports() || [])
  const [loading, setLoading] = useState(() => !getCachedReports())

  const [filterCounty, setFilterCounty] = useState("")
  const [filterStatus, setFilterStatus] = useState("")

  useEffect(() => {
    if (authLoading) return

    if (!token) {
      setReports([])
      setLoading(false)
      return
    }

    const loadReports = async () => {
      try {
        // Only show blocking loader if cache is empty.
        if (reports.length === 0) setLoading(true)
        const data = await ReportService.getReports(token)
        setReports(data)
        sessionStorage.setItem(REPORTS_CACHE_KEY, JSON.stringify(data))
      } catch {
        if (reports.length === 0) setReports([])
      } finally {
        if (reports.length === 0) setLoading(false)
      }
    }

    if (reports.length > 0) {
      setLoading(false)
    }

    loadReports()
  }, [token, authLoading])

  // backend → UI mapping
  const uiReports = reports.map((r) => ({
    id: r.id,
    county: r.county,
    dateGenerated: new Date(r.generatedAt).toLocaleDateString(),
    status: r.status,
    pdfUrl: r.pdfUrl,
    startDate: r.periodStart,
    endDate: r.periodEnd,
  }))

  const filteredReports = uiReports.filter((r) => {
    if (filterCounty && !r.county.toLowerCase().includes(filterCounty.toLowerCase())) return false
    if (filterStatus && r.status !== filterStatus) return false
    return true
  })

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="p-4 sm:p-6 space-y-6 lg:pt-0"
    >
      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-card rounded-lg border border-border p-3 sm:p-4"
      >
        <h3 className="font-semibold text-sm sm:text-base text-card-foreground mb-4">Filters</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 sm:gap-4">
          <SelectInput
            value={filterCounty}
            onChange={setFilterCounty}
            options={[
              { value: "", label: "All Counties" },
              ...Array.from(new Set(uiReports.map(r => r.county))).map(c => ({
                value: c.toLowerCase(),
                label: c
              }))
            ]}
            placeholder="Filter by county..."
          />
          <SelectInput
            value={filterStatus}
            onChange={setFilterStatus}
            options={[
              { value: "", label: "All Status" },
              { value: "success", label: "Success" },
              { value: "failed", label: "Failed" },
            ]}
            placeholder="Filter by status..."
          />
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="bg-primary hover:bg-primary/90 text-primary-foreground py-2 px-4 rounded-lg text-xs sm:text-sm font-medium transition-colors col-span-1 sm:col-span-2 md:col-span-1"
          >
            <Download className="w-4 h-4 inline mr-2" />
            Export as ZIP
          </motion.button>
        </div>
      </motion.div>

      {/* Reports Table */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="bg-card rounded-lg border border-border overflow-hidden"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-xs sm:text-sm">
            <thead>
              <tr className="border-b border-border bg-muted">
                <th className="px-3 sm:px-6 py-2 sm:py-3 text-left font-semibold text-card-foreground">County</th>
                <th className="px-3 sm:px-6 py-2 sm:py-3 text-left font-semibold text-card-foreground hidden sm:table-cell">Generated</th>
                <th className="px-3 sm:px-6 py-2 sm:py-3 text-left font-semibold text-card-foreground">Status</th>
                <th className="px-3 sm:px-6 py-2 sm:py-3 text-left font-semibold text-card-foreground hidden lg:table-cell">Start</th>
                <th className="px-3 sm:px-6 py-2 sm:py-3 text-left font-semibold text-card-foreground hidden md:table-cell">End</th>
                <th className="px-3 sm:px-6 py-2 sm:py-3 text-left font-semibold text-card-foreground">Actions</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-border">
              {loading && (
                <tr>
                  <td colSpan={6} className="px-6 py-6 text-center text-muted-foreground">
                    Loading reports…
                  </td>
                </tr>
              )}

              {!loading && filteredReports.map((report, idx) => (
                <motion.tr
                  key={report.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="hover:bg-muted/50 transition-colors"
                >
                  <td className="px-3 sm:px-6 py-3 sm:py-4 font-medium flex items-center gap-2">
                    <MapPin className="w-3 h-3 sm:w-4 sm:h-4 text-muted-foreground flex-shrink-0" />
                    <span className="truncate">{report.county}</span>
                  </td>

                  <td className="px-3 sm:px-6 py-3 sm:py-4 hidden sm:table-cell">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-3 h-3 sm:w-4 sm:h-4 text-muted-foreground" />
                      {report.dateGenerated}
                    </div>
                  </td>

                  <td className="px-3 sm:px-6 py-3 sm:py-4">
                    <div className="flex items-center gap-2">
                      {report.status === "success" ? (
                        <>
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span className="text-green-600 hidden xs:inline">Success</span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-4 h-4 text-red-500" />
                          <span className="text-red-600 hidden xs:inline">Failed</span>
                        </>
                      )}
                    </div>
                  </td>

                  <td className="px-3 sm:px-6 py-3 sm:py-4 hidden lg:table-cell">
                    {report.startDate}
                  </td>

                  <td className="px-3 sm:px-6 py-3 sm:py-4 hidden md:table-cell">
                    {report.endDate}
                  </td>

                  <td className="px-3 sm:px-6 py-3 sm:py-4">
                    <div className="flex gap-2">
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => onSelectCounty(report.county)}
                        className="text-primary hover:text-primary/80 text-xs font-medium"
                      >
                        View
                      </motion.button>

                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => {
                          if (!token) return
                          // prepend API_BASE for download
                          window.open(`${API_BASE}${report.pdfUrl}`, "_blank")
                        }}
                        className="text-primary hover:text-primary/80 text-xs font-medium"
                      >
                        PDF
                      </motion.button>
                    </div>
                  </td>
                </motion.tr>
              ))}

              {!loading && filteredReports.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-6 text-center text-muted-foreground">
                    No reports found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </motion.div>
    </motion.div>
  )
}

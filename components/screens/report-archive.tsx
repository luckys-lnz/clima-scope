"use client"

import { useState } from "react"
import { Download, MapPin, Calendar, CheckCircle, XCircle } from "lucide-react"
import { motion } from "framer-motion"
import { SelectInput } from "@/components/select-input"

interface ReportArchiveProps {
  onSelectCounty: (county: string) => void
}

interface Report {
  id: string
  county: string
  dateGenerated: string
  status: "success" | "failed"
  pdfUrl: string
  gribTimestamp: string
  modelVersion: string
}

const SAMPLE_REPORTS: Report[] = [
  {
    id: "1",
    county: "Nairobi",
    dateGenerated: "Dec 8, 2024",
    status: "success",
    pdfUrl: "#",
    gribTimestamp: "2024-12-08 00:00",
    modelVersion: "GFS v15.1",
  },
  {
    id: "2",
    county: "Mombasa",
    dateGenerated: "Dec 8, 2024",
    status: "success",
    pdfUrl: "#",
    gribTimestamp: "2024-12-08 00:00",
    modelVersion: "GFS v15.1",
  },
  {
    id: "3",
    county: "Kisumu",
    dateGenerated: "Dec 8, 2024",
    status: "success",
    pdfUrl: "#",
    gribTimestamp: "2024-12-08 00:00",
    modelVersion: "GFS v15.1",
  },
  {
    id: "4",
    county: "Meru",
    dateGenerated: "Dec 8, 2024",
    status: "failed",
    pdfUrl: "#",
    gribTimestamp: "2024-12-08 00:00",
    modelVersion: "GFS v15.1",
  },
  {
    id: "5",
    county: "Nakuru",
    dateGenerated: "Dec 7, 2024",
    status: "success",
    pdfUrl: "#",
    gribTimestamp: "2024-12-07 00:00",
    modelVersion: "GFS v15.1",
  },
]

export function ReportArchive({ onSelectCounty }: ReportArchiveProps) {
  const [filterCounty, setFilterCounty] = useState("")
  const [filterStatus, setFilterStatus] = useState("")
  const [filterDate, setFilterDate] = useState("")

  const filteredReports = SAMPLE_REPORTS.filter((r) => {
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
              { value: "nairobi", label: "Nairobi" },
              { value: "mombasa", label: "Mombasa" },
              { value: "kisumu", label: "Kisumu" },
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
                <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs sm:text-sm font-semibold text-card-foreground">County</th>
                <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs sm:text-sm font-semibold text-card-foreground hidden sm:table-cell">Date</th>
                <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs sm:text-sm font-semibold text-card-foreground">Status</th>
                <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs sm:text-sm font-semibold text-card-foreground hidden lg:table-cell">GRIB</th>
                <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs sm:text-sm font-semibold text-card-foreground hidden md:table-cell">Model</th>
                <th className="px-3 sm:px-6 py-2 sm:py-3 text-left text-xs sm:text-sm font-semibold text-card-foreground">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredReports.map((report, idx) => (
                <motion.tr
                  key={report.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="hover:bg-muted/50 transition-colors"
                >
                  <td className="px-3 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-card-foreground font-medium flex items-center gap-2">
                    <MapPin className="w-3 h-3 sm:w-4 sm:h-4 text-muted-foreground flex-shrink-0" />
                    <span className="truncate">{report.county}</span>
                  </td>
                  <td className="px-3 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-card-foreground hidden sm:table-cell">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-3 h-3 sm:w-4 sm:h-4 text-muted-foreground flex-shrink-0" />
                      {report.dateGenerated}
                    </div>
                  </td>
                  <td className="px-3 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm">
                    <div className="flex items-center gap-2">
                      {report.status === "success" ? (
                        <>
                          <CheckCircle className="w-3 h-3 sm:w-4 sm:h-4 text-green-500 flex-shrink-0" />
                          <span className="text-green-600 hidden xs:inline">Success</span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-3 h-3 sm:w-4 sm:h-4 text-red-500 flex-shrink-0" />
                          <span className="text-red-600 hidden xs:inline">Failed</span>
                        </>
                      )}
                    </div>
                  </td>
                  <td className="px-3 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-card-foreground hidden lg:table-cell">{report.gribTimestamp}</td>
                  <td className="px-3 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm text-card-foreground hidden md:table-cell">{report.modelVersion}</td>
                  <td className="px-3 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm">
                    <div className="flex gap-1 sm:gap-2">
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => onSelectCounty(report.county)}
                        className="text-primary hover:text-primary/80 transition-colors text-xs font-medium"
                      >
                        View
                      </motion.button>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className="text-primary hover:text-primary/80 transition-colors text-xs font-medium"
                      >
                        PDF
                      </motion.button>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </motion.div>
  )
}

"use client"

import { useEffect, useState } from "react"
import { ChevronLeft, Download, RefreshCw } from "lucide-react"
import { motion } from "framer-motion"
import { LogViewer } from "@/components/log-viewer"
import {
  formatWeeklyReportWindow,
  getCurrentWeeklyReportWindow,
} from "@/lib/utils/report_date"
import { authService } from "@/lib/services/authService"
import { workflowService } from "@/lib/services/workflowService"
import type { ValidationResponse, MapOutput } from "@/lib/models/workflow"

interface ManualGenerationProps {
  onBack: () => void
}

export function ManualGeneration({ onBack }: ManualGenerationProps) {
  // ===== WORKFLOW STATE =====
  const [step, setStep] = useState(1)
  const totalSteps = 4

  const [userCounty, setUserCounty] = useState("")
  const [availableVars, setAvailableVars] = useState<string[]>([])
  const [selectedVars, setSelectedVars] = useState<string[]>([])
  const [logs, setLogs] = useState<string[]>([])
  const [validationResult, setValidationResult] = useState<ValidationResponse | null>(null)
  const [generatedMaps, setGeneratedMaps] = useState<MapOutput[]>([])

  const [isGenerating, setIsGenerating] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [downloadUrl, setDownloadUrl] = useState("")
  const [errorMessage, setErrorMessage] = useState("")
  const [sessionToken, setSessionToken] = useState<string | null>(null)

  const reportWindow = getCurrentWeeklyReportWindow()

  // ===== HELPER: Format date to ISO string (YYYY-MM-DD) =====
  const formatDateToISO = (date: Date): string => {
    return date.toISOString().split('T')[0] // "2026-03-23"
  }

  // ===== SESSION =====
  useEffect(() => {
    authService.getSession().then((session) => {
      if (session?.user) {
        setUserCounty(session.user.county || "")
        setSessionToken(session.access_token)
      }
    })
  }, [])

  // ===== LOG HELPER =====
  const addLog = (msg: string) => {
    setLogs((prev) => [
      ...prev,
      `[${new Date().toLocaleTimeString()}] ${msg}`,
    ])
  }

  // ===== STEP 1: VALIDATE DATA =====
  const handleValidate = async () => {
    if (!sessionToken) {
      setErrorMessage("No active session")
      return
    }

    if (!reportWindow) {
      setErrorMessage("No active reporting period")
      return
    }

    addLog(`Stage 1: Checking observation for Week ${reportWindow.week}, ${reportWindow.year}…`)
    setIsGenerating(true)
    setErrorMessage("")

    try {
      const result = await workflowService.validateInputs(
        sessionToken,
        {
          report_week: reportWindow.week,
          report_year: reportWindow.year,
          report_start_at: formatDateToISO(reportWindow.start),
          report_end_at: formatDateToISO(reportWindow.end)
        }
      )
      
      setValidationResult(result)
      setAvailableVars(result.variables)
      setStep(2)

      addLog(`✓ Files found: ${result.observation_file}, ${result.shapefile}`)
      addLog(`✓ Variables detected: ${result.variables.join(", ")}`)
      addLog(`✓ Report period: Week ${result.report_week}, ${result.report_year}`)
      addLog(`✓ Period dates: ${result.report_period.start} to ${result.report_period.end}`)
      addLog(`✓ File stats: ${result.row_count} rows, ${result.column_count} columns`)
      addLog("Stage 1 complete")
    } catch (e: any) {
      const errorMsg = e.message || "Validation failed"
      addLog(`✗ Validation failed: ${errorMsg}`)
      setErrorMessage(errorMsg)
    } finally {
      setIsGenerating(false)
    }
  }

  // ===== STEP 2: VARIABLE SELECT =====
  const handleNextToMaps = () => {
    addLog(`Variables selected: ${selectedVars.join(", ")}`)
    setStep(3)
  }

  // ===== STEP 3: MAP GENERATION (USING WORKFLOW SERVICE) =====
  const handleGenerateMaps = async () => {
    if (!sessionToken || !reportWindow) return

    addLog("Stage 3: Generating maps…")
    setIsGenerating(true)
    setErrorMessage("")

    try {
      const result = await workflowService.generateMaps(sessionToken, {
        county: userCounty,
        variables: selectedVars,
        report_week: reportWindow.week,
        report_year: reportWindow.year,
        report_start_at: formatDateToISO(reportWindow.start),
        report_end_at: formatDateToISO(reportWindow.end)
      })

      setGeneratedMaps(result.outputs)

      result.outputs.forEach((map: MapOutput) =>
        addLog(`✓ Map ready: ${map.variable}`)
      )

      setStep(4)
      addLog("Stage 3 complete")
    } catch (e: any) {
      const errorMsg = e.message || "Map generation failed"
      addLog(`✗ Map generation failed: ${errorMsg}`)
      setErrorMessage(errorMsg)
    } finally {
      setIsGenerating(false)
    }
  }

  // ===== STEP 4: REPORT GENERATION (USING WORKFLOW SERVICE) =====
  const handleGenerateReport = async () => {
    if (!reportWindow || !sessionToken) {
      const errorMsg = !sessionToken ? "No active session" : "No active reporting period"
      addLog(`✗ Report generation blocked: ${errorMsg}`)
      setErrorMessage(errorMsg)
      return
    }

    addLog("Stage 4: Starting report generation workflow…")
    setIsGenerating(true)
    setErrorMessage("")

    try {
      const result = await workflowService.generateReport(sessionToken, {
        county_name: userCounty,
        week_number: reportWindow.week,
        year: reportWindow.year,
        report_start_at: formatDateToISO(reportWindow.start),
        report_end_at: formatDateToISO(reportWindow.end),
        variables: selectedVars
      })

      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      setDownloadUrl(`${baseUrl}${result.pdf_url}`)

      if (result.stage_statuses?.length) {
        result.stage_statuses.forEach((s) => {
          const prefix = s.status === "failed" ? "✗" : s.status === "in_progress" ? "…" : "✓"
          addLog(`${prefix} [${s.stage}] ${s.message}`)
        })
      }

      addLog(`✓ Report generated: ${result.filename}`)
      addLog("Workflow complete")

      setIsComplete(true)
    } catch (e: any) {
      const errorMsg = e.message || "Report generation failed"
      addLog(`✗ Report generation failed: ${errorMsg}`)
      setErrorMessage(errorMsg)
    } finally {
      setIsGenerating(false)
    }
  }

  // ===== RESET WORKFLOW =====
  const handleReset = () => {
    setStep(1)
    setSelectedVars([])
    setLogs([])
    setValidationResult(null)
    setGeneratedMaps([])
    setIsComplete(false)
    setDownloadUrl("")
    setErrorMessage("")
    addLog("Workflow reset")
  }

  // ===== UI =====
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-4 sm:p-6 space-y-6 lg:pt-0"
    >
      {/* BACK BUTTON */}
      <div className="flex items-center justify-between">
        <motion.button
          onClick={onBack}
          whileHover={{ x: -4 }}
          className="flex items-center gap-2 text-primary"
        >
          <ChevronLeft className="w-4 h-4" />
          <span className="text-sm">Back to Dashboard</span>
        </motion.button>

        {step > 1 && !isComplete && (
          <button
            onClick={handleReset}
            className="text-sm text-muted-foreground hover:text-primary"
          >
            Reset Workflow
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT PANEL — STEPPER */}
        <div className="lg:col-span-1">
          <div className="bg-card rounded-lg border border-border p-6 space-y-4">
            <h2 className="font-bold text-lg">Weekly Report</h2>

            <div className="text-xs text-muted-foreground">
              Step {step}/{totalSteps}
            </div>

            {/* STEP 1: VALIDATE */}
            {step === 1 && (
              <>
                <div>
                  <label className="text-xs font-medium">County</label>
                  <div className="bg-muted border rounded-lg px-3 py-2 text-sm">
                    {userCounty || "—"}
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium">Reporting Period</label>
                  <div className="bg-muted border rounded-lg px-3 py-2 text-sm">
                    {reportWindow
                      ? formatWeeklyReportWindow(reportWindow)
                      : "Next report available Monday"}
                  </div>
                </div>

                <button
                  disabled={isGenerating || !sessionToken}
                  onClick={handleValidate}
                  className="w-full bg-primary text-primary-foreground py-2 rounded-lg disabled:opacity-50"
                >
                  {isGenerating ? "Validating..." : "Next: Validate Data"}
                </button>
              </>
            )}

            {/* STEP 2: SELECT VARIABLES */}
            {step === 2 && (
              <>
                <p className="text-sm font-medium">Available variables:</p>

                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {availableVars.map((v) => (
                    <label
                      key={v}
                      className="flex items-center gap-2 text-sm cursor-pointer hover:bg-muted p-1 rounded"
                    >
                      <input
                        type="checkbox"
                        checked={selectedVars.includes(v)}
                        onChange={() =>
                          setSelectedVars((prev) =>
                            prev.includes(v)
                              ? prev.filter((x) => x !== v)
                              : [...prev, v]
                          )
                        }
                        className="cursor-pointer"
                      />
                      <span className="capitalize">{v}</span>
                    </label>
                  ))}
                </div>

                <button
                  disabled={selectedVars.length === 0}
                  onClick={handleNextToMaps}
                  className="w-full bg-primary text-primary-foreground py-2 rounded-lg disabled:opacity-50"
                >
                  Next: Generate Maps ({selectedVars.length} selected)
                </button>
              </>
            )}

            {/* STEP 3: GENERATE MAPS */}
            {step === 3 && (
              <>
                <p className="text-sm font-medium">Maps to generate:</p>

                <ul className="text-sm list-disc ml-4 space-y-1">
                  {selectedVars.map((v) => (
                    <li key={v} className="capitalize">{v}</li>
                  ))}
                </ul>

                <button
                  disabled={isGenerating}
                  onClick={handleGenerateMaps}
                  className="w-full bg-primary text-primary-foreground py-2 rounded-lg disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {isGenerating ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    "Generate Maps"
                  )}
                </button>
              </>
            )}

            {/* STEP 4: GENERATE REPORT */}
            {step === 4 && !isComplete && (
              <>
                <p className="text-sm font-medium">Generated Maps:</p>

                <ul className="text-sm list-disc ml-4 space-y-1">
                  {generatedMaps.map((map) => (
                    <li key={map.variable} className="capitalize flex items-center gap-2">
                      <span>{map.variable}</span>
                      <a 
                        href={map.map_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline"
                      >
                        (view)
                      </a>
                    </li>
                  ))}
                </ul>

                <button
                  disabled={isGenerating}
                  onClick={handleGenerateReport}
                  className="w-full bg-primary text-primary-foreground py-2 rounded-lg disabled:opacity-50"
                >
                  {isGenerating ? "Generating Report..." : "Generate Report"}
                </button>
              </>
            )}

            {/* COMPLETED */}
            {isComplete && (
              <>
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 text-center">
                  <p className="text-sm text-green-600 font-medium">✓ Workflow Complete</p>
                </div>

                <button
                  onClick={handleReset}
                  className="w-full border border-border py-2 rounded-lg text-sm hover:bg-muted transition-colors"
                >
                  Start New Report
                </button>
              </>
            )}
          </div>
        </div>

        {/* RIGHT PANEL — LOGS AND PREVIEW */}
        <div className="lg:col-span-2">
          <div className="bg-card rounded-lg border border-border p-6">
            <h2 className="font-bold text-lg mb-4">Processing Logs</h2>

            <LogViewer logs={logs} />

            {/* Validation Summary */}
            {validationResult && step > 1 && (
              <div className="mt-4 bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                <p className="text-xs text-blue-600 font-medium mb-1">Validation Summary</p>
                <p className="text-sm">
                  <span className="font-medium">File:</span> {validationResult.observation_file}<br />
                  <span className="font-medium">Variables:</span> {validationResult.variables.join(", ")}<br />
                  <span className="font-medium">Period:</span> {validationResult.report_period.start} to {validationResult.report_period.end}<br />
                  <span className="font-medium">Rows:</span> {validationResult.row_count}, <span className="font-medium">Columns:</span> {validationResult.column_count}
                </p>
              </div>
            )}

            {/* Generated Maps Preview */}
            {generatedMaps.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium mb-2">Generated Maps:</p>
                <div className="grid grid-cols-2 gap-2">
                  {generatedMaps.map((map) => (
                    <a
                      key={map.variable}
                      href={map.map_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="border border-border rounded-lg p-2 hover:bg-muted transition-colors"
                    >
                      <p className="text-xs text-center capitalize">{map.variable}</p>
                      <p className="text-[10px] text-muted-foreground text-center mt-1">Click to view</p>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Error Message */}
            {errorMessage && (
              <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                <p className="text-sm text-red-600">{errorMessage}</p>
              </div>
            )}

            {/* Download Section */}
            {isComplete && downloadUrl && (
              <div className="mt-6 space-y-3">
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                  <p className="text-sm text-green-600 font-medium">✓ Report generated successfully</p>
                </div>

                <div className="flex gap-3">
                  <a
                    href={downloadUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 bg-primary text-primary-foreground py-2 px-4 rounded-lg text-sm flex items-center justify-center gap-2 hover:bg-primary/90 transition-colors"
                  >
                    <Download className="w-4 h-4" />
                    Download PDF
                  </a>

                  <button
                    onClick={handleGenerateReport}
                    className="flex-1 border border-border py-2 px-4 rounded-lg text-sm flex items-center justify-center gap-2 hover:bg-muted transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Regenerate
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

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
import type { ValidationResponse } from "@/lib/models/workflow"

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

  const [isGenerating, setIsGenerating] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [downloadUrl, setDownloadUrl] = useState("")
  const [errorMessage, setErrorMessage] = useState("")
  const [sessionToken, setSessionToken] = useState<string | null>(null)

  const reportWindow = getCurrentWeeklyReportWindow()

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

    addLog("Stage 1: Checking observation & shapefiles…")
    setIsGenerating(true)
    setErrorMessage("")

    try {
      // Call backend validation using workflow service
      const result = await workflowService.validateInputs(sessionToken)
      
      setValidationResult(result)
      setAvailableVars(result.variables)
      setStep(2)

      addLog(`✓ Files found: ${result.observation_file}, ${result.shapefile}`)
      addLog(`✓ Variables detected: ${result.variables.join(", ")}`)
      addLog(`✓ Report period: Week ${result.report_week}, ${result.report_year}`)
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

  // ===== STEP 3: MAP GENERATION =====
  const handleGenerateMaps = async () => {
    if (!sessionToken) return

    addLog("Stage 3: Generating maps…")
    setIsGenerating(true)

    try {
      // This would be your next endpoint
      const res = await fetch("/api/v1/workflow/generate-maps", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${sessionToken}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          county: userCounty,
          variables: selectedVars,
          report_week: reportWindow.week,
          report_year: reportWindow.year
        })
      })

      const data = await res.json()
      
      if (!res.ok) {
        throw new Error(data.detail || "Map generation failed")
      }

      data.outputs?.forEach((o: any) =>
        addLog(`✓ Map ready: ${o.variable}`)
      )

      setStep(4)
      addLog("Stage 3 complete")
    } catch (e: any) {
      addLog(`✗ Map generation failed: ${e.message}`)
      setErrorMessage(e.message)
    } finally {
      setIsGenerating(false)
    }
  }

  // ===== STEP 4: REPORT =====
  const handleGenerateReport = async () => {
    if (!reportWindow || !sessionToken) return

    addLog("Stage 4: Generating final report…")
    setIsGenerating(true)

    try {
      const res = await fetch("/api/v1/workflow/generate-report", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${sessionToken}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          county_name: userCounty,
          week_number: reportWindow.week,
          year: reportWindow.year,
          variables: selectedVars
        })
      })

      const data = await res.json()
      
      if (!res.ok) {
        throw new Error(data.detail || "Report generation failed")
      }

      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
      setDownloadUrl(`${baseUrl}${data.pdf_url}`)

      addLog(`✓ Report generated: ${data.filename}`)
      addLog("Workflow complete")

      setIsComplete(true)
    } catch (e: any) {
      addLog(`✗ Report generation failed: ${e.message}`)
      setErrorMessage(e.message)
    } finally {
      setIsGenerating(false)
    }
  }

  // ===== UI =====
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-4 sm:p-6 space-y-6 lg:pt-0"
    >
      {/* BACK */}
      <motion.button
        onClick={onBack}
        whileHover={{ x: -4 }}
        className="flex items-center gap-2 text-primary"
      >
        <ChevronLeft className="w-4 h-4" />
        <span className="text-sm">Back to Dashboard</span>
      </motion.button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* LEFT PANEL — STEPPER */}
        <div className="lg:col-span-1">
          <div className="bg-card rounded-lg border border-border p-6 space-y-4">
            <h2 className="font-bold text-lg">Weekly Report</h2>

            <div className="text-xs text-muted-foreground">
              Step {step}/{totalSteps}
            </div>

            {/* STEP 1 */}
            {step === 1 && (
              <>
                <div>
                  <label className="text-xs font-medium">County</label>
                  <div className="bg-muted border rounded-lg px-3 py-2 text-sm">
                    {userCounty || "—"}
                  </div>
                </div>

                <div>
                  <label className="text-xs font-medium">
                    Reporting Period
                  </label>
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

            {/* STEP 2 */}
            {step === 2 && (
              <>
                <p className="text-sm font-medium">
                  Available variables:
                </p>

                <div className="space-y-2">
                  {availableVars.map((v) => (
                    <label
                      key={v}
                      className="flex items-center gap-2 text-sm"
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
                      />
                      {v}
                    </label>
                  ))}
                </div>

                <button
                  disabled={selectedVars.length === 0}
                  onClick={handleNextToMaps}
                  className="w-full bg-primary text-primary-foreground py-2 rounded-lg disabled:opacity-50"
                >
                  Next: Generate Maps
                </button>
              </>
            )}

            {/* STEP 3 */}
            {step === 3 && (
              <>
                <p className="text-sm">Maps will be created for:</p>

                <ul className="text-sm list-disc ml-4">
                  {selectedVars.map((v) => (
                    <li key={v}>{v}</li>
                  ))}
                </ul>

                <button
                  disabled={isGenerating}
                  onClick={handleGenerateMaps}
                  className="w-full bg-primary text-primary-foreground py-2 rounded-lg disabled:opacity-50"
                >
                  {isGenerating ? "Generating..." : "Next: Generate Tables"}
                </button>
              </>
            )}

            {/* STEP 4 */}
            {step === 4 && (
              <>
                <p className="text-sm">All components ready</p>

                <button
                  disabled={isGenerating}
                  onClick={handleGenerateReport}
                  className="w-full bg-primary text-primary-foreground py-2 rounded-lg disabled:opacity-50"
                >
                  {isGenerating ? "Generating..." : "Generate Report"}
                </button>
              </>
            )}
          </div>
        </div>

        {/* RIGHT PANEL — LOGS */}
        <div className="lg:col-span-2">
          <div className="bg-card rounded-lg border border-border p-6">
            <h2 className="font-bold text-lg mb-4">
              Processing Logs
            </h2>

            <LogViewer logs={logs} />

            {validationResult && step > 1 && (
              <div className="mt-4 bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                <p className="text-xs text-blue-600 font-medium">Validation Summary</p>
                <p className="text-sm mt-1">
                  File: {validationResult.observation_file}<br />
                  Variables: {validationResult.variables.join(", ")}<br />
                  Rows: {validationResult.row_count}, Columns: {validationResult.column_count}
                </p>
              </div>
            )}

            {errorMessage && (
              <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                <p className="text-sm text-red-600">
                  {errorMessage}
                </p>
              </div>
            )}

            {isComplete && (
              <div className="mt-6 space-y-3">
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                  <p className="text-sm text-green-600">
                    ✓ Report generated successfully
                  </p>
                </div>

                <div className="flex gap-3">
                  <a
                    href={downloadUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="flex-1 bg-primary text-primary-foreground py-2 px-4 rounded-lg text-sm flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Download PDF
                  </a>

                  <button
                    onClick={handleGenerateReport}
                    className="flex-1 border border-border py-2 px-4 rounded-lg text-sm flex items-center justify-center gap-2"
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
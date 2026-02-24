"use client"

import { useEffect, useRef, useState } from "react"
import { Loader2 } from "lucide-react"
import { uploadService, ReportingPeriod } from "@/lib/services/uploadService"
import { FileUploadSection } from "@/components/file-upload-section"
import {
  getForecastWindowFromAnyDay,
  formatWeeklyReportWindow,
  WeeklyReportWindow,
} from "@/lib/utils/report_date"
import type { Upload } from "@/lib/models/upload"

interface DataUploadProps {
  onBack: () => void
}

export function DataUpload({ onBack }: DataUploadProps) {
  const uploadRef = useRef<HTMLInputElement>(null)

  const [files, setFiles] = useState<File[]>([])
  const [window, setWindow] = useState<WeeklyReportWindow | null>(null)

  const [step, setStep] =
    useState<"idle" | "uploading" | "done" | "error">("idle")
  const [error, setError] = useState<string | null>(null)
  const [uploadedFiles, setUploadedFiles] = useState<Upload[]>([])

  // auto-calc reporting period from TODAY
  useEffect(() => {
    const w = getForecastWindowFromAnyDay(new Date())
    setWindow(w)
  }, [])

  const handleFileSelect = (fileList: FileList | null) => {
    if (!fileList) return
    setFiles(prev => [...prev, ...Array.from(fileList)])
  }

  const deleteUploadedFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    handleFileSelect(e.dataTransfer.files)
  }

  const handleDragOver = (e: React.DragEvent) => e.preventDefault()

  const handleSave = async () => {
    if (!files.length || !window) return

    try {
      setStep("uploading")
      setError(null)

      // Build reporting period payload
      const period: ReportingPeriod = {
        report_week: window.week,
        report_year: window.year,
        report_start_at: window.start.toISOString().slice(0, 10),
        report_end_at: window.end.toISOString().slice(0, 10),
      }

      const response = await uploadService.uploadFiles(files, "observations", period)

      setUploadedFiles(response)
      setStep("done")

      // Clear local files after a short delay
      setTimeout(() => setFiles([]), 2000)
    } catch (err: any) {
      setError(err.message || "Upload failed")
      setStep("error")
    }
  }

  const isUploading = step === "uploading"

  return (
    <div className="p-6 space-y-6">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-primary hover:text-primary/80 mb-4"
      >
        ← Back to Dashboard
      </button>

      <div className="max-w-3xl space-y-6">
        {/* HEADER */}
        <div className="bg-black rounded-lg border border-gray-700 p-6 text-white">
          <h1 className="font-bold text-xl">Upload Data</h1>
          <p className="text-sm text-gray-300">
            High-resolution weather observation data for ward-level forecasts
          </p>
        </div>

        {/* COMBINED REPORTING PERIOD + FILE UPLOAD */}
        {window && (
          <div className="bg-black rounded-lg border border-gray-700 p-6 text-white space-y-4">
            {/* Section title */}
            <div>
              <h2 className="font-semibold text-lg">
                Weather Observation Data (CSV required)
              </h2>
              <p className="text-sm text-gray-400">
                Upload high-resolution weather data for ward-level forecasts. Ensure your CSV files are formatted correctly and include all necessary columns.
              </p>
            </div>

            {/* Reporting period (font size reduced) */}
            <div className="bg-black/40 border border-gray-700 rounded-md p-3">
              <p className="text-xs text-gray-400">Reporting Period</p>
              <p className="text-sm font-semibold text-gray-200">
                {formatWeeklyReportWindow(window)}
              </p>
            </div>

            {/* Upload area */}
            <FileUploadSection
              files={files}
              onFileSelect={handleFileSelect}
              onDeleteFile={deleteUploadedFile}
              accept=".csv"
              uploadRef={uploadRef}
              onDrop={handleDrop}
              onDragOver={handleDragOver} title={""} description={""} />
          </div>
        )}

        {/* SAVE BUTTON */}
        <button
          onClick={handleSave}
          disabled={isUploading || files.length === 0 || !window}
          className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-white py-3 rounded-lg font-medium flex justify-center items-center gap-2"
        >
          {isUploading && <Loader2 className="w-4 h-4 animate-spin" />}
          {isUploading
            ? `Uploading ${files.length} file${files.length !== 1 ? "s" : ""}...`
            : "Upload Files"}
        </button>

        {files.length > 0 && !isUploading && (
          <p className="text-sm text-gray-400 text-center">
            {files.length} file{files.length !== 1 ? "s" : ""} ready to upload
          </p>
        )}

        {error && (
          <p className="text-sm text-red-500 text-center">{error}</p>
        )}
      </div>
    </div>
  )
}
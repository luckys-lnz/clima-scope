"use client"

import { useRef, useState } from "react"
import { Loader2, Check, AlertTriangle } from "lucide-react"
import { uploadService } from "../app/services/uploadService"
import { FileUploadSection } from "./file-upload-section"
import type { Upload } from "@/app/models/upload"

interface DataUploadProps {
  onBack: () => void
}

export function DataUpload({ onBack }: DataUploadProps) {
  const uploadRef = useRef<HTMLInputElement>(null)

  const [files, setFiles] = useState<File[]>([])
  const [uploaded, setUploaded] = useState<Upload[]>([])
  const [step, setStep] = useState<"idle" | "uploading" | "saving" | "done" | "error">("idle")
  const [error, setError] = useState<string | null>(null)

  // ---------------------------
  // File selection
  // ---------------------------
  const handleFileSelect = (fileList: FileList | null) => {
    if (!fileList) return
    setFiles(prev => [...prev, ...Array.from(fileList)])
  }

  const deleteUploadedFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  // ---------------------------
  // Drag & drop
  // ---------------------------
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    handleFileSelect(e.dataTransfer.files)
  }

  const handleDragOver = (e: React.DragEvent) => e.preventDefault()

  // ---------------------------
  // Save / Upload
  // ---------------------------
  const handleSave = async () => {
    if (!files.length) return

    try {
      setStep("uploading")
      setError(null)

      const results: Upload[] = []

      for (const file of files) {
        const upload = await uploadService.uploadFile(file)
        results.push(upload)
      }

      setUploaded(results)
      setStep("done")
      setTimeout(onBack, 2000)
    } catch (err: any) {
      setError(err.message || "Upload failed")
      setStep("error")
    }
  }

  const isSaveDisabled =
    step === "uploading" || step === "saving" || files.length === 0

  // ---------------------------
  // UI
  // ---------------------------
  return (
    <div className="p-6 space-y-6">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-primary hover:text-primary/80 mb-4"
      >
        Back to Dashboard
      </button>

      <div className="max-w-3xl space-y-6">
        <div className="bg-black rounded-lg border border-gray-700 p-6 text-white">
          <h1 className="font-bold text-xl">Upload Data</h1>
          <p className="text-sm text-gray-300">
            High-resolution weather observation data for ward-level forecasts
          </p>
        </div>

        {/* STATUS */}
        {step !== "idle" && step !== "done" && (
          <div
            className={`rounded-lg border p-4 ${
              step === "error"
                ? "bg-red-500/10 border-red-500/30 text-red-700"
                : "bg-blue-500/10 border-blue-500/30 text-blue-700"
            }`}
          >
            <div className="flex items-center gap-3">
              {step === "error"
                ? <AlertTriangle className="w-5 h-5" />
                : <Loader2 className="w-5 h-5 animate-spin" />}
              <p className="font-medium">
                {step === "uploading" ? "Uploading..." : "Saving..."}
              </p>
            </div>
            {error && <p className="text-sm mt-1">{error}</p>}
          </div>
        )}

        {/* SUCCESS */}
        {step === "done" && (
          <div className="rounded-lg border border-green-300 bg-green-50 p-4">
            <div className="flex items-center gap-3">
              <Check className="w-5 h-5 text-green-600" />
              <div>
                <p className="font-medium text-green-800">Data saved successfully!</p>
                <p className="text-sm text-green-700">Redirecting to dashboard…</p>
              </div>
            </div>
          </div>
        )}

        {/* FILE UPLOAD */}
        <FileUploadSection
          title="Weather Observation Data (CSV required)"
          description="Upload high-resolution weather data for accurate ward-level forecasts"
          files={files}
          onFileSelect={handleFileSelect}
          onDeleteFile={deleteUploadedFile}
          accept=".csv"
          uploadRef={uploadRef}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
        />

        {/* SAVE BUTTON */}
        <button
          onClick={handleSave}
          disabled={isSaveDisabled}
          className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 text-white py-3 rounded-lg font-medium flex justify-center gap-2"
        >
          {step === "uploading" ? "Uploading…" : "Save"}
        </button>
      </div>
    </div>
  )
}

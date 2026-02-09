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
  const [step, setStep] = useState<"idle" | "uploading" | "done" | "error">("idle")
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
  // Upload handler
  // ---------------------------
  const handleSave = async () => {
    if (!files.length) return

    try {
      setStep("uploading")
      setError(null)

      for (const file of files) {
        await uploadService.uploadFile(file)
      }

      setStep("done")
      setTimeout(onBack, 2000)
    } catch (err: any) {
      setError(err.message || "Upload failed")
      setStep("error")
    }
  }

  const isUploading = step === "uploading"

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
        {/* HEADER */}
        <div className="bg-black rounded-lg border border-gray-700 p-6 text-white">
          <h1 className="font-bold text-xl">Upload Data</h1>
          <p className="text-sm text-gray-300">
            High-resolution weather observation data for ward-level forecasts
          </p>
        </div>

        {/* FEEDBACK (shared success / error section) */}
        {(step === "done" || step === "error") && (
          <div
            className={`rounded-lg border p-4 ${
              step === "done"
                ? "border-green-300 bg-green-50"
                : "border-red-300 bg-red-50"
            }`}
          >
            <div className="flex items-center gap-3">
              {step === "done" ? (
                <Check className="w-5 h-5 text-green-600" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-red-600" />
              )}

              <div>
                <p
                  className={`font-medium ${
                    step === "done" ? "text-green-800" : "text-red-800"
                  }`}
                >
                  {step === "done"
                    ? "Data saved successfully!"
                    : "Upload failed"}
                </p>

                <p
                  className={`text-sm ${
                    step === "done" ? "text-green-700" : "text-red-700"
                  }`}
                >
                  {step === "done"
                    ? "Redirecting to dashboard…"
                    : error}
                </p>
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
          disabled={isUploading || files.length === 0}
          className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-white py-3 rounded-lg font-medium flex justify-center items-center gap-2"
        >
          {isUploading && <Loader2 className="w-4 h-4 animate-spin" />}
          {isUploading ? "Saving…" : "Save"}
        </button>
      </div>
    </div>
  )
}

"use client"

import { useState, useCallback } from "react"
import { supabase } from "../lib/supabaseClient"
import { UploadedFile as UploadedFileType, SaveStep } from "./types"

const BUCKET_NAME = process.env.NEXT_PUBLIC_SUPABASE_BUCKET || "weather-reports"

export const useFileUpload = () => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFileType[]>([])
  const [saveStep, setSaveStep] = useState<SaveStep>("idle")
  const [saveError, setSaveError] = useState<string>("")

  /** Select files */
  const handleFileSelect = useCallback((files: FileList | null) => {
    if (!files) return
    const newFiles: UploadedFileType[] = Array.from(files)
      .filter((file) => file.name.toLowerCase().endsWith(".csv"))
      .map((file) => ({
        id: Date.now().toString() + Math.random(),
        name: file.name,
        file,
        size: `${(file.size / (1024 * 1024)).toFixed(2)} MB`,
        status: "selected",
        timestamp: new Date(),
        type: "observations",
      }))
    setUploadedFiles((prev) => [...prev, ...newFiles])
  }, [])

  /** Delete file */
  const deleteUploadedFile = useCallback((id: string) => {
    setUploadedFiles((prev) => prev.filter((f) => f.id !== id))
  }, [])

  /** Upload all files */
  const handleSave = useCallback(async (): Promise<boolean> => {
    if (uploadedFiles.length === 0) return false

    setSaveStep("saving")
    setSaveError("")

    try {
      const { data: { session }, error: sessionError } = await supabase.auth.getSession()
      if (sessionError) throw sessionError
      if (!session?.user?.id) throw new Error("Not authenticated")

      const userId = session.user.id

      for (const fileObj of uploadedFiles) {
        const filePath = `users/${userId}/inputs/observations/${fileObj.name}`

        const { error } = await supabase.storage
          .from(BUCKET_NAME)
          .upload(filePath, fileObj.file, { cacheControl: "3600", upsert: true })

        if (error) throw error
      }

      setSaveStep("done")
      return true
    } catch (err: any) {
      console.error("Upload error:", err)
      setSaveStep("error")
      setSaveError(err.message || "Upload failed")
      return false
    }
  }, [uploadedFiles])

  return {
    uploadedFiles,
    saveStep,
    saveError,
    handleFileSelect,
    deleteUploadedFile,
    handleSave,
  }
}

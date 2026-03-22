// frontend/models/upload.ts

export interface UploadData {
  file_name: string
  file_type: "boundaries" | "observations"

  // reporting period (sent to backend)
  report_week: number
  report_year: number
  report_start_at: string // YYYY-MM-DD
  report_end_at: string   // YYYY-MM-DD
}

export interface Upload {
  id: string
  file_name: string
  file_type: string
  status: "pending" | "processing" | "completed" | "failed"

  // ✅ renamed to match backend
  uploaded_at: string // ISO datetime

  // reporting period
  report_week?: number
  report_year?: number
  report_start_at?: string
  report_end_at?: string
}

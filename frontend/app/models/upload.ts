// frontend/models/upload.ts

export interface UploadData {
    file_name: string
    file_type: "boundaries" | "observations"
  }
  
  export interface Upload {
    id: string
    file_name: string
    file_type: string
    status: "pending" | "processing" | "completed" | "failed"
    upload_date: string // ISO date string from backend
  }

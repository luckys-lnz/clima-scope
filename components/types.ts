// components/upload/types.ts
export interface UploadedFile {
    id: string
    name: string
    type: 'boundaries' | 'observations'
    size: string
    timestamp: Date
    file: File
    status: 'selected' | 'validating' | 'valid' | 'invalid' | 'uploading' | 'uploaded' | 'error'
    validationResults?: {
      passed: boolean
      logs: string[]
      details?: any
    }
    error?: string
  }
  
  export type SaveStep = 'idle' | 'validating' | 'uploading' | 'saving' | 'done' | 'error'
  
  export interface ProgressLog {
    id: number
    timestamp: Date
    message: string
    type: 'info' | 'success' | 'error' | 'warning'
    fileId?: string
  }
  
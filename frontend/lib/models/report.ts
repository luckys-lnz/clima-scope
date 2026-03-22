export interface ReportArchiveItem {
    id: string
    county: string
    generatedAt: string
    periodStart: string
    periodEnd: string
    status: "success" | "failed"
    pdfUrl: string
  }
  
export interface ReportArchiveResponse {
    reports: ReportArchiveItem[]
}

export interface ReportDetailResponse {
    report: {
      id: string
      status: string
      generated_at: string
      file_path: string
      pdf_url: string
    }
    observation: {
      id: string
      file_name: string
      file_path?: string
      status: string
      report_week?: number
      report_year?: number
      report_start_at?: string
      report_end_at?: string
    } | null
    observation_summary?: {
      row_count?: number
      column_count?: number
      variables?: Record<string, {
        column?: string | null
        available?: boolean
        numeric?: boolean
        non_null_count?: number
        mean?: number
        min?: number
        max?: number
        sum?: number
      }>
    }
    forecast_summary?: {
      mean_temperature?: number | null
      max_wind_speed?: number | null
      rainfall_sum?: number | null
    }
    ai_narration?: {
      weekly_summary_text?: string
      marine_summary_text?: string
      source?: string
    }
    maps: Array<{
      variable: string
      map_url: string
      created_at: string
    }>
    workflow_logs: Array<{
      stage: string
      status: string
      message: string
      created_at: string
    }>
}

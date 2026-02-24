export interface ReportPeriod {
    start: string
    end: string
}
  
export interface ValidationResponse {
    observation_found: boolean
    shapefile_found: boolean
    variables: string[]
    observation_file: string
    shapefile: string
    report_week: number
    report_year: number
    report_period: ReportPeriod
    column_count: number
    row_count: number
}
  
export interface ValidationError {
    detail: string
}
  
export interface WorkflowStatus {
    id: string
    user_id: string
    report_week: number
    report_year: number
    report_start_at: string
    report_end_at: string
    uploaded: boolean
    validated: boolean
    variables_found: string[]
    maps_generated: boolean
    report_generated: boolean
    completed: boolean
    observation_file_id?: string
    shapefile_id?: string
    generated_report_id?: string
    created_at: string
    updated_at: string
}

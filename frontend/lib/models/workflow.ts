// ============================================
// Report Period Schema
// ============================================
export interface ReportPeriod {
    start: string
    end: string
}

// ============================================
// Validation Schemas
// ============================================
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

// ============================================
// MAP GENERATION SCHEMAS
// ============================================
export interface MapGenerationRequest {
    county: string
    variables: string[]
    report_week: number
    report_year: number
    report_start_at: string
    report_end_at: string
}

export interface MapOutput {
    variable: string
    map_url: string
    thumbnail_url?: string
}

export interface MapGenerationResponse {
    outputs: MapOutput[]
    workflow_status_id?: number
}

// ============================================
// Generated Map Record
// ============================================
export interface GeneratedMap {
    id?: string
    user_id: string
    workflow_status_id: number
    variable: string
    map_url: string
    storage_path: string
    report_week: number
    report_year: number
    file_size?: number
    created_at?: string
}

// ============================================
// Workflow Status Schema
// ============================================
export interface WorkflowStatus {
    id: number  // Changed from string to number to match DB
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

export type WorkflowStep =
  | "uploaded"
  | "aggregated"
  | "mapped"
  | "generated"
  | "completed"
  | null

export interface DashboardStats {
  countiesProcessed: number
  totalCounties: number
  allReportsDone: number
  lastGeneration: string
  userReportsGenerated: number
}

export interface DashboardOverviewData {
  stats: DashboardStats
  workflow_step: WorkflowStep
  current_window: {
    week: number
    year: number
    start: string
    end: string
  }
  workflow_progress: {
    stage: string
    status: "info" | "success" | "error"
    message: string
    created_at: string
  } | null
}

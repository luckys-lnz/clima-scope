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
}

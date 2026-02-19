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

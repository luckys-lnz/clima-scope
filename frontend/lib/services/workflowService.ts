"use client"

import { authService } from "@/lib/services/authService"
import type {
  GeneratedMap,
  MapGenerationRequest,
  MapGenerationResponse,
  ReportPeriod,
  ValidationResponse,
  WorkflowStatus,
} from "@/lib/models/workflow"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface ValidateInputsPayload {
  report_week: number
  report_year: number
  report_start_at: string
  report_end_at: string
}

interface GenerateReportPayload {
  county_name: string
  week_number: number
  year: number
  report_start_at: string
  report_end_at: string
  variables: string[]
}

interface GenerateReportAsyncPayload {
  county_name: string
  week_number: number
  year: number
  report_start_at: string
  report_end_at: string
  variables: string[]
}

interface WorkflowStageStatus {
  stage: string
  status: string
  message: string
  timestamp: string
}

interface GenerateReportResponse {
  pdf_url: string
  filename: string
  report_week: number
  report_year: number
  stage_statuses?: WorkflowStageStatus[]
}

interface CurrentReportWindowResponse {
  week: number
  year: number
  period: ReportPeriod
}

interface ApiErrorBody {
  detail?: string
  message?: string
}

const getResponseErrorMessage = async (
  response: Response,
  fallback: string,
): Promise<string> => {
  const error = await response.json().catch(
    () => null as ApiErrorBody | null,
  )
  return error?.detail || error?.message || fallback
}

export const workflowService = {
  validateInputs: async (
    token: string,
    data: ValidateInputsPayload,
  ): Promise<ValidationResponse> => {
    return authService.requestJsonWithAuth<ValidationResponse, ValidateInputsPayload>(
      `${API_BASE}/api/v1/workflow/validate-inputs`,
      {
        method: "POST",
        token,
        body: data,
      },
    )
  },

  generateMaps: async (
    token: string,
    data: MapGenerationRequest,
  ): Promise<MapGenerationResponse> => {
    return authService.requestJsonWithAuth<MapGenerationResponse, MapGenerationRequest>(
      `${API_BASE}/api/v1/workflow/generate-maps`,
      {
        method: "POST",
        token,
        body: data,
      },
    )
  },

  getGeneratedMaps: async (
    token: string,
    reportWeek: number,
    reportYear: number,
  ): Promise<GeneratedMap[]> => {
    return authService.requestJsonWithAuth<GeneratedMap[]>(
      `${API_BASE}/api/v1/workflow/maps?week=${reportWeek}&year=${reportYear}`,
      {
        method: "GET",
        token,
      },
    )
  },

  getMapByVariable: async (
    token: string,
    variable: string,
    reportWeek: number,
    reportYear: number,
  ): Promise<GeneratedMap | null> => {
    const response = await authService.fetchWithAuth(
      `${API_BASE}/api/v1/workflow/maps/${variable}?week=${reportWeek}&year=${reportYear}`,
      {
        method: "GET",
        token,
      },
    )

    if (response.status === 404) {
      return null
    }

    if (!response.ok) {
      throw new Error(await getResponseErrorMessage(response, "Failed to fetch map"))
    }

    return (await response.json()) as GeneratedMap
  },

  getWorkflowStatus: async (
    token: string,
    reportWeek?: number,
    reportYear?: number,
  ): Promise<WorkflowStatus | null> => {
    let url = `${API_BASE}/api/v1/workflow/status`
    if (typeof reportWeek === "number" && typeof reportYear === "number") {
      url += `?week=${reportWeek}&year=${reportYear}`
    }

    const response = await authService.fetchWithAuth(url, {
      method: "GET",
      token,
    })

    if (response.status === 404) {
      return null
    }

    if (!response.ok) {
      throw new Error(
        await getResponseErrorMessage(response, "Failed to fetch workflow status"),
      )
    }

    return (await response.json()) as WorkflowStatus
  },

  updateWorkflowStatus: async (
    token: string,
    reportWeek: number,
    reportYear: number,
    updates: Partial<WorkflowStatus>,
  ): Promise<WorkflowStatus> => {
    return authService.requestJsonWithAuth<WorkflowStatus, Partial<WorkflowStatus>>(
      `${API_BASE}/api/v1/workflow/status?week=${reportWeek}&year=${reportYear}`,
      {
        method: "PATCH",
        token,
        body: updates,
      },
    )
  },

  getCurrentReportWindow: async (
    token: string,
  ): Promise<CurrentReportWindowResponse> => {
    return authService.requestJsonWithAuth<CurrentReportWindowResponse>(
      `${API_BASE}/api/v1/workflow/current-window`,
      {
        method: "GET",
        token,
      },
    )
  },

  generateReport: async (
    token: string,
    data: GenerateReportPayload,
  ): Promise<GenerateReportResponse> => {
    return authService.requestJsonWithAuth<GenerateReportResponse, GenerateReportPayload>(
      `${API_BASE}/api/v1/workflow/generate-report`,
      {
        method: "POST",
        token,
        body: data,
      },
    )
  },

  /**
   * Step 4 (Async): Start final PDF report generation in background
   */
  generateReportAsync: async (
    token: string,
    data: GenerateReportAsyncPayload,
  ): Promise<{
    accepted: boolean
    workflow_status_id?: number
    report_week: number
    report_year: number
    message: string
  }> => {
    return authService.requestJsonWithAuth<
      {
        accepted: boolean
        workflow_status_id?: number
        report_week: number
        report_year: number
        message: string
      },
      GenerateReportAsyncPayload
    >(
      `${API_BASE}/api/v1/workflow/generate-report-async`,
      {
        method: "POST",
        token,
        body: data,
      },
    )
  }
}

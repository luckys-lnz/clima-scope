"use client"

import type { 
  ValidationResponse, 
  ValidationError,
  WorkflowStatus,
  ReportPeriod,
  MapGenerationRequest,
  MapGenerationResponse,
  GeneratedMap
} from "@/lib/models/workflow"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

// ============================================
// Service
// ============================================
export const workflowService = {
  /**
   * Step 1: Validate inputs for current reporting period
   * Checks if observation file exists for current week and validates shapefile
   */
  validateInputs: async (
    token: string, 
    data: { 
      report_week: number; 
      report_year: number; 
      report_start_at: string; 
      report_end_at: string;
    }
  ): Promise<ValidationResponse> => {
    const response = await fetch(`${API_BASE}/api/v1/workflow/validate-inputs`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    })

    const responseData = await response.json()
    
    if (!response.ok) {
      const error = responseData as ValidationError
      throw new Error(error.detail || "Validation failed")
    }

    return responseData as ValidationResponse
  },

  /**
   * Step 3: Generate maps for selected variables
   * Creates maps for each variable and returns URLs
   */
  generateMaps: async (
    token: string,
    data: MapGenerationRequest
  ): Promise<MapGenerationResponse> => {
    const response = await fetch(`${API_BASE}/api/v1/workflow/generate-maps`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    })

    const responseData = await response.json()
    
    if (!response.ok) {
      const error = responseData as ValidationError
      throw new Error(error.detail || "Map generation failed")
    }

    return responseData as MapGenerationResponse
  },

  /**
   * Get all generated maps for a specific week
   * Returns list of maps created for this reporting period
   */
  getGeneratedMaps: async (
    token: string,
    reportWeek: number,
    reportYear: number
  ): Promise<GeneratedMap[]> => {
    const response = await fetch(
      `${API_BASE}/api/v1/workflow/maps?week=${reportWeek}&year=${reportYear}`,
      {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || "Failed to fetch maps")
    }

    return response.json()
  },

  /**
   * Get a specific map by variable and week
   * Useful for checking if a map already exists
   */
  getMapByVariable: async (
    token: string,
    variable: string,
    reportWeek: number,
    reportYear: number
  ): Promise<GeneratedMap | null> => {
    const response = await fetch(
      `${API_BASE}/api/v1/workflow/maps/${variable}?week=${reportWeek}&year=${reportYear}`,
      {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      }
    )

    if (response.status === 404) {
      return null
    }

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || "Failed to fetch map")
    }

    return response.json()
  },

  /**
   * Get current workflow status for the user and specific week
   */
  getWorkflowStatus: async (
    token: string,
    reportWeek?: number,
    reportYear?: number
  ): Promise<WorkflowStatus | null> => {
    let url = `${API_BASE}/api/v1/workflow/status`
    
    if (reportWeek && reportYear) {
      url += `?week=${reportWeek}&year=${reportYear}`
    }
    
    const response = await fetch(url, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    })

    if (!response.ok) {
      if (response.status === 404) {
        return null
      }
      const error = await response.json()
      throw new Error(error.detail || "Failed to fetch workflow status")
    }

    return response.json()
  },

  /**
   * Update workflow status (mark steps as complete)
   */
  updateWorkflowStatus: async (
    token: string,
    reportWeek: number,
    reportYear: number,
    updates: Partial<WorkflowStatus>
  ): Promise<WorkflowStatus> => {
    const response = await fetch(
      `${API_BASE}/api/v1/workflow/status?week=${reportWeek}&year=${reportYear}`,
      {
        method: "PATCH",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify(updates)
      }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || "Failed to update workflow status")
    }

    return response.json()
  },

  /**
   * Get the current report window info
   */
  getCurrentReportWindow: async (token: string): Promise<{
    week: number
    year: number
    period: ReportPeriod
  }> => {
    const response = await fetch(`${API_BASE}/api/v1/workflow/current-window`, {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || "Failed to fetch report window")
    }

    return response.json()
  },

  /**
   * Step 4: Generate final PDF report
   */
  generateReport: async (
    token: string,
    data: {
      county_name: string
      week_number: number
      year: number
      report_start_at: string
      report_end_at: string
      variables: string[]
    }
  ): Promise<{
    pdf_url: string
    filename: string
    report_week: number
    report_year: number
    stage_statuses?: Array<{
      stage: string
      status: string
      message: string
      timestamp: string
    }>
  }> => {
    const response = await fetch(`${API_BASE}/api/v1/workflow/generate-report`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    })

    const responseData = await response.json()
    
    if (!response.ok) {
      const error = responseData as ValidationError
      throw new Error(error.detail || "Report generation failed")
    }

    return responseData
  },

  /**
   * Step 4 (Async): Start final PDF report generation in background
   */
  generateReportAsync: async (
    token: string,
    data: {
      county_name: string
      week_number: number
      year: number
      report_start_at: string
      report_end_at: string
      variables: string[]
    }
  ): Promise<{
    accepted: boolean
    workflow_status_id?: number
    report_week: number
    report_year: number
    message: string
  }> => {
    const response = await fetch(`${API_BASE}/api/v1/workflow/generate-report-async`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    })

    const responseData = await response.json()

    if (!response.ok) {
      const error = responseData as ValidationError
      throw new Error(error.detail || "Failed to start background report generation")
    }

    return responseData
  }
}

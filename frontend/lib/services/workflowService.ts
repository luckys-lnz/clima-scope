"use client"

import type { 
  ValidationResponse, 
  ValidationError,
  WorkflowStatus,
  ReportPeriod 
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
      // ✅ FIXED: Send the data in the request body
      body: JSON.stringify(data)
    })

    const responseData = await response.json()
    
    if (!response.ok) {
      // Type assertion for error response
      const error = responseData as ValidationError
      throw new Error(error.detail || "Validation failed")
    }

    return responseData as ValidationResponse
  },

  /**
   * Get current workflow status for the user
   */
  getWorkflowStatus: async (token: string): Promise<WorkflowStatus | null> => {
    const response = await fetch(`${API_BASE}/api/v1/workflow/status`, {
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
  }
}

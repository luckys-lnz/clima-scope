"use client"

import { DashboardService } from "@/lib/services/dashboardService"
import { ReportService } from "@/lib/services/reportService"
import { SettingsService } from "@/lib/services/settingService"

const DASHBOARD_CACHE_KEY = "dashboard_overview_cache_v1"
const REPORTS_CACHE_KEY = "report_archive_cache_v1"
const SETTINGS_CACHE_KEY = "system_settings_cache"
const SETTINGS_CACHE_VERSION = 2

export const bootstrapService = {
  primeDashboardData: async (token: string): Promise<void> => {
    const tasks = [
      DashboardService.getOverview(token).then((data) => {
        sessionStorage.setItem(DASHBOARD_CACHE_KEY, JSON.stringify(data))
      }),
      ReportService.getReports(token).then((data) => {
        sessionStorage.setItem(REPORTS_CACHE_KEY, JSON.stringify(data))
      }),
      SettingsService.getSettings(token).then((data) => {
        const settingsData = {
          version: SETTINGS_CACHE_VERSION,
          shapefilePath: data.shapefile_path || "",
          templates: data.templates || [],
          selectedTemplateId: data.user_settings?.pdf_template_id || null,
        }
        sessionStorage.setItem(SETTINGS_CACHE_KEY, JSON.stringify(settingsData))
      }),
    ]

    await Promise.allSettled(tasks)
  },
}

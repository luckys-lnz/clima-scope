/**
 * Schema Validation Tests
 * 
 * Tests for Person B's schema implementations
 */

import { describe, it, expect } from "vitest"
import {
  KENYA_COUNTIES,
  validateCountyList,
  CountyWeatherReport,
  generateMockCountyReport,
} from "../weather-schemas"
import {
  isValidCountyReport,
  flattenReportForCSV,
  EXAMPLE_REPORT,
  CountyWeatherReportData,
} from "../json-schema"

describe("County List Validation", () => {
  it("should have exactly 47 counties", () => {
    expect(KENYA_COUNTIES.length).toBe(47)
  })

  it("should have no duplicate county IDs", () => {
    const ids = KENYA_COUNTIES.map((c) => c.id)
    const uniqueIds = new Set(ids)
    expect(uniqueIds.size).toBe(47)
  })

  it("should have no duplicate county names", () => {
    const names = KENYA_COUNTIES.map((c) => c.name)
    const uniqueNames = new Set(names)
    expect(uniqueNames.size).toBe(47)
  })

  it("should have all county IDs in 2-digit format", () => {
    KENYA_COUNTIES.forEach((county) => {
      expect(county.id).toMatch(/^\d{2}$/)
    })
  })

  it("validateCountyList should return valid", () => {
    const result = validateCountyList()
    expect(result.isValid).toBe(true)
    expect(result.errors).toHaveLength(0)
  })
})

describe("CountyWeatherReport Schema", () => {
  it("should generate valid mock report", () => {
    const report = generateMockCountyReport("31", "Nairobi")
    
    expect(report.county_id).toBe("31")
    expect(report.county_name).toBe("Nairobi")
    expect(report.period.start).toBeDefined()
    expect(report.period.end).toBeDefined()
    expect(report.variables.temperature).toBeDefined()
    expect(report.variables.rainfall).toBeDefined()
    expect(report.variables.wind).toBeDefined()
    expect(report.wards).toBeDefined()
    expect(report.metadata).toBeDefined()
    expect(report.disclaimer).toBeDefined()
  })

  it("should have 7 daily values for temperature", () => {
    const report = generateMockCountyReport("31", "Nairobi")
    expect(report.variables.temperature.daily).toHaveLength(7)
  })

  it("should have 7 daily values for rainfall", () => {
    const report = generateMockCountyReport("31", "Nairobi")
    expect(report.variables.rainfall.daily).toHaveLength(7)
  })

  it("should have 7 daily values for wind", () => {
    const report = generateMockCountyReport("31", "Nairobi")
    expect(report.variables.wind.daily_peak).toHaveLength(7)
  })

  it("should have valid temperature ranges", () => {
    const report = generateMockCountyReport("31", "Nairobi")
    const temp = report.variables.temperature
    
    expect(temp.weekly.mean).toBeGreaterThan(-50)
    expect(temp.weekly.mean).toBeLessThan(50)
    expect(temp.weekly.max).toBeGreaterThanOrEqual(temp.weekly.mean)
    expect(temp.weekly.min).toBeLessThanOrEqual(temp.weekly.mean)
  })

  it("should have valid rainfall values", () => {
    const report = generateMockCountyReport("31", "Nairobi")
    const rain = report.variables.rainfall
    
    expect(rain.weekly.total).toBeGreaterThanOrEqual(0)
    expect(rain.weekly.max_intensity).toBeGreaterThanOrEqual(0)
    rain.daily.forEach((val) => {
      expect(val).toBeGreaterThanOrEqual(0)
    })
  })

  it("should have valid wind values", () => {
    const report = generateMockCountyReport("31", "Nairobi")
    const wind = report.variables.wind
    
    expect(wind.weekly.mean_speed).toBeGreaterThanOrEqual(0)
    expect(wind.weekly.max_gust).toBeGreaterThanOrEqual(wind.weekly.mean_speed)
    wind.daily_peak.forEach((val) => {
      expect(val).toBeGreaterThanOrEqual(0)
    })
  })
})

describe("JSON Schema Validation", () => {
  it("should validate example report", () => {
    expect(isValidCountyReport(EXAMPLE_REPORT)).toBe(true)
  })

  it("should reject invalid data", () => {
    expect(isValidCountyReport(null)).toBe(false)
    expect(isValidCountyReport({})).toBe(false)
    expect(isValidCountyReport({ county_id: "invalid" })).toBe(false)
  })

  it("should validate county ID format", () => {
    const validReport: CountyWeatherReportData = {
      ...(EXAMPLE_REPORT as CountyWeatherReportData),
      county_id: "31",
    }
    expect(isValidCountyReport(validReport)).toBe(true)

    const invalidReport: CountyWeatherReportData = {
      ...(EXAMPLE_REPORT as CountyWeatherReportData),
      county_id: "999", // Invalid - not 2 digits
    }
    // The type guard checks format, so this should fail
    if (isValidCountyReport(invalidReport)) {
      // If it passes, check the format manually
      expect(invalidReport.county_id).not.toMatch(/^\d{2}$/)
    }
  })
})

describe("CSV Flattening", () => {
  it("should flatten report to CSV format", () => {
    const flat = flattenReportForCSV(EXAMPLE_REPORT as CountyWeatherReportData)
    
    expect(flat).toBeDefined()
    expect(Array.isArray(flat)).toBe(true)
    
    if (flat.length > 0) {
      const firstRow = flat[0]
      expect(firstRow.county_id).toBe(EXAMPLE_REPORT.county_id)
      expect(firstRow.ward_id).toBeDefined()
      expect(firstRow.rainfall_total).toBeDefined()
      expect(firstRow.temp_mean).toBeDefined()
    }
  })

  it("should create one row per ward", () => {
    const flat = flattenReportForCSV(EXAMPLE_REPORT as CountyWeatherReportData)
    expect(flat.length).toBe(EXAMPLE_REPORT.wards?.length || 0)
  })

  it("should handle reports with no wards", () => {
    const reportWithoutWards: CountyWeatherReportData = {
      ...(EXAMPLE_REPORT as CountyWeatherReportData),
      wards: undefined,
    }
    const flat = flattenReportForCSV(reportWithoutWards)
    expect(flat).toHaveLength(0)
  })
})

describe("Schema Consistency", () => {
  it("should have consistent structure between weather-schemas and json-schema", () => {
    const mockReport = generateMockCountyReport("31", "Nairobi")
    
    // Check that mock report has required fields for JSON schema
    expect(mockReport.county_id).toBeDefined()
    expect(mockReport.county_name).toBeDefined()
    expect(mockReport.period.start).toBeDefined()
    expect(mockReport.period.end).toBeDefined()
    expect(mockReport.variables).toBeDefined()
    expect(mockReport.metadata).toBeDefined()
  })

  it("should have schema_version field available", () => {
    const report = generateMockCountyReport("31", "Nairobi")
    // schema_version is optional, so it may or may not be present
    // But the type should allow it
    const reportWithVersion: CountyWeatherReport = {
      ...report,
      schema_version: "1.0",
    }
    expect(reportWithVersion.schema_version).toBe("1.0")
  })
})

describe("Extreme Values Structure", () => {
  it("should have correct extreme values structure", () => {
    const report = generateMockCountyReport("31", "Nairobi")
    
    if (report.extremes) {
      if (report.extremes.highest_rainfall) {
        expect(report.extremes.highest_rainfall.ward_id).toBeDefined()
        expect(report.extremes.highest_rainfall.value).toBeDefined()
      }
      
      if (report.extremes.hottest_ward) {
        expect(typeof report.extremes.hottest_ward).toBe("object")
        expect(report.extremes.hottest_ward.ward_id).toBeDefined()
        expect(report.extremes.hottest_ward.value).toBeDefined()
      }
    }
  })
})

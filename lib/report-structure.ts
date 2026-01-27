/**
 * Report Structure Type Definitions
 * Based on REPORT_STRUCTURE_SPECIFICATION.md
 * 
 * This file defines the TypeScript interfaces for the complete report structure
 * as specified in the report structure specification document.
 * 
 * @author Person B
 * @version 1.0
 */

import type { CountyWeatherReport, Metadata } from "./weather-schemas"

/**
 * Cover Page Information
 */
export interface CoverPageInfo {
  reportTitle: string // "Weekly Weather Outlook for [County Name] County"
  reportPeriod: {
    weekNumber: number
    year: number
    startDate: string // ISO date format
    endDate: string // ISO date format
    formatted: string // "Week 50, 2024 (December 2 - December 8, 2024)"
  }
  county: {
    name: string
    code: string // KNBS code
    region?: string
  }
  generationMetadata: {
    generatedAt: string // ISO timestamp
    modelRunTimestamp: string // ISO timestamp
    dataSource: string // "GFS v15.1"
    systemVersion: string
  }
  disclaimer: string
}

/**
 * Executive Summary Section
 */
export interface ExecutiveSummary {
  summaryStatistics: {
    totalRainfall: number // mm
    meanTemperature: number // °C
    temperatureRange: {
      min: number // °C
      max: number // °C
    }
    maxWindSpeed: number // km/h
    dominantWindDirection: string
  }
  keyHighlights: string[] // 3-5 bullet points
  weatherPatternSummary: string // 3-4 sentence paragraph
}

/**
 * Weekly Narrative Summary Section
 */
export interface WeeklyNarrative {
  openingParagraph: string
  temporalBreakdown: {
    earlyWeek: string // Days 1-2
    midWeek: string // Days 3-4
    lateWeek: string // Days 5-7
  }
  variableSpecificDetails: {
    rainfall: string
    temperature: string
    wind: string
    humidity?: string
  }
  spatialVariations: string
}

/**
 * Rainfall Outlook Section
 */
export interface RainfallOutlook {
  countyLevelSummary: {
    totalWeeklyRainfall: number // mm
    dailyBreakdown: Array<{
      day: string
      date: string
      rainfall: number // mm
    }>
    maxDailyIntensity: number // mm
    numberOfRainyDays: number
    probabilityAboveNormal?: number // percentage
  }
  wardLevelAnalysis: Array<{
    wardId: string
    wardName: string
    totalRainfall: number // mm
    numberOfRainyDays: number
    peakIntensityDay: string
  }>
  topWardsByRainfall: Array<{
    wardId: string
    wardName: string
    totalRainfall: number
  }>
  floodRiskWards: string[] // ward IDs
  rainfallDistributionMap: {
    imagePath: string
    colorScale: Array<{
      range: string // "0-20mm"
      color: string
    }>
  }
  temporalPatterns: {
    dailyChart: {
      data: Array<{
        day: string
        rainfall: number
      }>
    }
    peakRainfallDays: string[]
    dryPeriods: Array<{
      start: string
      end: string
    }>
  }
  narrativeDescription: string // 2-3 paragraphs
}

/**
 * Temperature Outlook Section
 */
export interface TemperatureOutlook {
  countyLevelSummary: {
    meanWeeklyTemperature: number // °C
    maximumTemperature: {
      value: number // °C
      day: string
    }
    minimumTemperature: {
      value: number // °C
      day: string
    }
    temperatureRange: number // max - min
    dailyMeanTemperatures: Array<{
      day: string
      mean: number // °C
    }>
  }
  wardLevelAnalysis: Array<{
    wardId: string
    wardName: string
    meanTemperature: number // °C
    maxTemperature: number // °C
    minTemperature: number // °C
  }>
  hottestWard: {
    wardId: string
    wardName: string
    temperature: number
  }
  coolestWard: {
    wardId: string
    wardName: string
    temperature: number
  }
  temperatureDistributionMap: {
    imagePath: string
    colorScale: Array<{
      range: string // "<18°C"
      color: string
    }>
  }
  diurnalPatterns: {
    daytimeHighs: Array<{
      day: string
      high: number // °C
    }>
    nighttimeLows: Array<{
      day: string
      low: number // °C
    }>
  }
  narrativeDescription: string // 2-3 paragraphs
}

/**
 * Wind Outlook Section
 */
export interface WindOutlook {
  countyLevelSummary: {
    meanWindSpeed: number // km/h
    maximumGust: {
      value: number // km/h
      day: string
    }
    dominantWindDirection: string
    dailyPeakWindSpeeds: Array<{
      day: string
      speed: number // km/h
    }>
  }
  wardLevelAnalysis: Array<{
    wardId: string
    wardName: string
    meanWindSpeed: number // km/h
    maxGust: number // km/h
    dominantDirection: string
  }>
  highestWindSpeedWards: Array<{
    wardId: string
    wardName: string
    maxGust: number
  }>
  windSpeedDistributionMap: {
    imagePath: string
    colorScale: Array<{
      range: string // "0-10 km/h"
      color: string
    }>
  }
  windDirectionAnalysis?: {
    windRose?: {
      data: Array<{
        direction: string
        frequency: number
        averageSpeed: number
      }>
    }
    directionFrequency: Array<{
      direction: string
      frequency: number
    }>
  }
  narrativeDescription: string // 2-3 paragraphs
}

/**
 * Ward-Level Visualizations Section
 */
export interface WardLevelVisualizations {
  rainfallMap: {
    imagePath: string
    title: string
    resolution: string // "300 DPI"
    projection: string // "UTM Zone 37N, EPSG:32637"
  }
  temperatureMap: {
    imagePath: string
    title: string
    resolution: string
    projection: string
  }
  windSpeedMap: {
    imagePath: string
    title: string
    resolution: string
    projection: string
  }
}

/**
 * Extreme Values and Highlights Section
 */
export interface ExtremeValues {
  extremeEvents: {
    highestSingleDayRainfall: {
      wardId: string
      wardName: string
      value: number // mm
      date: string
    }
    highestWeeklyRainfall: {
      wardId: string
      wardName: string
      total: number // mm
    }
    hottestDay: {
      wardId: string
      wardName: string
      temperature: number // °C
      date: string
    }
    coolestNight: {
      wardId: string
      wardName: string
      temperature: number // °C
      date: string
    }
    strongestWindGust: {
      wardId: string
      wardName: string
      speed: number // km/h
      date: string
    }
  }
  riskIndicators: {
    floodRiskWards: Array<{
      wardId: string
      wardName: string
      riskLevel: "low" | "moderate" | "high"
      reason: string
    }>
    heatStressWarnings?: Array<{
      wardId: string
      wardName: string
      warningLevel: string
    }>
    windAdvisories?: Array<{
      wardId: string
      wardName: string
      advisoryLevel: string
    }>
  }
  notablePatterns: string[]
}

/**
 * Impacts and Advisories Section
 */
export interface ImpactsAndAdvisories {
  agriculturalAdvisories: {
    rainfallImpact: string
    temperatureEffects: string
    optimalTiming: string
  }
  waterResources: {
    rainfallContribution: string
    reservoirImplications?: string
  }
  healthAdvisories?: {
    heatRelatedWarnings?: string[]
    vectorBorneDiseaseRisk?: string
  }
  generalPublicAdvisories: {
    travelConditions: string
    outdoorActivityRecommendations: string
    safetyPrecautions: string
  }
  sectorSpecificGuidance: {
    energy?: string
    construction?: string
    tourism?: string
  }
}

/**
 * Data Sources and Methodology Section
 */
export interface DataSourcesAndMethodology {
  forecastModel: {
    name: string // "GFS"
    version: string // "v15.1"
    runDate: string // ISO timestamp
    forecastHorizon: number // days
    gridResolution: string // "0.25°"
  }
  dataProcessing: {
    aggregationMethod: "point-in-polygon" | "area-weighted"
    numberOfGridPoints: number
    spatialInterpolation: string
    qualityControlMeasures: string[]
  }
  observationalData?: {
    source: string
    stationLocations: Array<{
      stationId: string
      name: string
      coordinates: {
        lat: number
        lon: number
      }
    }>
    integrationMethod: string
    lastUpdateTimestamp: string
  }
  shapefileSources: {
    countyBoundaries: {
      source: string // "KNBS", "HDX", etc.
      version: string
      date: string
    }
    wardBoundaries: {
      source: string
      version: string
      date: string
    }
    coordinateReferenceSystem: string // "EPSG:4326" or "EPSG:32637"
  }
  limitationsAndUncertainties: {
    modelUncertainty: string
    spatialAggregationLimitations: string
    temporalResolutionConstraints: string
    wardLevelForecastAccuracy: string
  }
}

/**
 * Metadata and Disclaimers Section
 */
export interface MetadataAndDisclaimers {
  generationMetadata: {
    reportGenerationTimestamp: string // ISO timestamp
    systemVersion: string
    processingDuration?: number // seconds
    dataQualityFlags: string[]
    warnings: string[]
  }
  disclaimerStatement: string
  copyrightAndAttribution: {
    dataSourceAttribution: string // "NOAA/NCEP for GFS"
    systemAttribution: string
    usageRights: string
  }
  contactInformation: {
    meteorologicalDepartment?: {
      name: string
      contact: string
    }
    technicalSupport: {
      contact: string
    }
    reportFeedback: {
      mechanism: string
    }
  }
}

/**
 * Complete Report Structure
 * 
 * This interface represents the complete report as specified in
 * REPORT_STRUCTURE_SPECIFICATION.md
 */
export interface CompleteWeatherReport {
  // Section 1: Cover Page
  coverPage: CoverPageInfo

  // Section 2: Executive Summary
  executiveSummary: ExecutiveSummary

  // Section 3: Weekly Narrative Summary
  weeklyNarrative: WeeklyNarrative

  // Section 4: Rainfall Outlook
  rainfallOutlook: RainfallOutlook

  // Section 5: Temperature Outlook
  temperatureOutlook: TemperatureOutlook

  // Section 6: Wind Outlook
  windOutlook: WindOutlook

  // Section 7: Ward-Level Visualizations
  wardLevelVisualizations: WardLevelVisualizations

  // Section 8: Extreme Values and Highlights
  extremeValues: ExtremeValues

  // Section 9: Impacts and Advisories
  impactsAndAdvisories: ImpactsAndAdvisories

  // Section 10: Data Sources and Methodology
  dataSourcesAndMethodology: DataSourcesAndMethodology

  // Section 11: Metadata and Disclaimers
  metadataAndDisclaimers: MetadataAndDisclaimers

  // Raw data reference (for processing)
  rawData: CountyWeatherReport
}

/**
 * Report Generation Configuration
 */
export interface ReportGenerationConfig {
  includeObservations: boolean
  includeHistoricalComparison: boolean
  includeExtendedOutlook: boolean
  language: "en" | "sw" // English or Swahili
  pageSize: "A4" | "Letter"
  mapResolution: number // DPI
  colorScheme: "standard" | "colorblind-friendly"
}

/**
 * Helper function to validate report structure completeness
 */
export function validateReportStructure(report: CompleteWeatherReport): {
  isValid: boolean
  missingSections: string[]
  errors: string[]
} {
  const missingSections: string[] = []
  const errors: string[] = []

  // Check all required sections exist
  if (!report.coverPage) missingSections.push("Cover Page")
  if (!report.executiveSummary) missingSections.push("Executive Summary")
  if (!report.weeklyNarrative) missingSections.push("Weekly Narrative")
  if (!report.rainfallOutlook) missingSections.push("Rainfall Outlook")
  if (!report.temperatureOutlook) missingSections.push("Temperature Outlook")
  if (!report.windOutlook) missingSections.push("Wind Outlook")
  if (!report.wardLevelVisualizations) missingSections.push("Ward-Level Visualizations")
  if (!report.extremeValues) missingSections.push("Extreme Values")
  if (!report.impactsAndAdvisories) missingSections.push("Impacts and Advisories")
  if (!report.dataSourcesAndMethodology) missingSections.push("Data Sources and Methodology")
  if (!report.metadataAndDisclaimers) missingSections.push("Metadata and Disclaimers")

  // Validate cover page
  if (report.coverPage && !report.coverPage.reportTitle) {
    errors.push("Cover page missing report title")
  }

  // Validate executive summary statistics
  if (report.executiveSummary) {
    const stats = report.executiveSummary.summaryStatistics
    if (stats.totalRainfall < 0) errors.push("Invalid total rainfall value")
    if (stats.meanTemperature < -10 || stats.meanTemperature > 50) {
      errors.push("Mean temperature out of reasonable range for Kenya")
    }
  }

  return {
    isValid: missingSections.length === 0 && errors.length === 0,
    missingSections,
    errors,
  }
}

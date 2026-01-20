/**
 * Data Interfaces & Schemas
 * 
 * Comprehensive type definitions for the Automated Weekly County Weather Reporting system.
 * Defines how data flows through the system: Input → Processing → Output
 * 
 * @author Person B
 * @version 1.0
 * 
 * Based on:
 * - GFS GRIB file structure
 * - Kenya administrative boundaries (KNBS)
 * - Optional observational data (KMD)
 * - Processing pipeline requirements
 * - Report generation specifications
 */

// ============================================================================
// INPUT SCHEMAS - Raw Data from External Sources
// ============================================================================

/**
 * GFS GRIB File Interface
 * 
 * Represents a GFS (Global Forecast System) GRIB2 file loaded into xarray Dataset.
 * GRIB files contain gridded forecast data at 0.25° resolution.
 */
export interface GFSGribFile {
  /** File path or identifier */
  filePath: string
  /** Model run timestamp (UTC) - e.g., "2026-01-14T00:00:00Z" */
  modelRun: string
  /** Forecast hours from model run (0, 3, 6, ..., 168 for 7 days) */
  forecastHours: number[]
  /** GRIB variables extracted from the file */
  variables: GFSVariables
  /** Grid metadata */
  grid: GFSGridMetadata
  /** File metadata */
  metadata: GFSFileMetadata
}

/**
 * GFS Variables Dictionary
 * 
 * Maps GRIB parameter names to their data arrays and metadata.
 */
export interface GFSVariables {
  /** Total precipitation (apcpsfc) - accumulated surface precipitation */
  total_precipitation: GFSVariableData
  /** 2-meter temperature (t2m) */
  t2m: GFSVariableData
  /** 10-meter U-wind component (u10m) */
  u10m: GFSVariableData
  /** 10-meter V-wind component (v10m) */
  v10m: GFSVariableData
  /** Optional: 2-meter relative humidity */
  rh2m?: GFSVariableData
  /** Optional: Surface pressure */
  sp?: GFSVariableData
}

/**
 * Individual GFS Variable Data
 */
export interface GFSVariableData {
  /** Units of measurement */
  units: string
  /** Vertical levels (usually ["surface"] for surface variables) */
  levels: string[]
  /** Time steps (ISO datetime strings) */
  times: string[]
  /** 
   * Data array structure
   * In Python: xarray.DataArray with dimensions [lat, lon, time]
   * In TypeScript: Represented as structured data
   */
  data: GFSDataArray
  /** GRIB parameter code */
  paramCode?: string
  /** Long name/description */
  longName?: string
}

/**
 * GFS Data Array Structure
 * 
 * Represents the gridded data from xarray DataArray.
 * Dimensions: [latitude, longitude, time]
 */
export interface GFSDataArray {
  /** Latitude values (degrees, -90 to 90) */
  latitudes: number[]
  /** Longitude values (degrees, -180 to 180) */
  longitudes: number[]
  /** Time steps (ISO datetime strings) */
  times: string[]
  /** 
   * 3D data array: [time][lat][lon]
   * Values are stored as flat array with indexing: time * lat_len * lon_len + lat * lon_len + lon
   */
  values: number[]
  /** Missing data indicator */
  fillValue?: number
  /** Data validity mask (true = valid, false = missing) */
  validMask?: boolean[]
}

/**
 * GFS Grid Metadata
 */
export interface GFSGridMetadata {
  /** Grid resolution in degrees */
  resolution: number // e.g., 0.25
  /** Grid type */
  gridType: "regular_ll" | "rotated_ll" | "lambert" | "mercator"
  /** Bounding box */
  bbox: {
    north: number
    south: number
    east: number
    west: number
  }
  /** Number of grid points */
  gridPoints: {
    lat: number
    lon: number
  }
}

/**
 * GFS File Metadata
 */
export interface GFSFileMetadata {
  /** Model version */
  modelVersion: string // e.g., "GFS v15.1"
  /** Center that produced the data */
  center: string // e.g., "NCEP"
  /** Sub-center */
  subCenter?: string
  /** File size in bytes */
  fileSize: number
  /** Download timestamp */
  downloadedAt: string
}

// ============================================================================
// ADMINISTRATIVE BOUNDARIES SCHEMAS
// ============================================================================

/**
 * Administrative Boundary Interface
 * 
 * Represents county and ward boundaries from shapefiles.
 * Compatible with GeoPandas GeoDataFrame structure.
 */
export interface AdminBoundary {
  /** County KNBS code (e.g., "31" for Nairobi) */
  countyId: string
  /** County official name */
  countyName: string
  /** County geometry (WGS84, EPSG:4326) */
  countyGeometry: Geometry
  /** Wards within the county */
  wards: WardBoundary[]
  /** Metadata */
  metadata: BoundaryMetadata
}

/**
 * Ward Boundary
 */
export interface WardBoundary {
  /** Ward identifier (unique within county) */
  wardId: string
  /** Ward official name */
  wardName: string
  /** Ward geometry (Polygon or MultiPolygon) */
  geometry: Geometry
  /** County ID this ward belongs to */
  countyId: string
  /** Optional: Ward area in square kilometers */
  areaKm2?: number
}

/**
 * Geometry Interface
 * 
 * Represents GeoJSON-compatible geometry.
 * In Python: shapely.Polygon or shapely.MultiPolygon
 */
export interface Geometry {
  /** Geometry type */
  type: "Polygon" | "MultiPolygon"
  /** Coordinates array */
  coordinates: number[][][] | number[][][][]
  /** Coordinate Reference System */
  crs: {
    type: "name"
    properties: {
      name: string // e.g., "EPSG:4326"
    }
  }
}

/**
 * Boundary Metadata
 */
export interface BoundaryMetadata {
  /** Data source (e.g., "KNBS", "HDX", "OpenAfrica") */
  source: string
  /** Version or date of boundary data */
  version: string
  /** Download/update date */
  updatedAt: string
  /** Coordinate Reference System */
  crs: string // e.g., "EPSG:4326"
  /** Number of wards */
  wardCount: number
}

// ============================================================================
// OBSERVATIONAL DATA SCHEMAS (Optional)
// ============================================================================

/**
 * Station Observation Summary
 * 
 * Represents aggregated observational data from weather stations.
 * Used for validation and enhancement of forecast data.
 */
export interface StationObservation {
  /** County ID */
  countyId: string
  /** Weather stations in the county */
  stations: WeatherStation[]
  /** Aggregation period */
  period: {
    start: string // ISO date
    end: string // ISO date
  }
  /** Data source */
  source: "KMD" | "NOAA_GSOD" | "WMO_WIS" | "CUSTOM"
}

/**
 * Weather Station
 */
export interface WeatherStation {
  /** Station identifier (KMD code or WMO ID) */
  stationId: string
  /** Station name */
  stationName: string
  /** Geographic coordinates */
  coordinates: {
    latitude: number
    longitude: number
    elevation?: number // meters above sea level
  }
  /** Past 7-day summary */
  past7Days: StationSummary
  /** Optional: Daily observations */
  dailyObservations?: DailyObservation[]
}

/**
 * Station Summary (7-day aggregated)
 */
export interface StationSummary {
  /** Total rainfall in millimeters */
  totalRainfallMm: number
  /** Mean temperature in Celsius */
  meanTempC: number
  /** Maximum temperature in Celsius */
  maxTempC: number
  /** Minimum temperature in Celsius */
  minTempC: number
  /** Maximum wind speed in km/h */
  maxWindKmh: number
  /** Mean wind speed in km/h */
  meanWindKmh: number
  /** Dominant wind direction */
  dominantWindDirection?: string
  /** Number of rainy days */
  rainyDays: number
}

/**
 * Daily Observation
 */
export interface DailyObservation {
  /** Date (ISO format) */
  date: string
  /** Rainfall (mm) */
  rainfall: number
  /** Maximum temperature (°C) */
  tempMax: number
  /** Minimum temperature (°C) */
  tempMin: number
  /** Mean temperature (°C) */
  tempMean: number
  /** Maximum wind speed (km/h) */
  windMax: number
  /** Wind direction */
  windDirection?: string
}

// ============================================================================
// PROCESSING SCHEMAS - Intermediate Data Structures
// ============================================================================

/**
 * Aggregated Ward Forecast Data
 * 
 * Result of spatial aggregation: GFS grid points → Ward polygons
 * Output from GeoPandas spatial join operation.
 */
export interface WardForecast {
  /** Ward identifier */
  wardId: string
  /** County identifier */
  countyId: string
  /** Ward name */
  wardName: string
  /** Variable name */
  variable: WeatherVariable
  /** Weekly aggregated value */
  weeklyTotal?: number
  /** Weekly mean value */
  weeklyMean?: number
  /** Weekly maximum value */
  weeklyMax?: number
  /** Weekly minimum value */
  weeklyMin?: number
  /** Daily values (7-day array) */
  daily: number[]
  /** Aggregation method used */
  aggregationMethod: "point-in-polygon_mean" | "point-in-polygon_max" | "point-in-polygon_min" | "area-weighted_mean" | "area-weighted_sum"
  /** Number of grid points used in aggregation */
  gridPointsUsed: number
  /** Quality flag */
  qualityFlag: "good" | "degraded" | "missing"
  /** Units */
  units: string
}

/**
 * Weather Variable Type
 */
export type WeatherVariable = "rainfall" | "temperature" | "temperature_max" | "temperature_min" | "wind_speed" | "wind_u" | "wind_v" | "wind_direction" | "humidity"

/**
 * County Report Data
 * 
 * Aggregated county-level summary derived from ward-level data.
 */
export interface CountyReportData {
  /** County name */
  countyName: string
  /** County ID */
  countyId: string
  /** Report period */
  period: {
    start: string // ISO date
    end: string // ISO date
  }
  /** Rainfall summary */
  rainfall: {
    meanMm: number
    totalMm: number
    maxWard: {
      wardId: string
      wardName: string
      value: number
    }
    minWard: {
      wardId: string
      wardName: string
      value: number
    }
    numberOfRainyDays: number
  }
  /** Temperature summary */
  temperature: {
    minC: number
    maxC: number
    meanC: number
    hottestWard: {
      wardId: string
      wardName: string
      value: number
    }
    coolestWard: {
      wardId: string
      wardName: string
      value: number
    }
  }
  /** Wind summary */
  wind: {
    meanSpeedKmh: number
    maxGustKmh: number
    dominantDirection: string
    windiestWard: {
      wardId: string
      wardName: string
      value: number
    }
  }
  /** Extreme wards */
  extremeWards: {
    highestRainfall: string[] // ward IDs
    hottest: string[] // ward IDs
    coolest: string[] // ward IDs
    windiest: string[] // ward IDs
    floodRisk: string[] // ward IDs
  }
  /** Processing metadata */
  processingMetadata: {
    aggregationMethod: string
    gridPointsUsed: number
    dataQuality: "excellent" | "good" | "fair" | "degraded"
    warnings: string[]
  }
}

/**
 * Spatial Join Result
 * 
 * Result of GeoPandas spatial join operation.
 * Maps GFS grid points to ward polygons.
 */
export interface SpatialJoinResult {
  /** Ward ID */
  wardId: string
  /** Grid point indices that fall within this ward */
  gridPointIndices: number[]
  /** Grid point coordinates */
  gridPointCoordinates: Array<{
    lat: number
    lon: number
  }>
  /** Number of points */
  pointCount: number
  /** Coverage percentage (points in ward / total ward area) */
  coveragePercent?: number
}

// ============================================================================
// OUTPUT SCHEMAS - Report Components for PDF Generation
// ============================================================================

/**
 * Report Components
 * 
 * Structured data ready for PDF generation via ReportLab or WeasyPrint.
 */
export interface ReportComponents {
  /** Report header information */
  header: ReportHeader
  /** Generated map images (PNG paths or base64) */
  maps: ReportMaps
  /** Narrative text sections */
  narrative: ReportNarrative
  /** Tables and statistics */
  tables: ReportTables
  /** Metadata for report */
  metadata: ReportMetadata
}

/**
 * Report Header
 */
export interface ReportHeader {
  /** County name */
  county: string
  /** Valid period string */
  validPeriod: string // e.g., "Week 50, 2024 (December 2 - December 8, 2024)"
  /** Disclaimer text */
  disclaimer: string
  /** Generation date */
  generatedAt: string
}

/**
 * Report Maps
 * 
 * Paths to generated map images or base64 encoded images.
 */
export interface ReportMaps {
  /** Ward-level rainfall distribution map */
  rainfallWard: string // file path or base64
  /** Ward-level temperature distribution map */
  temperatureWard: string
  /** Ward-level wind speed distribution map */
  windSpeedWard: string
  /** Optional: County-level overview map */
  countyOverview?: string
  /** Map metadata */
  mapMetadata: {
    resolution: number // DPI
    format: "PNG" | "JPEG" | "SVG"
    projection: string // e.g., "EPSG:32637"
    generatedAt: string
  }
}

/**
 * Report Narrative
 * 
 * Generated narrative text for each section.
 */
export interface ReportNarrative {
  /** Executive overview paragraph */
  overview: string
  /** Rainfall outlook narrative */
  rainfallOutlook: string
  /** Temperature outlook narrative */
  temperatureOutlook: string
  /** Wind outlook narrative */
  windOutlook: string
  /** Impacts and advisories */
  advisories: string[]
  /** Weekly summary narrative */
  weeklySummary: string
}

/**
 * Report Tables
 * 
 * Structured data for table generation.
 */
export interface ReportTables {
  /** Ward-level statistics table */
  wardStatistics: WardStatisticsTable[]
  /** Daily summary table */
  dailySummary: DailySummaryTable[]
  /** Extreme values table */
  extremeValues: ExtremeValuesTable
}

/**
 * Ward Statistics Table Row
 */
export interface WardStatisticsTable {
  wardId: string
  wardName: string
  rainfallTotal: number
  rainfallDays: number
  tempMean: number
  tempMax: number
  tempMin: number
  windMax: number
  windMean: number
}

/**
 * Daily Summary Table Row
 */
export interface DailySummaryTable {
  day: string // "Monday", "Tuesday", etc.
  date: string // ISO date
  rainfall: number
  tempMax: number
  tempMin: number
  tempMean: number
  windMax: number
  windDirection?: string
}

/**
 * Extreme Values Table
 */
export interface ExtremeValuesTable {
  highestRainfall: {
    ward: string
    value: number
    date: string
  }
  lowestRainfall: {
    ward: string
    value: number
    date: string
  }
  hottestDay: {
    ward: string
    value: number
    date: string
  }
  coolestNight: {
    ward: string
    value: number
    date: string
  }
  strongestWind: {
    ward: string
    value: number
    date: string
  }
}

/**
 * Report Metadata
 */
export interface ReportMetadata {
  /** GFS model run timestamp */
  gfsRun: string
  /** Report generation timestamp */
  generated: string
  /** System version */
  systemVersion: string
  /** Data source */
  dataSource: "GFS" | "GFS+OBS"
  /** Processing duration in seconds */
  processingDuration?: number
  /** Quality flags */
  qualityFlags: string[]
}

// ============================================================================
// DATA FLOW VALIDATION INTERFACES
// ============================================================================

/**
 * Validation Result
 */
export interface ValidationResult {
  /** Whether validation passed */
  isValid: boolean
  /** Validation errors */
  errors: ValidationError[]
  /** Validation warnings */
  warnings: ValidationWarning[]
}

/**
 * Validation Error
 */
export interface ValidationError {
  /** Error code */
  code: string
  /** Error message */
  message: string
  /** Field or component that failed */
  field?: string
  /** Severity */
  severity: "error" | "critical"
}

/**
 * Validation Warning
 */
export interface ValidationWarning {
  /** Warning code */
  code: string
  /** Warning message */
  message: string
  /** Field or component */
  field?: string
}

/**
 * Data Quality Flags
 */
export interface DataQualityFlags {
  /** Overall quality score (0-100) */
  qualityScore: number
  /** Missing data percentage */
  missingDataPercent: number
  /** Out of range values count */
  outOfRangeCount: number
  /** Spatial coverage percentage */
  spatialCoveragePercent: number
  /** Temporal coverage percentage */
  temporalCoveragePercent: number
  /** Flags */
  flags: Array<{
    type: "missing_data" | "out_of_range" | "low_coverage" | "temporal_gap" | "spatial_gap"
    message: string
    severity: "info" | "warning" | "error"
  }>
}

// ============================================================================
// HELPER TYPES AND UTILITIES
// ============================================================================

/**
 * Coordinate Point
 */
export interface Coordinate {
  latitude: number
  longitude: number
}

/**
 * Bounding Box
 */
export interface BoundingBox {
  north: number
  south: number
  east: number
  west: number
}

/**
 * Time Range
 */
export interface TimeRange {
  start: string // ISO datetime
  end: string // ISO datetime
}

/**
 * Processing Status
 */
export type ProcessingStatus = "pending" | "processing" | "completed" | "failed" | "cancelled"

/**
 * Processing Step
 */
export interface ProcessingStep {
  step: string
  status: ProcessingStatus
  startedAt?: string
  completedAt?: string
  duration?: number // seconds
  error?: string
}

/**
 * Processing Pipeline State
 */
export interface ProcessingPipelineState {
  /** Current step */
  currentStep: string
  /** All steps */
  steps: ProcessingStep[]
  /** Overall status */
  status: ProcessingStatus
  /** Progress percentage (0-100) */
  progress: number
  /** Started timestamp */
  startedAt: string
  /** Estimated completion */
  estimatedCompletion?: string
}

// ============================================================================
// VALIDATION FUNCTIONS
// ============================================================================

/**
 * Validate GFS GRIB file structure
 */
export function validateGFSFile(file: GFSGribFile): ValidationResult {
  const errors: ValidationError[] = []
  const warnings: ValidationWarning[] = []

  // Check required variables
  if (!file.variables.total_precipitation) {
    errors.push({
      code: "MISSING_PRECIPITATION",
      message: "Total precipitation variable is required",
      severity: "error",
    })
  }

  if (!file.variables.t2m) {
    errors.push({
      code: "MISSING_TEMPERATURE",
      message: "2-meter temperature variable is required",
      severity: "error",
    })
  }

  // Check forecast hours
  if (file.forecastHours.length < 7) {
    warnings.push({
      code: "INSUFFICIENT_FORECAST_HOURS",
      message: "Forecast hours should cover at least 7 days",
    })
  }

  // Check grid resolution
  if (file.grid.resolution !== 0.25) {
    warnings.push({
      code: "NON_STANDARD_RESOLUTION",
      message: `Grid resolution is ${file.grid.resolution}°, expected 0.25°`,
    })
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  }
}

/**
 * Validate administrative boundaries
 */
export function validateAdminBoundary(boundary: AdminBoundary): ValidationResult {
  const errors: ValidationError[] = []
  const warnings: ValidationWarning[] = []

  // Check county ID format
  if (!/^\d{2}$/.test(boundary.countyId)) {
    errors.push({
      code: "INVALID_COUNTY_ID",
      message: "County ID must be a 2-digit string",
      field: "countyId",
      severity: "error",
    })
  }

  // Check ward count
  if (boundary.wards.length === 0) {
    errors.push({
      code: "NO_WARDS",
      message: "County must have at least one ward",
      severity: "error",
    })
  }

  // Check CRS
  if (boundary.metadata.crs !== "EPSG:4326") {
    warnings.push({
      code: "NON_WGS84_CRS",
      message: `CRS is ${boundary.metadata.crs}, expected EPSG:4326`,
    })
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  }
}

/**
 * Validate ward forecast data
 */
export function validateWardForecast(forecast: WardForecast): ValidationResult {
  const errors: ValidationError[] = []
  const warnings: ValidationWarning[] = []

  // Check daily array length
  if (forecast.daily.length !== 7) {
    errors.push({
      code: "INVALID_DAILY_LENGTH",
      message: "Daily array must contain exactly 7 values",
      field: "daily",
      severity: "error",
    })
  }

  // Check for NaN values
  if (forecast.daily.some((val) => isNaN(val))) {
    errors.push({
      code: "NAN_VALUES",
      message: "Daily array contains NaN values",
      field: "daily",
      severity: "error",
    })
  }

  // Check grid points used
  if (forecast.gridPointsUsed === 0) {
    warnings.push({
      code: "NO_GRID_POINTS",
      message: "No grid points used in aggregation - data may be unreliable",
    })
  }

  // Check quality flag
  if (forecast.qualityFlag === "missing") {
    errors.push({
      code: "MISSING_DATA",
      message: "Ward forecast has missing data flag",
      severity: "error",
    })
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  }
}

/**
 * Calculate data quality score
 */
export function calculateDataQuality(forecasts: WardForecast[]): DataQualityFlags {
  const totalWards = forecasts.length
  const missingData = forecasts.filter((f) => f.qualityFlag === "missing").length
  const degradedData = forecasts.filter((f) => f.qualityFlag === "degraded").length
  const goodData = forecasts.filter((f) => f.qualityFlag === "good").length

  const missingPercent = (missingData / totalWards) * 100
  const qualityScore = (goodData / totalWards) * 100

  const flags: DataQualityFlags["flags"] = []

  if (missingPercent > 10) {
    flags.push({
      type: "missing_data",
      message: `${missingPercent.toFixed(1)}% of wards have missing data`,
      severity: "error",
    })
  } else if (missingPercent > 5) {
    flags.push({
      type: "missing_data",
      message: `${missingPercent.toFixed(1)}% of wards have missing data`,
      severity: "warning",
    })
  }

  if (degradedData > 0) {
    flags.push({
      type: "low_coverage",
      message: `${degradedData} wards have degraded data quality`,
      severity: "warning",
    })
  }

  return {
    qualityScore: Math.round(qualityScore),
    missingDataPercent: Math.round(missingPercent * 10) / 10,
    outOfRangeCount: 0, // Would need additional validation
    spatialCoveragePercent: ((totalWards - missingData) / totalWards) * 100,
    temporalCoveragePercent: 100, // Assuming full temporal coverage
    flags,
  }
}

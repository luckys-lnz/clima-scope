// County Weather Report JSON Schema
// Based on GFS GRIB data aggregation for Kenya counties

export interface TemperatureData {
  weekly: {
    mean: number
    max: number
    min: number
  }
  daily: number[] // 7 values [Mon-Sun]
  units: "°C"
  anomaly?: number
}

export interface RainfallData {
  weekly: {
    total: number
    max_intensity: number
  }
  daily: number[] // 7 values in mm
  units: "mm"
  probability_above_normal?: number
}

export interface WindData {
  weekly: {
    mean_speed: number
    max_gust: number
    dominant_direction: string
  }
  units: "km/h"
  daily_peak: number[]
}

export interface WardSummary {
  ward_id: string
  ward_name: string
  rainfall_total: number
  temp_max: number
  temp_min: number
  temp_mean?: number
  wind_max: number
  wind_mean?: number
  grid_points_used?: number
  quality_flag?: "good" | "degraded" | "missing"
}

export interface ExtremeValues {
  highest_rainfall?: {
    ward_id: string
    ward_name?: string
    value: number
    days?: number[]
  }
  lowest_rainfall?: {
    ward_id: string
    ward_name?: string
    value: number
  }
  hottest_ward?: {
    ward_id: string
    ward_name?: string
    value: number
    day?: number
  }
  coolest_ward?: {
    ward_id: string
    ward_name?: string
    value: number
    day?: number
  }
  windiest_ward?: {
    ward_id: string
    ward_name?: string
    value: number
  }
  flood_risk_wards?: Array<{
    ward_id: string
    ward_name?: string
    risk_level?: "low" | "moderate" | "high"
    total_rainfall?: number
  }>
}

export interface Metadata {
  data_source: "GFS" | "GFS+OBS"
  model_run: string
  generated: string
  aggregation_method: "point-in-polygon" | "area-weighted"
  grid_resolution: string
  grid_points_used: number
  warnings?: string[]
}

export interface CountyWeatherReport {
  schema_version?: string
  county_id: string
  county_name: string
  period: {
    start: string
    end: string
    week_number?: number
    year?: number
  }
  variables: {
    temperature: TemperatureData
    rainfall: RainfallData
    wind: WindData
  }
  wards: WardSummary[]
  extremes?: ExtremeValues
  metadata: Metadata
  disclaimer: string
  quality_flags?: {
    overall_quality?: "excellent" | "good" | "fair" | "degraded"
    missing_data_percent?: number
    spatial_coverage_percent?: number
    warnings?: string[]
  }
}

// Kenya County List with KNBS codes
// Official 47 counties as per Kenya Constitution 2010
// Source: Kenya National Bureau of Statistics (KNBS)
export const KENYA_COUNTIES = [
  { id: "01", name: "Mombasa" },
  { id: "02", name: "Kwale" },
  { id: "03", name: "Kilifi" },
  { id: "04", name: "Tana River" },
  { id: "05", name: "Lamu" },
  { id: "06", name: "Taita-Taveta" },
  { id: "07", name: "Garissa" },
  { id: "08", name: "Wajir" },
  { id: "09", name: "Mandera" },
  { id: "10", name: "Marsabit" },
  { id: "11", name: "Isiolo" },
  { id: "12", name: "Meru" },
  { id: "13", name: "Tharaka-Nithi" },
  { id: "14", name: "Embu" },
  { id: "15", name: "Kitui" },
  { id: "16", name: "Makueni" },
  { id: "17", name: "Nyandarua" },
  { id: "18", name: "Nyeri" },
  { id: "19", name: "Kirinyaga" },
  { id: "20", name: "Muranga" },
  { id: "21", name: "Kiambu" },
  { id: "22", name: "Turkana" },
  { id: "23", name: "West Pokot" },
  { id: "24", name: "Samburu" },
  { id: "25", name: "Trans-Nzoia" },
  { id: "26", name: "Uasin Gishu" },
  { id: "27", name: "Elgeyo-Marakwet" },
  { id: "28", name: "Nandi" },
  { id: "29", name: "Baringo" },
  { id: "30", name: "Laikipia" },
  { id: "31", name: "Nakuru" },
  { id: "32", name: "Nairobi" },
  { id: "33", name: "Kajiado" },
  { id: "34", name: "Kericho" },
  { id: "35", name: "Bomet" },
  { id: "36", name: "Kakamega" },
  { id: "37", name: "Vihiga" },
  { id: "38", name: "Bungoma" },
  { id: "39", name: "Busia" },
  { id: "40", name: "Siaya" },
  { id: "41", name: "Kisumu" },
  { id: "42", name: "Homa Bay" },
  { id: "43", name: "Migori" },
  { id: "44", name: "Kisii" },
  { id: "45", name: "Nyamira" },
  { id: "46", name: "Narok" },
  { id: "47", name: "Machakos" }
] as const

// Validate county list has exactly 47 unique counties
export function validateCountyList(): { isValid: boolean; errors: string[] } {
  const errors: string[] = []
  const ids = new Set<string>()
  const names = new Set<string>()

  for (const county of KENYA_COUNTIES) {
    if (ids.has(county.id)) {
      errors.push(`Duplicate county ID: ${county.id}`)
    }
    ids.add(county.id)

    if (names.has(county.name)) {
      errors.push(`Duplicate county name: ${county.name}`)
    }
    names.add(county.name)
  }

  if (KENYA_COUNTIES.length !== 47) {
    errors.push(`Expected 47 counties, found ${KENYA_COUNTIES.length}`)
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}

// Mock weather data generator for demonstration
export function generateMockCountyReport(countyId: string, countyName: string): CountyWeatherReport {
  const today = new Date()
  const startDate = new Date(today)
  startDate.setDate(startDate.getDate() - today.getDay())
  const endDate = new Date(startDate)
  endDate.setDate(endDate.getDate() + 6)

  const formatDate = (date: Date) => date.toISOString().split("T")[0]

  return {
    county_id: countyId,
    county_name: countyName,
    period: {
      start: formatDate(startDate),
      end: formatDate(endDate),
    },
    variables: {
      temperature: {
        weekly: {
          mean: 24.8 + Math.random() * 5,
          max: 28.2 + Math.random() * 4,
          min: 19.1 + Math.random() * 3,
        },
        daily: Array.from({ length: 7 }, () => 25 + Math.random() * 5),
        units: "°C",
        anomaly: Math.random() * 2 - 1,
      },
      rainfall: {
        weekly: {
          total: 30 + Math.random() * 30,
          max_intensity: 12 + Math.random() * 20,
        },
        daily: Array.from({ length: 7 }, () => Math.random() * 20),
        units: "mm",
        probability_above_normal: 40 + Math.random() * 40,
      },
      wind: {
        weekly: {
          mean_speed: 12 + Math.random() * 8,
          max_gust: 20 + Math.random() * 15,
          dominant_direction: ["N", "S", "E", "W", "NE", "NW", "SE", "SW"][
            Math.floor(Math.random() * 8)
          ],
        },
        units: "km/h",
        daily_peak: Array.from({ length: 7 }, () => 15 + Math.random() * 20),
      },
    },
    wards: [
      {
        ward_id: `${countyId}01`,
        ward_name: "Ward 1",
        rainfall_total: 30 + Math.random() * 25,
        temp_max: 28 + Math.random() * 3,
        temp_min: 18 + Math.random() * 3,
        wind_max: 25 + Math.random() * 15,
      },
      {
        ward_id: `${countyId}02`,
        ward_name: "Ward 2",
        rainfall_total: 28 + Math.random() * 25,
        temp_max: 27 + Math.random() * 3,
        temp_min: 17 + Math.random() * 3,
        wind_max: 24 + Math.random() * 15,
      },
    ],
    extremes: {
      highest_rainfall: {
        ward_id: `${countyId}01`,
        ward_name: "Ward 1",
        value: 45 + Math.random() * 20,
        days: [3, 4],
      },
      hottest_ward: {
        ward_id: `${countyId}02`,
        ward_name: "Ward 2",
        value: 28 + Math.random() * 3,
        day: 2,
      },
      flood_risk_wards: [
        {
          ward_id: `${countyId}01`,
          ward_name: "Ward 1",
          risk_level: "moderate",
          total_rainfall: 45 + Math.random() * 20,
        },
      ],
    },
    metadata: {
      data_source: Math.random() > 0.5 ? "GFS" : "GFS+OBS",
      model_run: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      generated: new Date().toISOString(),
      aggregation_method: "point-in-polygon",
      grid_resolution: "0.25°",
      grid_points_used: 180 + Math.floor(Math.random() * 20),
    },
    disclaimer:
      "Ward-level maps derived from spatial aggregation of global forecasts for planning purposes only. Contact the local meteorological office for updates.",
  }
}

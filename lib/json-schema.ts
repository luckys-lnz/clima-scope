/**
 * JSON Schema Definition for County Weather Report Output
 * 
 * This file defines the JSON Schema (Draft 7) for the county weather report output.
 * The schema is used for validation, documentation, and API contracts.
 * 
 * @author Person B
 * @version 1.0
 * 
 * Schema follows JSON Schema Draft 7 specification:
 * https://json-schema.org/draft-07/schema
 */

/**
 * Main County Weather Report JSON Schema
 * 
 * This is the nested structure optimized for dashboard consumption.
 * For CSV export, use the flattening utilities provided.
 */
export const COUNTY_WEATHER_REPORT_SCHEMA = {
  $schema: "http://json-schema.org/draft-07/schema#",
  $id: "https://clima-scope.ke/schemas/county-weather-report/v1.0",
  title: "County Weather Report",
  description: "Weekly county-level weather forecast report with ward-level breakdowns",
  type: "object",
  required: ["county_id", "county_name", "period", "variables", "metadata", "schema_version"],
  properties: {
    schema_version: {
      type: "string",
      description: "Schema version for compatibility checking",
      pattern: "^\\d+\\.\\d+$",
      example: "1.0",
      default: "1.0",
    },
    county_id: {
      type: "string",
      description: "KNBS county code (2-digit string, e.g., '31' for Nairobi)",
      pattern: "^\\d{2}$",
      minLength: 2,
      maxLength: 2,
      examples: ["01", "31", "47"],
    },
    county_name: {
      type: "string",
      description: "Full official county name",
      minLength: 1,
      maxLength: 100,
      examples: ["Nairobi", "Mombasa", "Kisumu"],
    },
    period: {
      type: "object",
      description: "Report period (7-day week)",
      required: ["start", "end"],
      properties: {
        start: {
          type: "string",
          format: "date",
          description: "Week start date (ISO 8601: YYYY-MM-DD)",
          pattern: "^\\d{4}-\\d{2}-\\d{2}$",
          example: "2026-01-19",
        },
        end: {
          type: "string",
          format: "date",
          description: "Week end date (ISO 8601: YYYY-MM-DD)",
          pattern: "^\\d{4}-\\d{2}-\\d{2}$",
          example: "2026-01-25",
        },
        week_number: {
          type: "integer",
          description: "ISO week number (1-53)",
          minimum: 1,
          maximum: 53,
        },
        year: {
          type: "integer",
          description: "Year (4 digits)",
          minimum: 2000,
          maximum: 2100,
        },
      },
      additionalProperties: false,
    },
    variables: {
      type: "object",
      description: "Weather variables aggregated at county and ward levels",
      required: ["temperature", "rainfall", "wind"],
      properties: {
        temperature: {
          $ref: "#/definitions/TemperatureData",
        },
        rainfall: {
          $ref: "#/definitions/RainfallData",
        },
        wind: {
          $ref: "#/definitions/WindData",
        },
      },
      additionalProperties: false,
    },
    wards: {
      type: "array",
      description: "Ward-level summary statistics",
      items: {
        $ref: "#/definitions/WardSummary",
      },
      minItems: 1,
    },
    extremes: {
      $ref: "#/definitions/ExtremeValues",
    },
    metadata: {
      $ref: "#/definitions/Metadata",
    },
    disclaimer: {
      type: "string",
      description: "Legal disclaimer and usage guidance",
      minLength: 1,
      maxLength: 1000,
    },
    quality_flags: {
      type: "object",
      description: "Data quality indicators",
      properties: {
        overall_quality: {
          type: "string",
          enum: ["excellent", "good", "fair", "degraded"],
          description: "Overall data quality assessment",
        },
        missing_data_percent: {
          type: "number",
          minimum: 0,
          maximum: 100,
          description: "Percentage of missing data",
        },
        spatial_coverage_percent: {
          type: "number",
          minimum: 0,
          maximum: 100,
          description: "Percentage of wards with valid data",
        },
        warnings: {
          type: "array",
          items: {
            type: "string",
          },
          description: "Quality warnings",
        },
      },
    },
  },
  additionalProperties: false,
  definitions: {
    TemperatureData: {
      type: "object",
      description: "Temperature data (2-meter air temperature)",
      required: ["weekly", "daily", "units"],
      properties: {
        weekly: {
          type: "object",
          description: "Weekly aggregated temperature statistics",
          required: ["mean", "max", "min"],
          properties: {
            mean: {
              type: "number",
              description: "Mean temperature over 7 days",
              minimum: -50,
              maximum: 50,
              example: 24.8,
            },
            max: {
              type: "number",
              description: "Maximum temperature during the week",
              minimum: -50,
              maximum: 50,
              example: 28.2,
            },
            min: {
              type: "number",
              description: "Minimum temperature during the week",
              minimum: -50,
              maximum: 50,
              example: 19.1,
            },
          },
          additionalProperties: false,
        },
        daily: {
          type: "array",
          description: "Daily maximum temperatures [Mon, Tue, Wed, Thu, Fri, Sat, Sun]",
          items: {
            type: "number",
            minimum: -50,
            maximum: 50,
          },
          minItems: 7,
          maxItems: 7,
          example: [26.1, 27.3, 28.2, 25.8, 24.1, 23.9, 22.7],
        },
        units: {
          type: "string",
          enum: ["°C"],
          description: "Temperature units (always Celsius)",
          example: "°C",
        },
        anomaly: {
          type: "number",
          description: "Temperature anomaly vs climatology (°C)",
          minimum: -20,
          maximum: 20,
          example: 1.2,
        },
        daily_min: {
          type: "array",
          description: "Daily minimum temperatures [Mon-Sun]",
          items: {
            type: "number",
            minimum: -50,
            maximum: 50,
          },
          minItems: 7,
          maxItems: 7,
        },
        daily_mean: {
          type: "array",
          description: "Daily mean temperatures [Mon-Sun]",
          items: {
            type: "number",
            minimum: -50,
            maximum: 50,
          },
          minItems: 7,
          maxItems: 7,
        },
      },
      additionalProperties: false,
    },
    RainfallData: {
      type: "object",
      description: "Precipitation (rainfall) data",
      required: ["weekly", "daily", "units"],
      properties: {
        weekly: {
          type: "object",
          description: "Weekly aggregated rainfall statistics",
          required: ["total", "max_intensity"],
          properties: {
            total: {
              type: "number",
              description: "Total accumulated rainfall over 7 days",
              minimum: 0,
              maximum: 1000,
              example: 34.7,
            },
            max_intensity: {
              type: "number",
              description: "Maximum daily rainfall intensity",
              minimum: 0,
              maximum: 500,
              example: 18.2,
            },
            rainy_days: {
              type: "integer",
              description: "Number of days with rainfall > 0.1mm",
              minimum: 0,
              maximum: 7,
              example: 5,
            },
          },
          additionalProperties: false,
        },
        daily: {
          type: "array",
          description: "Daily rainfall amounts [Mon, Tue, Wed, Thu, Fri, Sat, Sun] in mm",
          items: {
            type: "number",
            minimum: 0,
            maximum: 500,
          },
          minItems: 7,
          maxItems: 7,
          example: [2.1, 8.4, 12.7, 5.3, 3.9, 1.2, 1.1],
        },
        units: {
          type: "string",
          enum: ["mm"],
          description: "Rainfall units (always millimeters)",
          example: "mm",
        },
        probability_above_normal: {
          type: "number",
          description: "Probability of above-normal rainfall (0-100%)",
          minimum: 0,
          maximum: 100,
          example: 65.5,
        },
      },
      additionalProperties: false,
    },
    WindData: {
      type: "object",
      description: "Wind speed and direction data (10-meter)",
      required: ["weekly", "units", "daily_peak"],
      properties: {
        weekly: {
          type: "object",
          description: "Weekly aggregated wind statistics",
          required: ["mean_speed", "max_gust", "dominant_direction"],
          properties: {
            mean_speed: {
              type: "number",
              description: "Mean wind speed over 7 days",
              minimum: 0,
              maximum: 200,
              example: 12.5,
            },
            max_gust: {
              type: "number",
              description: "Maximum wind gust during the week",
              minimum: 0,
              maximum: 200,
              example: 25.3,
            },
            dominant_direction: {
              type: "string",
              description: "Most frequent wind direction",
              pattern: "^(N|S|E|W|NE|NW|SE|SW|NNE|NNW|SSE|SSW|ENE|ESE|WNW|WSW)$",
              example: "NE",
            },
          },
          additionalProperties: false,
        },
        units: {
          type: "string",
          enum: ["km/h"],
          description: "Wind speed units (always km/h)",
          example: "km/h",
        },
        daily_peak: {
          type: "array",
          description: "Daily peak wind speeds [Mon-Sun] in km/h",
          items: {
            type: "number",
            minimum: 0,
            maximum: 200,
          },
          minItems: 7,
          maxItems: 7,
          example: [15.2, 18.7, 22.1, 16.3, 14.8, 13.5, 12.9],
        },
        daily_direction: {
          type: "array",
          description: "Daily dominant wind directions [Mon-Sun]",
          items: {
            type: "string",
            pattern: "^(N|S|E|W|NE|NW|SE|SW|NNE|NNW|SSE|SSW|ENE|ESE|WNW|WSW)$",
          },
          minItems: 7,
          maxItems: 7,
        },
      },
      additionalProperties: false,
    },
    WardSummary: {
      type: "object",
      description: "Ward-level weather summary",
      required: ["ward_id", "ward_name", "rainfall_total", "temp_max", "temp_min", "wind_max"],
      properties: {
        ward_id: {
          type: "string",
          description: "Unique ward identifier (county code + ward number)",
          pattern: "^\\d{4,6}$",
          example: "3101",
        },
        ward_name: {
          type: "string",
          description: "Official ward name",
          minLength: 1,
          maxLength: 100,
          example: "Kibera",
        },
        rainfall_total: {
          type: "number",
          description: "Total weekly rainfall (mm)",
          minimum: 0,
          maximum: 1000,
          example: 48.2,
        },
        temp_max: {
          type: "number",
          description: "Maximum temperature (°C)",
          minimum: -50,
          maximum: 50,
          example: 27.1,
        },
        temp_min: {
          type: "number",
          description: "Minimum temperature (°C)",
          minimum: -50,
          maximum: 50,
          example: 18.5,
        },
        temp_mean: {
          type: "number",
          description: "Mean temperature (°C)",
          minimum: -50,
          maximum: 50,
          example: 22.8,
        },
        wind_max: {
          type: "number",
          description: "Maximum wind speed (km/h)",
          minimum: 0,
          maximum: 200,
          example: 28.3,
        },
        wind_mean: {
          type: "number",
          description: "Mean wind speed (km/h)",
          minimum: 0,
          maximum: 200,
          example: 14.2,
        },
        grid_points_used: {
          type: "integer",
          description: "Number of GFS grid points used in aggregation",
          minimum: 0,
          example: 12,
        },
        quality_flag: {
          type: "string",
          enum: ["good", "degraded", "missing"],
          description: "Data quality indicator for this ward",
          example: "good",
        },
      },
      additionalProperties: false,
    },
    ExtremeValues: {
      type: "object",
      description: "Extreme weather values and notable conditions",
      properties: {
        highest_rainfall: {
          type: "object",
          description: "Ward with highest rainfall",
          required: ["ward_id", "ward_name", "value"],
          properties: {
            ward_id: {
              type: "string",
              example: "31015",
            },
            ward_name: {
              type: "string",
              example: "Kasarani",
            },
            value: {
              type: "number",
              description: "Total rainfall (mm)",
              minimum: 0,
              example: 68.2,
            },
            days: {
              type: "array",
              description: "Days of week (0-6) with highest rainfall",
              items: {
                type: "integer",
                minimum: 0,
                maximum: 6,
              },
              example: [2, 3],
            },
          },
          additionalProperties: false,
        },
        lowest_rainfall: {
          type: "object",
          description: "Ward with lowest rainfall",
          properties: {
            ward_id: {
              type: "string",
            },
            ward_name: {
              type: "string",
            },
            value: {
              type: "number",
              minimum: 0,
            },
          },
        },
        hottest_ward: {
          type: "object",
          description: "Ward with highest temperature",
          properties: {
            ward_id: {
              type: "string",
            },
            ward_name: {
              type: "string",
            },
            value: {
              type: "number",
            },
            day: {
              type: "integer",
              minimum: 0,
              maximum: 6,
            },
          },
        },
        coolest_ward: {
          type: "object",
          description: "Ward with lowest temperature",
          properties: {
            ward_id: {
              type: "string",
            },
            ward_name: {
              type: "string",
            },
            value: {
              type: "number",
            },
            day: {
              type: "integer",
              minimum: 0,
              maximum: 6,
            },
          },
        },
        windiest_ward: {
          type: "object",
          description: "Ward with highest wind speed",
          properties: {
            ward_id: {
              type: "string",
            },
            ward_name: {
              type: "string",
            },
            value: {
              type: "number",
            },
          },
        },
        flood_risk_wards: {
          type: "array",
          description: "Wards with elevated flood risk (based on rainfall thresholds)",
          items: {
            type: "object",
            properties: {
              ward_id: {
                type: "string",
              },
              ward_name: {
                type: "string",
              },
              risk_level: {
                type: "string",
                enum: ["low", "moderate", "high"],
              },
              total_rainfall: {
                type: "number",
              },
            },
          },
        },
      },
      additionalProperties: false,
    },
    Metadata: {
      type: "object",
      description: "Report generation metadata and data provenance",
      required: ["data_source", "model_run", "generated", "aggregation_method", "grid_resolution", "grid_points_used"],
      properties: {
        data_source: {
          type: "string",
          enum: ["GFS", "GFS+OBS"],
          description: "Data source identifier",
          example: "GFS",
        },
        model_run: {
          type: "string",
          format: "date-time",
          description: "GFS model run timestamp (ISO 8601)",
          pattern: "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$",
          example: "2026-01-18T00:00:00Z",
        },
        generated: {
          type: "string",
          format: "date-time",
          description: "Report generation timestamp (ISO 8601)",
          pattern: "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z$",
          example: "2026-01-18T09:30:00Z",
        },
        aggregation_method: {
          type: "string",
          enum: ["point-in-polygon", "area-weighted"],
          description: "Spatial aggregation method used",
          example: "point-in-polygon",
        },
        grid_resolution: {
          type: "string",
          description: "GFS grid resolution",
          pattern: "^\\d+\\.\\d+°$",
          example: "0.25°",
        },
        grid_points_used: {
          type: "integer",
          description: "Total number of GFS grid points used in aggregation",
          minimum: 0,
          example: 184,
        },
        warnings: {
          type: "array",
          description: "Data quality warnings and notices",
          items: {
            type: "string",
            maxLength: 500,
          },
          example: ["Some wards have limited grid point coverage"],
        },
        system_version: {
          type: "string",
          description: "System version that generated this report",
          pattern: "^\\d+\\.\\d+\\.\\d+$",
          example: "1.0.0",
        },
        processing_duration_seconds: {
          type: "number",
          description: "Time taken to generate report (seconds)",
          minimum: 0,
          example: 45.3,
        },
      },
      additionalProperties: false,
    },
  },
} as const

/**
 * County Weather Report Data Type
 * 
 * This represents the actual report data structure (not the schema definition).
 * Use this type for report data instances.
 */
export interface CountyWeatherReportData {
  schema_version: string
  county_id: string
  county_name: string
  period: {
    start: string
    end: string
    week_number?: number
    year?: number
  }
  variables: {
    temperature: {
      weekly: {
        mean: number
        max: number
        min: number
      }
      daily: number[] | readonly number[]
      units: "°C"
      anomaly?: number
      daily_min?: number[] | readonly number[]
      daily_mean?: number[] | readonly number[]
    }
    rainfall: {
      weekly: {
        total: number
        max_intensity: number
        rainy_days?: number
      }
      daily: number[] | readonly number[]
      units: "mm"
      probability_above_normal?: number
    }
    wind: {
      weekly: {
        mean_speed: number
        max_gust: number
        dominant_direction: string
      }
      units: "km/h"
      daily_peak: number[] | readonly number[]
      daily_direction?: string[] | readonly string[]
    }
  }
  wards?: Array<{
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
  }> | ReadonlyArray<{
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
  }>
  extremes?: {
    highest_rainfall?: {
      ward_id: string
      ward_name: string
      value: number
      days?: number[] | readonly number[]
    }
    lowest_rainfall?: {
      ward_id: string
      ward_name: string
      value: number
    }
    hottest_ward?: {
      ward_id: string
      ward_name: string
      value: number
      day?: number
    }
    coolest_ward?: {
      ward_id: string
      ward_name: string
      value: number
      day?: number
    }
    windiest_ward?: {
      ward_id: string
      ward_name: string
      value: number
    }
    flood_risk_wards?: Array<{
      ward_id: string
      ward_name: string
      risk_level: "low" | "moderate" | "high"
      total_rainfall: number
    }> | ReadonlyArray<{
      ward_id: string
      ward_name: string
      risk_level: "low" | "moderate" | "high"
      total_rainfall: number
    }>
  }
  metadata: {
    data_source: "GFS" | "GFS+OBS"
    model_run: string
    generated: string
    aggregation_method: "point-in-polygon" | "area-weighted"
    grid_resolution: string
    grid_points_used: number
    warnings?: string[] | readonly string[]
    system_version?: string
    processing_duration_seconds?: number
  }
  disclaimer?: string
  quality_flags?: {
    overall_quality?: "excellent" | "good" | "fair" | "degraded"
    missing_data_percent?: number
    spatial_coverage_percent?: number
    warnings?: string[] | readonly string[]
  }
}

/**
 * Flat Structure Schema (for CSV export)
 * 
 * This is a flattened version where each ward is a separate row.
 * Useful for CSV export and tabular analysis.
 */
export interface FlatWardReport {
  /** Schema version */
  schema_version: string
  /** County ID */
  county_id: string
  /** County name */
  county_name: string
  /** Period start */
  period_start: string
  /** Period end */
  period_end: string
  /** Ward ID */
  ward_id: string
  /** Ward name */
  ward_name: string
  /** Total rainfall (mm) */
  rainfall_total: number
  /** Mean temperature (°C) */
  temp_mean: number
  /** Max temperature (°C) */
  temp_max: number
  /** Min temperature (°C) */
  temp_min: number
  /** Max wind speed (km/h) */
  wind_max: number
  /** Mean wind speed (km/h) */
  wind_mean: number
  /** Data source */
  data_source: "GFS" | "GFS+OBS"
  /** Model run timestamp */
  model_run: string
  /** Generation timestamp */
  generated: string
}

/**
 * Type guard to check if data matches the schema
 */
export function isValidCountyReport(data: unknown): data is CountyWeatherReportData {
  if (typeof data !== "object" || data === null) {
    return false
  }

  const obj = data as Record<string, unknown>

  // Check required fields
  if (
    typeof obj.county_id !== "string" ||
    typeof obj.county_name !== "string" ||
    typeof obj.period !== "object" ||
    typeof obj.variables !== "object" ||
    typeof obj.metadata !== "object"
  ) {
    return false
  }

  // Check county_id format
  if (!/^\d{2}$/.test(obj.county_id)) {
    return false
  }

  // Check period structure
  const period = obj.period as Record<string, unknown>
  if (typeof period.start !== "string" || typeof period.end !== "string") {
    return false
  }

  // Check variables structure
  const variables = obj.variables as Record<string, unknown>
  if (
    typeof variables.temperature !== "object" ||
    typeof variables.rainfall !== "object" ||
    typeof variables.wind !== "object"
  ) {
    return false
  }

  return true
}

/**
 * Flatten nested report structure for CSV export
 * 
 * Converts nested structure to flat structure with one row per ward.
 */
export function flattenReportForCSV(
  report: CountyWeatherReportData | Readonly<CountyWeatherReportData>
): FlatWardReport[] {
  const flatReports: FlatWardReport[] = []

  if (!report.wards || !Array.isArray(report.wards)) {
    return flatReports
  }

  for (const ward of report.wards) {
    flatReports.push({
      schema_version: report.schema_version || "1.0",
      county_id: report.county_id,
      county_name: report.county_name,
      period_start: report.period.start,
      period_end: report.period.end,
      ward_id: ward.ward_id,
      ward_name: ward.ward_name,
      rainfall_total: ward.rainfall_total,
      temp_mean: ward.temp_mean || (ward.temp_max + ward.temp_min) / 2,
      temp_max: ward.temp_max,
      temp_min: ward.temp_min,
      wind_max: ward.wind_max,
      wind_mean: ward.wind_mean || ward.wind_max * 0.7, // Estimate if not provided
      data_source: report.metadata.data_source,
      model_run: report.metadata.model_run,
      generated: report.metadata.generated,
    })
  }

  return flatReports
}

/**
 * Example complete report (for documentation and testing)
 */
export const EXAMPLE_REPORT = {
  schema_version: "1.0",
  county_id: "31",
  county_name: "Nairobi",
  period: {
    start: "2026-01-19",
    end: "2026-01-25",
    week_number: 3,
    year: 2026,
  },
  variables: {
    temperature: {
      weekly: {
        mean: 24.8,
        max: 28.2,
        min: 19.1,
      },
      daily: [26.1, 27.3, 28.2, 25.8, 24.1, 23.9, 22.7],
      units: "°C",
      anomaly: 1.2,
      daily_min: [18.5, 19.2, 20.1, 18.8, 17.9, 17.5, 16.8],
      daily_mean: [22.3, 23.2, 24.1, 22.3, 21.0, 20.7, 19.7],
    },
    rainfall: {
      weekly: {
        total: 34.7,
        max_intensity: 18.2,
        rainy_days: 5,
      },
      daily: [2.1, 8.4, 12.7, 5.3, 3.9, 1.2, 1.1],
      units: "mm",
      probability_above_normal: 65.5,
    },
    wind: {
      weekly: {
        mean_speed: 12.5,
        max_gust: 25.3,
        dominant_direction: "NE",
      },
      units: "km/h",
      daily_peak: [15.2, 18.7, 22.1, 16.3, 14.8, 13.5, 12.9],
      daily_direction: ["NE", "NE", "E", "NE", "N", "N", "NE"],
    },
  },
  wards: [
    {
      ward_id: "3101",
      ward_name: "Kibera",
      rainfall_total: 48.2,
      temp_max: 27.1,
      temp_min: 18.5,
      temp_mean: 22.8,
      wind_max: 28.3,
      wind_mean: 14.2,
      grid_points_used: 12,
      quality_flag: "good",
    },
    {
      ward_id: "3102",
      ward_name: "Westlands",
      rainfall_total: 32.5,
      temp_max: 26.8,
      temp_min: 19.2,
      temp_mean: 23.0,
      wind_max: 24.1,
      wind_mean: 13.5,
      grid_points_used: 15,
      quality_flag: "good",
    },
  ],
  extremes: {
    highest_rainfall: {
      ward_id: "31015",
      ward_name: "Kasarani",
      value: 68.2,
      days: [2, 3],
    },
    hottest_ward: {
      ward_id: "3102",
      ward_name: "Westlands",
      value: 28.5,
      day: 2,
    },
    windiest_ward: {
      ward_id: "3101",
      ward_name: "Kibera",
      value: 28.3,
    },
    flood_risk_wards: [
      {
        ward_id: "31015",
        ward_name: "Kasarani",
        risk_level: "moderate",
        total_rainfall: 68.2,
      },
    ],
  },
  metadata: {
    data_source: "GFS",
    model_run: "2026-01-18T00:00:00Z",
    generated: "2026-01-18T09:30:00Z",
    aggregation_method: "point-in-polygon",
    grid_resolution: "0.25°",
    grid_points_used: 184,
    warnings: [],
    system_version: "1.0.0",
    processing_duration_seconds: 45.3,
  },
  disclaimer:
    "Ward-level maps derived from spatial aggregation of global forecasts for planning purposes only. Contact the local meteorological office for updates.",
  quality_flags: {
    overall_quality: "good",
    missing_data_percent: 0,
    spatial_coverage_percent: 100,
    warnings: [],
  },
} as const

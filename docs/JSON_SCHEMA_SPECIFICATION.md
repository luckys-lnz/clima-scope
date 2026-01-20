# JSON Schema Specification for County Weather Report Output

**Document Version:** 1.0  
**Prepared by:** Person B  
**Date:** 2026-01-06  
**Status:** Approved for Implementation

---

## 1. Document Purpose

This document defines the JSON schema for the county weather report output. The schema standardizes the structure of JSON data produced by the system, enabling validation, documentation, and consistent data exchange between frontend and backend components.

---

## 2. Schema Overview

### 2.1 Schema Version
- **Current Version:** 1.0
- **Format:** JSON Schema Draft 7
- **Location:** `schemas/county-weather-report.schema.json`
- **TypeScript Definition:** `lib/json-schema.ts`

### 2.2 Design Principles

1. **Nested Structure** - Optimized for dashboard consumption (React/Vue)
2. **Type Safety** - Strict validation with minimum/maximum constraints
3. **Extensibility** - Versioned schema for future compatibility
4. **Completeness** - All required fields clearly defined
5. **Documentation** - Comprehensive descriptions and examples

---

## 3. Root Schema Structure

### 3.1 Required Fields

```json
{
  "schema_version": "1.0",
  "county_id": "31",
  "county_name": "Nairobi",
  "period": { "start": "2026-01-19", "end": "2026-01-25" },
  "variables": { /* ... */ },
  "metadata": { /* ... */ }
}
```

### 3.2 Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | Yes | Schema version (e.g., "1.0") |
| `county_id` | string | Yes | KNBS 2-digit county code |
| `county_name` | string | Yes | Full official county name |
| `period` | object | Yes | Report period (7-day week) |
| `variables` | object | Yes | Weather variables (temp, rain, wind) |
| `wards` | array | No | Ward-level summaries |
| `extremes` | object | No | Extreme values |
| `metadata` | object | Yes | Generation metadata |
| `disclaimer` | string | No | Legal disclaimer |
| `quality_flags` | object | No | Data quality indicators |

---

## 4. Variable Schemas

### 4.1 Temperature Data

**Structure:**
```json
{
  "weekly": {
    "mean": 24.8,
    "max": 28.2,
    "min": 19.1
  },
  "daily": [26.1, 27.3, 28.2, 25.8, 24.1, 23.9, 22.7],
  "units": "°C",
  "anomaly": 1.2,
  "daily_min": [18.5, 19.2, 20.1, 18.8, 17.9, 17.5, 16.8],
  "daily_mean": [22.3, 23.2, 24.1, 22.3, 21.0, 20.7, 19.7]
}
```

**Constraints:**
- `weekly.mean/max/min`: -50 to 50°C
- `daily`: Exactly 7 values (Mon-Sun)
- `units`: Always "°C"
- `anomaly`: Optional, -20 to 20°C

### 4.2 Rainfall Data

**Structure:**
```json
{
  "weekly": {
    "total": 34.7,
    "max_intensity": 18.2,
    "rainy_days": 5
  },
  "daily": [2.1, 8.4, 12.7, 5.3, 3.9, 1.2, 1.1],
  "units": "mm",
  "probability_above_normal": 65.5
}
```

**Constraints:**
- `weekly.total`: 0 to 1000 mm
- `weekly.max_intensity`: 0 to 500 mm/day
- `daily`: Exactly 7 values, all ≥ 0
- `units`: Always "mm"
- `probability_above_normal`: 0 to 100%

### 4.3 Wind Data

**Structure:**
```json
{
  "weekly": {
    "mean_speed": 12.5,
    "max_gust": 25.3,
    "dominant_direction": "NE"
  },
  "units": "km/h",
  "daily_peak": [15.2, 18.7, 22.1, 16.3, 14.8, 13.5, 12.9],
  "daily_direction": ["NE", "NE", "E", "NE", "N", "N", "NE"]
}
```

**Constraints:**
- `weekly.mean_speed/max_gust`: 0 to 200 km/h
- `weekly.dominant_direction`: Cardinal/intercardinal (N, S, E, W, NE, NW, SE, SW, etc.)
- `daily_peak`: Exactly 7 values, all ≥ 0
- `units`: Always "km/h"

---

## 5. Ward Summary Schema

**Structure:**
```json
{
  "ward_id": "3101",
  "ward_name": "Kibera",
  "rainfall_total": 48.2,
  "temp_max": 27.1,
  "temp_min": 18.5,
  "temp_mean": 22.8,
  "wind_max": 28.3,
  "wind_mean": 14.2,
  "grid_points_used": 12,
  "quality_flag": "good"
}
```

**Constraints:**
- `ward_id`: 4-6 digit string (county code + ward number)
- `quality_flag`: "good" | "degraded" | "missing"
- All numeric fields have appropriate min/max constraints

---

## 6. Extreme Values Schema

**Structure:**
```json
{
  "highest_rainfall": {
    "ward_id": "31015",
    "ward_name": "Kasarani",
    "value": 68.2,
    "days": [2, 3]
  },
  "hottest_ward": {
    "ward_id": "3102",
    "ward_name": "Westlands",
    "value": 28.5,
    "day": 2
  },
  "windiest_ward": {
    "ward_id": "3101",
    "ward_name": "Kibera",
    "value": 28.3
  },
  "flood_risk_wards": [
    {
      "ward_id": "31015",
      "ward_name": "Kasarani",
      "risk_level": "moderate",
      "total_rainfall": 68.2
    }
  ]
}
```

---

## 7. Metadata Schema

**Structure:**
```json
{
  "data_source": "GFS",
  "model_run": "2026-01-18T00:00:00Z",
  "generated": "2026-01-18T09:30:00Z",
  "aggregation_method": "point-in-polygon",
  "grid_resolution": "0.25°",
  "grid_points_used": 184,
  "warnings": [],
  "system_version": "1.0.0",
  "processing_duration_seconds": 45.3
}
```

**Required Fields:**
- `data_source`: "GFS" | "GFS+OBS"
- `model_run`: ISO 8601 datetime
- `generated`: ISO 8601 datetime
- `aggregation_method`: "point-in-polygon" | "area-weighted"
- `grid_resolution`: String (e.g., "0.25°")
- `grid_points_used`: Integer ≥ 0

---

## 8. Quality Flags Schema

**Structure:**
```json
{
  "overall_quality": "good",
  "missing_data_percent": 0,
  "spatial_coverage_percent": 100,
  "warnings": []
}
```

**Quality Levels:**
- `excellent`: All data valid, no issues
- `good`: Minor issues, data usable
- `fair`: Some data missing or questionable
- `degraded`: Significant data quality issues

---

## 9. Data Types Summary

| Field Type | JSON Type | Examples | Constraints |
|------------|-----------|----------|-------------|
| County ID | string | "31", "01" | 2 digits, pattern: `^\d{2}$` |
| Dates | string | "2026-01-19" | ISO 8601 date format |
| Timestamps | string | "2026-01-18T00:00:00Z" | ISO 8601 datetime |
| Temperature | number | 24.8 | -50 to 50 |
| Rainfall | number | 34.7 | 0 to 1000 |
| Wind Speed | number | 12.5 | 0 to 200 |
| Wind Direction | string | "NE" | Cardinal/intercardinal |
| Arrays | array | [26.1, 27.3, ...] | Fixed length (7 for daily) |
| Enums | string | "GFS", "good" | Limited set of values |

---

## 10. Nested vs Flat Structure

### 10.1 Nested Structure (Default)

**Use Case:** Dashboard consumption, API responses

**Advantages:**
- Clean hierarchical organization
- Easy to consume in React/Vue components
- Logical grouping of related data
- Reduces data duplication

**Example:**
```json
{
  "county_name": "Nairobi",
  "variables": {
    "temperature": { "weekly": { "mean": 24.8 } }
  },
  "wards": [
    { "ward_id": "3101", "rainfall_total": 48.2 }
  ]
}
```

### 10.2 Flat Structure (CSV Export)

**Use Case:** CSV export, tabular analysis

**Conversion:** Use `flattenReportForCSV()` function

**Example:**
```json
[
  {
    "county_id": "31",
    "county_name": "Nairobi",
    "ward_id": "3101",
    "ward_name": "Kibera",
    "rainfall_total": 48.2,
    "temp_mean": 22.8
  }
]
```

---

## 11. Validation

### 11.1 Schema Validation

**Python (jsonschema library):**
```python
import jsonschema
import json

with open('schemas/county-weather-report.schema.json') as f:
    schema = json.load(f)

jsonschema.validate(instance=report_data, schema=schema)
```

**TypeScript (ajv library):**
```typescript
import Ajv from 'ajv'
import schema from './schemas/county-weather-report.schema.json'

const ajv = new Ajv()
const validate = ajv.compile(schema)
const valid = validate(reportData)
```

### 11.2 Type Guards

**TypeScript:**
```typescript
import { isValidCountyReport } from './lib/json-schema'

if (isValidCountyReport(data)) {
  // TypeScript knows data matches schema
  console.log(data.county_name)
}
```

---

## 12. Complete Example

See `lib/json-schema.ts` for `EXAMPLE_REPORT` constant containing a complete, valid example.

---

## 13. Versioning Strategy

### 13.1 Schema Version Format
- Format: `MAJOR.MINOR` (e.g., "1.0", "1.1", "2.0")
- Major: Breaking changes (removed fields, type changes)
- Minor: Additive changes (new optional fields)

### 13.2 Compatibility

**Backward Compatible Changes (Minor):**
- Adding optional fields
- Adding enum values
- Relaxing constraints (e.g., increasing max)

**Breaking Changes (Major):**
- Removing required fields
- Changing field types
- Making optional fields required
- Tightening constraints

### 13.3 Migration

When schema version changes:
1. Update `schema_version` field
2. Document changes in changelog
3. Provide migration utilities if needed
4. Support multiple versions during transition

---

## 14. Usage Guidelines

### 14.1 For Backend (Python)

1. Generate JSON matching schema
2. Validate before sending to frontend
3. Use schema for API documentation
4. Include `schema_version` in all outputs

### 14.2 For Frontend (TypeScript)

1. Use TypeScript interfaces from `lib/json-schema.ts`
2. Validate API responses against schema
3. Handle quality flags for user feedback
4. Use flattening utilities for CSV export

### 14.3 For CSV Export

```typescript
import { flattenReportForCSV } from './lib/json-schema'

const flatData = flattenReportForCSV(report)
// Convert to CSV using csv-writer or similar
```

---

## 15. File Locations

- **JSON Schema:** `schemas/county-weather-report.schema.json`
- **TypeScript Types:** `lib/json-schema.ts`
- **Documentation:** `docs/JSON_SCHEMA_SPECIFICATION.md` (this file)
- **Example Data:** `lib/json-schema.ts` (EXAMPLE_REPORT constant)

---

## 16. References

- JSON Schema Specification: https://json-schema.org/
- JSON Schema Draft 7: https://json-schema.org/draft-07/schema
- ISO 8601 Date Format: https://en.wikipedia.org/wiki/ISO_8601
- KNBS County Codes: Kenya National Bureau of Statistics

---

**End of Specification Document**

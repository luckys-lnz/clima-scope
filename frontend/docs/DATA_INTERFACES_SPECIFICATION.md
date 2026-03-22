# Data Interfaces & Schemas Specification

**Document Version:** 1.0  
**Prepared by:** Person B  
**Date:** 2026-01-06  
**Status:** Approved for Implementation

---

## 1. Document Purpose

This document defines the complete data interfaces and schemas for the Automated Weekly County Weather Reporting system. It standardizes how data flows through the system from raw inputs (GFS GRIB files, shapefiles, observations) through processing to final report outputs.

---

## 2. Data Flow Overview

```
┌─────────────────┐
│  INPUT SCHEMAS  │
├─────────────────┤
│ • GFS GRIB      │
│ • Shapefiles    │
│ • Observations  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ PROCESSING      │
│ SCHEMAS         │
├─────────────────┤
│ • Spatial Join  │
│ • Aggregation   │
│ • County Summary│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ OUTPUT SCHEMAS  │
├─────────────────┤
│ • Report        │
│   Components    │
│ • Maps          │
│ • Narratives    │
└─────────────────┘
```

---

## 3. Input Schemas

### 3.1 GFS GRIB File Interface

**Purpose:** Standardize GFS forecast data loaded from GRIB2 files.

**Key Components:**
- `GFSGribFile` - Main file structure
- `GFSVariables` - Dictionary of weather variables
- `GFSVariableData` - Individual variable with data array
- `GFSDataArray` - 3D gridded data structure

**Data Sources:**
- NOAA/NCEP OpenDAP servers
- FTP servers (nomads.ncep.noaa.gov)
- Local cached files

**Variables Included:**
- `total_precipitation` (apcpsfc) - Surface accumulated precipitation
- `t2m` - 2-meter temperature
- `u10m`, `v10m` - 10-meter wind components
- Optional: `rh2m` (humidity), `sp` (surface pressure)

**Grid Specifications:**
- Resolution: 0.25° (approximately 25km)
- Coverage: Global
- Forecast horizon: 7 days (168 hours)
- Time steps: 3-hourly (0, 3, 6, ..., 168)

**Example Usage:**
```typescript
const gfsFile: GFSGribFile = {
  filePath: "gfs.t00z.pgrb2.0p25.f000",
  modelRun: "2026-01-14T00:00:00Z",
  forecastHours: [0, 3, 6, ..., 168],
  variables: {
    total_precipitation: { /* ... */ },
    t2m: { /* ... */ },
    // ...
  },
  // ...
}
```

---

### 3.2 Administrative Boundaries Interface

**Purpose:** Standardize county and ward boundary data from shapefiles.

**Key Components:**
- `AdminBoundary` - County with wards
- `WardBoundary` - Individual ward geometry
- `Geometry` - GeoJSON-compatible geometry
- `BoundaryMetadata` - Source and CRS information

**Data Sources:**
- KNBS (Kenya National Bureau of Statistics)
- HDX (Humanitarian Data Exchange)
- OpenAfrica
- GADM

**Coordinate System:**
- Primary: EPSG:4326 (WGS84)
- May be reprojected to UTM Zone 37N (EPSG:32637) for mapping

**Structure:**
- County level: One polygon per county
- Ward level: One polygon per ward (1,450+ wards across 47 counties)
- Hierarchical: Wards belong to counties

**Example Usage:**
```typescript
const boundary: AdminBoundary = {
  countyId: "31",
  countyName: "Nairobi",
  countyGeometry: { /* ... */ },
  wards: [
    {
      wardId: "31001",
      wardName: "Westlands",
      geometry: { /* ... */ },
      countyId: "31"
    },
    // ...
  ],
  metadata: {
    source: "KNBS",
    version: "2024",
    crs: "EPSG:4326",
    // ...
  }
}
```

---

### 3.3 Observational Data Interface (Optional)

**Purpose:** Standardize weather station observations for validation and enhancement.

**Key Components:**
- `StationObservation` - County-level station data
- `WeatherStation` - Individual station
- `StationSummary` - 7-day aggregated observations
- `DailyObservation` - Daily station readings

**Data Sources:**
- KMD (Kenya Meteorological Department)
- NOAA GSOD (Global Summary of the Day)
- WMO WIS (World Information System)
- Custom station networks

**Use Cases:**
- Validate forecast accuracy
- Enhance forecasts with local observations
- Provide context for forecast interpretation
- Historical comparison

**Example Usage:**
```typescript
const observations: StationObservation = {
  countyId: "31",
  stations: [
    {
      stationId: "KMD001",
      stationName: "Nairobi JKIA",
      coordinates: { latitude: -1.3192, longitude: 36.9278 },
      past7Days: {
        totalRainfallMm: 45.2,
        meanTempC: 22.5,
        // ...
      }
    }
  ],
  // ...
}
```

---

## 4. Processing Schemas

### 4.1 Spatial Aggregation

**Process:** Map GFS grid points to ward polygons using spatial join.

**Key Interfaces:**
- `SpatialJoinResult` - Result of point-in-polygon operation
- `WardForecast` - Aggregated forecast per ward

**Aggregation Methods:**
1. **Point-in-Polygon (Mean)** - Average all grid points within ward
2. **Point-in-Polygon (Max/Min)** - Use maximum/minimum value
3. **Area-Weighted Mean** - Weight by grid cell area overlap
4. **Area-Weighted Sum** - For accumulated variables (rainfall)

**Processing Steps:**
1. Load GFS data → xarray Dataset
2. Clip to county bounding box
3. Spatial join: `gdf_wards.sjoin(gdf_gfs_points, predicate='contains')`
4. Group by `ward_id` → compute statistics
5. Validate (check for NaN, missing data)

**Example:**
```typescript
const wardForecast: WardForecast = {
  wardId: "31001",
  countyId: "31",
  variable: "rainfall",
  weeklyTotal: 45.2,
  daily: [5.2, 8.1, 12.3, 6.7, 4.2, 5.8, 2.9],
  aggregationMethod: "point-in-polygon_mean",
  gridPointsUsed: 12,
  qualityFlag: "good",
  units: "mm"
}
```

---

### 4.2 County Summary

**Process:** Aggregate ward-level data to county-level statistics.

**Key Interface:**
- `CountyReportData` - County-level summary

**Aggregations:**
- **Rainfall:** Total, mean, max/min wards, rainy days
- **Temperature:** Mean, max, min, hottest/coolest wards
- **Wind:** Mean speed, max gust, dominant direction, windiest ward
- **Extremes:** Identify extreme wards for each variable

**Example:**
```typescript
const countyData: CountyReportData = {
  countyName: "Nairobi",
  countyId: "31",
  rainfall: {
    meanMm: 42.5,
    totalMm: 297.5,
    maxWard: { wardId: "31015", wardName: "Kasarani", value: 68.2 },
    // ...
  },
  // ...
}
```

---

## 5. Output Schemas

### 5.1 Report Components

**Purpose:** Structure data for PDF generation.

**Key Interface:**
- `ReportComponents` - Complete report structure

**Components:**
1. **Header** - County, period, disclaimers
2. **Maps** - Generated map images (PNG/JPEG/SVG)
3. **Narrative** - Generated text sections
4. **Tables** - Ward statistics, daily summaries, extremes
5. **Metadata** - Generation info, data sources

**Map Generation:**
- Format: PNG (300 DPI minimum)
- Projection: UTM Zone 37N (EPSG:32637) or WGS84
- Color scales: Defined per variable
- Resolution: High enough for print quality

**Narrative Generation:**
- Template-based with data-driven customization
- Sections: Overview, Rainfall, Temperature, Wind, Advisories
- Tone: Professional, objective, advisory

**Example:**
```typescript
const reportComponents: ReportComponents = {
  header: {
    county: "Nairobi",
    validPeriod: "Week 50, 2024 (December 2 - December 8, 2024)",
    // ...
  },
  maps: {
    rainfallWard: "/path/to/rainfall_map.png",
    temperatureWard: "/path/to/temp_map.png",
    // ...
  },
  narrative: {
    overview: "This week in Nairobi County...",
    // ...
  },
  // ...
}
```

---

## 6. Data Validation

### 6.1 Validation Functions

**Purpose:** Ensure data quality and completeness at each stage.

**Key Functions:**
- `validateGFSFile()` - Check GFS file structure
- `validateAdminBoundary()` - Check boundary data
- `validateWardForecast()` - Check aggregated data
- `calculateDataQuality()` - Compute quality scores

**Validation Checks:**
- Required fields present
- Data types correct
- Value ranges reasonable (Kenya-specific)
- No NaN or missing values
- Spatial coverage adequate
- Temporal coverage complete

**Quality Flags:**
- `good` - All data valid
- `degraded` - Some data missing or questionable
- `missing` - Critical data missing

---

## 7. Data Flow Validation

### 7.1 Processing Pipeline

**Step 1: Parse GFS**
- Load GRIB file → xarray Dataset
- Extract required variables
- Validate structure

**Step 2: Spatial Join**
- Clip GFS to county bounding box
- Perform point-in-polygon operation
- Map grid points to wards

**Step 3: Aggregation**
- Group by ward_id
- Compute statistics (mean, max, min, sum)
- Handle edge cases (no points in ward)

**Step 4: Validation**
- Check for NaN values
- Validate ranges
- Flag quality issues

**Step 5: County Summary**
- Aggregate ward data to county
- Identify extremes
- Compute summary statistics

**Step 6: Report Generation**
- Generate maps
- Generate narratives
- Assemble tables
- Create PDF

---

## 8. Implementation Notes

### 8.1 Python Backend Integration

**Libraries:**
- `xarray` - GRIB file handling
- `geopandas` - Spatial operations
- `shapely` - Geometry operations
- `pygrib` or `cfgrib` - GRIB parsing

**Data Conversion:**
- Python xarray → JSON → TypeScript interfaces
- GeoPandas GeoDataFrame → GeoJSON → TypeScript interfaces
- Use JSON schema validation

### 8.2 Type Safety

**TypeScript Strict Mode:**
- All interfaces are strictly typed
- No `any` types
- Optional fields marked with `?`
- Union types for enums

**Runtime Validation:**
- Use Zod or similar for runtime validation
- Validate data at API boundaries
- Type guards for discriminated unions

---

## 9. File Structure

```
lib/
├── data-interfaces.ts      # All data interfaces (this spec)
├── weather-schemas.ts      # Existing weather report schemas
└── report-structure.ts     # Report structure interfaces
```

---

## 10. Future Enhancements

**Potential Additions:**
- Ensemble forecast support (multiple models)
- Historical data interfaces
- Real-time data streaming interfaces
- API request/response schemas
- Database schema definitions
- Caching layer interfaces

---

## 11. References

- GFS Documentation: https://www.ncep.noaa.gov/products/gfs/
- GeoPandas Documentation: https://geopandas.org/
- xarray Documentation: https://xarray.pydata.org/
- GeoJSON Specification: https://geojson.org/
- KNBS Administrative Boundaries

---

**End of Specification Document**

# Map Embedding Strategy - Implementation Summary

**Date:** 2026-01-18  
**Prepared by:** Person B  
**Status:** Specification Complete

---

## Overview

The Map Embedding Strategy specification defines how generated weather maps are placed, formatted, and integrated into PDF reports and web dashboards. This document provides a complete strategy for consistent, high-quality map presentation across all output formats.

---

## Deliverables

### 1. Specification Document
**File:** `docs/MAP_EMBEDDING_STRATEGY.md`

Comprehensive specification covering:
- PDF report embedding (section maps and full-page maps)
- Web dashboard embedding (card maps and detail views)
- Map generation specifications
- Color schemes and cartographic elements
- File formats, resolutions, and quality standards
- Integration points with existing report structure

### 2. TypeScript Implementation
**File:** `lib/map-embedding.ts`

Complete TypeScript interfaces and utilities:
- `MapGenerationConfig` - Configuration for map generation
- `MapMetadata` - Metadata for generated maps
- `PDFMapEmbedding` - PDF embedding configuration
- `WebMapDisplay` - Web display configuration
- `MapEmbeddingStrategy` - Complete embedding strategy
- Default configurations and helper functions

---

## Key Features

### PDF Report Embedding

**Section Maps (Inline):**
- Size: 170mm × 120mm (60% page width)
- Resolution: 300 DPI minimum
- Format: PNG (preferred) or JPEG
- Position: Centered below narrative, above tables
- Includes: Title, legend, scale bar, caption

**Full-Page Maps:**
- Size: Full page (170mm × 257mm for A4)
- Resolution: 400 DPI preferred
- Format: PNG or vector graphics
- Position: Dedicated page, centered
- Includes: All cartographic elements (title, legend, scale, north arrow)

### Web Dashboard Embedding

**Dashboard Cards:**
- Size: Responsive, minimum 300px × 200px
- Resolution: 150 DPI (2x for retina)
- Format: WebP with PNG fallback
- Features: Hover effects, lazy loading, error handling

**Detail Views:**
- Size: Full viewport width, 80vh max height
- Resolution: 200 DPI (2x for retina)
- Format: High-resolution PNG/WebP
- Features: Zoom, pan, download, fullscreen

### Color Schemes

**Rainfall Maps:**
- Blue gradient: Light blue (#E3F2FD) to very dark blue (#0D47A1)
- 5 ranges: 0-20mm, 20-40mm, 40-60mm, 60-80mm, 80mm+

**Temperature Maps:**
- Cool to warm gradient: Blue (#2196F3) to Red (#F44336)
- 5 ranges: <18°C, 18-22°C, 22-26°C, 26-30°C, >30°C

**Wind Speed Maps:**
- Light to dark green gradient: Light green (#E8F5E9) to very dark green (#2E7D32)
- 5 ranges: 0-10 km/h, 10-15 km/h, 15-20 km/h, 20-25 km/h, 25+ km/h

### Cartographic Elements

All maps include:
- Title block with variable name, units, date range
- Legend with color scale and value ranges
- Scale bar (kilometers)
- North arrow (full-page maps)
- Ward boundaries (0.5pt) and county boundary (1pt)
- Optional: Ward labels, coordinate grid

---

## Integration Points

### Report Structure

Maps are integrated into the report structure through:

1. **Section Maps** (Sections 4, 5, 6):
   - `RainfallOutlook.rainfallDistributionMap`
   - `TemperatureOutlook.temperatureDistributionMap`
   - `WindOutlook.windSpeedDistributionMap`

2. **Full-Page Maps** (Section 7):
   - `WardLevelVisualizations.rainfallMap`
   - `WardLevelVisualizations.temperatureMap`
   - `WardLevelVisualizations.windSpeedMap`

3. **Data Interfaces:**
   - `ReportMaps` interface in `lib/data-interfaces.ts`
   - Maps referenced by `imagePath` (file path, base64, or URL)

### Web Components

**Existing Components:**
- `MapPlaceholder` - Placeholder for dashboard cards
- Used in `CountyDetail` component for map previews

**Future Components:**
- `MapDisplay` - Reusable map display component
- `InteractiveMap` - Interactive map with zoom/pan
- `MapModal` - Full-screen map modal

---

## File Organization

### Generated Maps Storage

**File System Structure:**
```
reports/
  maps/
    [county-id]/
      [date]/
        [county-id]_[variable]_[date]_[context]_[resolution]dpi.[ext]
```

**Example:**
```
reports/maps/31/2026-01-19/
  31_rainfall_2026-01-19_section_300dpi.png
  31_rainfall_2026-01-19_fullpage_400dpi.png
  31_temperature_2026-01-19_section_300dpi.png
  31_temperature_2026-01-19_fullpage_400dpi.png
  31_wind_2026-01-19_section_300dpi.png
  31_wind_2026-01-19_fullpage_400dpi.png
```

### Web-Optimized Versions

**Web Storage:**
```
public/maps/
  [county-id]/
    [variable]/
      [date].webp
      [date].png (fallback)
```

---

## Quality Standards

### Resolution Requirements
- PDF Section Maps: 300 DPI minimum
- PDF Full-Page Maps: 400 DPI preferred
- Web Dashboard Cards: 150 DPI (displayed at 2x)
- Web Detail Views: 200 DPI (displayed at 2x)

### File Size Targets
- PDF Section Maps: < 500KB
- PDF Full-Page Maps: < 2MB
- Web Dashboard Cards: < 200KB
- Web Detail Views: < 1MB

### Visual Quality
- Sharp, anti-aliased boundaries
- Smooth color gradients (no banding)
- Readable text at intended size
- Professional appearance suitable for institutional use

---

## Implementation Guidelines

### Map Generation Pipeline

1. **Data Preparation**
   - Aggregate ward-level data
   - Calculate value ranges
   - Identify missing data

2. **Map Rendering**
   - Generate base map with boundaries
   - Apply color scheme
   - Add cartographic elements
   - Add title and metadata

3. **Format Export**
   - Export at required resolutions
   - Optimize file sizes
   - Generate web-optimized versions

4. **Storage**
   - Store in organized directory structure
   - Generate metadata
   - Update report structure

### PDF Embedding

**Method 1: Base64 (Preferred)**
- Convert map to base64 string
- Embed directly in PDF
- Single-file distribution

**Method 2: File Reference**
- Reference file path
- PDF library includes file during generation
- Requires file system access

### Web Integration

**API Endpoints:**
- `GET /api/maps/[county-id]/[variable]/[date]` - Get map image
- `GET /api/maps/[county-id]/[variable]/[date]/metadata` - Get metadata

**Optimization:**
- WebP format with PNG fallback
- Lazy loading for below-the-fold maps
- Responsive images based on viewport
- CDN delivery for performance

---

## Testing Requirements

### Visual Testing
- Print test: Generate PDF and print at 100% scale
- Screen test: View on various screen sizes
- Color test: Verify colorblind-friendly alternatives
- Quality test: Check for pixelation, banding, artifacts

### Functional Testing
- PDF: Verify all maps render correctly
- Web: Test loading, interactions, responsive behavior
- Performance: Measure load times, file sizes
- Cross-browser: Test in Chrome, Firefox, Safari, Edge

---

## Next Steps

1. **Backend Implementation:**
   - Implement map generation pipeline (Python/GeoPandas)
   - Create API endpoints for map retrieval
   - Set up storage system (file system or cloud)

2. **Frontend Integration:**
   - Create `MapDisplay` component
   - Implement interactive map features
   - Add map modal/detail views

3. **PDF Generation:**
   - Integrate map embedding into PDF generation
   - Test base64 vs. file reference methods
   - Optimize PDF file sizes

4. **Quality Assurance:**
   - Visual testing across devices
   - Performance optimization
   - Accessibility improvements

---

## Related Documents

- `docs/REPORT_STRUCTURE_SPECIFICATION.md` - Report structure with map sections
- `docs/DATA_INTERFACES_SPECIFICATION.md` - Data interfaces including map references
- `lib/report-structure.ts` - Report structure TypeScript interfaces
- `lib/data-interfaces.ts` - Data interface definitions
- `lib/map-embedding.ts` - Map embedding TypeScript implementation

---

**End of Summary**

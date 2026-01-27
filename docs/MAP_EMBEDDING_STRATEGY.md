# Map Embedding Strategy Specification

**Document Version:** 1.0  
**Prepared by:** Person B  
**Date:** 2026-01-18  
**Status:** Approved for Implementation

---

## 1. Document Purpose

This document defines the complete strategy for embedding, formatting, and integrating generated weather maps into PDF reports and web dashboards. It ensures consistent presentation, optimal quality, and clear visual communication across all output formats.

---

## 2. Overview

### 2.1 Map Types

The system generates three primary map types:

1. **Rainfall Distribution Maps** - Ward-level total rainfall visualization
2. **Temperature Distribution Maps** - Ward-level mean temperature visualization  
3. **Wind Speed Distribution Maps** - Ward-level maximum wind speed visualization

### 2.2 Output Contexts

Maps are embedded in two primary contexts:

1. **PDF Reports** - Static, high-resolution maps for print and digital distribution
2. **Web Dashboards** - Interactive, responsive maps for online viewing

### 2.3 Map Appearances

Maps appear in multiple locations within reports:

- **Section Maps** - Inline maps within variable-specific sections (Rainfall, Temperature, Wind Outlook)
- **Full-Page Maps** - Dedicated pages in Ward-Level Visualizations section
- **Dashboard Cards** - Compact preview maps in web interface
- **Detail Views** - Full-screen interactive maps in web interface

---

## 3. PDF Report Embedding

### 3.1 Section Maps (Inline)

**Context:** Maps embedded within Rainfall, Temperature, and Wind Outlook sections.

**Specifications:**
- **Size:** 170mm × 120mm (6.7" × 4.7") - approximately 60% of page width
- **Position:** Centered below narrative text, above tables/charts
- **Resolution:** 300 DPI minimum
- **Format:** PNG (preferred) or JPEG (if file size is critical)
- **Border:** 1pt solid border, color: #CCCCCC
- **Padding:** 5mm margin around map
- **Caption:** Below map, 9pt italic, format: "Figure X: [Map Title] - [Date Range]"

**Layout Example:**
```
[Narrative Text - 2-3 paragraphs]
[5mm spacing]
[Map: 170mm × 120mm, centered]
[Caption: "Figure 1: 7-Day Total Rainfall Distribution (mm) - Week 3, 2026"]
[5mm spacing]
[Tables/Charts]
```

### 3.2 Full-Page Maps

**Context:** Maps in Ward-Level Visualizations section (Section 7).

**Specifications:**
- **Size:** Full page minus margins (170mm × 257mm for A4 with 20mm margins)
- **Position:** Centered on dedicated page
- **Resolution:** 300 DPI minimum (preferred: 400 DPI for high-quality printing)
- **Format:** PNG (preferred) or vector graphics (SVG embedded as raster)
- **Border:** None (edge-to-edge within margins)
- **Page Break:** Each map on separate page
- **Title:** Top of page, 16pt bold, format: "[Variable] Distribution Map - [County Name]"
- **Subtitle:** Below title, 11pt regular, format: "Week [XX], [YYYY] ([Start Date] - [End Date])"

**Layout Example:**
```
[Page Break]
[Title: 16pt bold, centered]
[Subtitle: 11pt, centered]
[5mm spacing]
[Map: Full page, 170mm × 257mm]
[Legend: Bottom right, 10pt]
[Scale Bar: Bottom left]
[North Arrow: Top right]
[Footer: Page number, report title]
```

### 3.3 Map Elements (Cartographic Components)

All maps must include:

1. **Title Block**
   - Variable name and units
   - Date range
   - County name

2. **Legend**
   - Color scale with value ranges
   - Position: Bottom right (section maps) or bottom center (full-page)
   - Font: 9pt regular
   - Border: 1pt solid, background: white with 80% opacity

3. **Scale Bar**
   - Position: Bottom left
   - Units: Kilometers
   - Style: Professional, clear divisions

4. **North Arrow**
   - Position: Top right (full-page maps only)
   - Style: Simple, professional

5. **Ward Boundaries**
   - Line width: 0.5pt for ward boundaries, 1pt for county boundary
   - Color: #333333 for wards, #000000 for county
   - Style: Solid lines

6. **Ward Labels** (Optional)
   - Only if readable at map scale
   - Font: 7pt regular
   - Color: #000000
   - Position: Centered in ward polygon

7. **Coordinate Grid** (Optional, full-page only)
   - Light grid lines (0.25pt, #CCCCCC)
   - Coordinate labels in margins
   - Format: Decimal degrees or UTM

### 3.4 Color Schemes

#### Rainfall Maps
- **Color Scale:** Blue gradient (light to dark)
- **Ranges:** 
  - 0-20mm: #E3F2FD (light blue)
  - 20-40mm: #90CAF9 (medium blue)
  - 40-60mm: #42A5F5 (blue)
  - 60-80mm: #1E88E5 (dark blue)
  - 80mm+: #0D47A1 (very dark blue)
- **No Data:** #CCCCCC (gray)

#### Temperature Maps
- **Color Scale:** Cool to warm gradient
- **Ranges:**
  - <18°C: #2196F3 (blue)
  - 18-22°C: #4CAF50 (green)
  - 22-26°C: #FFEB3B (yellow)
  - 26-30°C: #FF9800 (orange)
  - >30°C: #F44336 (red)
- **No Data:** #CCCCCC (gray)

#### Wind Speed Maps
- **Color Scale:** Light to dark gradient
- **Ranges:**
  - 0-10 km/h: #E8F5E9 (light green)
  - 10-15 km/h: #A5D6A7 (green)
  - 15-20 km/h: #66BB6A (medium green)
  - 20-25 km/h: #43A047 (dark green)
  - 25+ km/h: #2E7D32 (very dark green)
- **No Data:** #CCCCCC (gray)

**Colorblind-Friendly Alternative:**
- Use sequential color schemes with distinct lightness levels
- Test with colorblind simulation tools
- Provide pattern overlays for critical distinctions (optional)

### 3.5 Image Format Specifications

#### PNG Format (Preferred)
- **Compression:** Lossless (PNG-24)
- **Color Depth:** 24-bit RGB
- **Transparency:** Not required (white background)
- **Use Case:** All PDF maps, especially full-page maps

#### JPEG Format (Alternative)
- **Quality:** 95% minimum
- **Color Space:** sRGB
- **Use Case:** Section maps when file size is critical
- **Limitation:** Not recommended for full-page maps

#### SVG Format (Future)
- **Use Case:** Vector graphics for scalability
- **Implementation:** Convert to raster (PNG) for PDF embedding
- **Note:** PDF libraries may support direct SVG embedding

### 3.6 File Naming Convention

**Format:** `[county-id]_[variable]_[period-start]_[resolution].png`

**Examples:**
- `31_rainfall_2026-01-19_300dpi.png`
- `31_temperature_2026-01-19_300dpi.png`
- `31_wind_2026-01-19_300dpi.png`

**Full-Page Maps:**
- `31_rainfall_2026-01-19_fullpage_400dpi.png`

**Section Maps:**
- `31_rainfall_2026-01-19_section_300dpi.png`

### 3.7 Storage and Reference

**Storage Options:**
1. **File System:** Maps stored in `reports/maps/[county-id]/[date]/`
2. **Base64 Embedding:** Maps embedded directly in PDF (preferred for single-file distribution)
3. **Cloud Storage:** Maps stored in S3/cloud storage, referenced by URL

**PDF Embedding Method:**
- **Preferred:** Base64-encoded images embedded directly in PDF
- **Alternative:** File paths (requires file system access for PDF viewing)
- **Metadata:** Include map generation timestamp, resolution, format in PDF metadata

---

## 4. Web Dashboard Embedding

### 4.1 Dashboard Card Maps

**Context:** Compact map previews in county detail views and dashboard overview.

**Specifications:**
- **Size:** Responsive, minimum 300px × 200px
- **Aspect Ratio:** 16:9 or 3:2
- **Format:** Web-optimized PNG or JPEG
- **Resolution:** 150 DPI (sufficient for screen display)
- **File Size:** < 200KB (optimized for web)
- **Border:** 1px solid, color: theme border color
- **Border Radius:** 8px (rounded corners)
- **Hover Effect:** Slight scale (1.02x) and shadow on hover
- **Loading State:** Skeleton loader or placeholder

**Layout Example:**
```tsx
<div className="bg-card rounded-lg border border-border overflow-hidden">
  <MapImage 
    src={mapUrl}
    alt="Rainfall Distribution"
    className="w-full h-48 object-cover"
  />
  <div className="p-4">
    <h3 className="font-semibold text-sm">Rainfall Distribution</h3>
    <p className="text-xs text-muted-foreground">7-day total (mm)</p>
  </div>
</div>
```

### 4.2 Detail View Maps

**Context:** Full-screen or large modal views of maps.

**Specifications:**
- **Size:** Full viewport width (responsive)
- **Maximum Height:** 80vh
- **Format:** High-resolution PNG (300 DPI source, served at 2x for retina displays)
- **Resolution:** 150-200 DPI for display (served at 2x for retina)
- **File Size:** < 1MB (optimized)
- **Controls:** Zoom, pan, download, fullscreen
- **Overlay:** Legend toggle, layer controls (if applicable)

**Interactive Features:**
- **Hover:** Show ward name and value on hover
- **Click:** Navigate to ward detail (if implemented)
- **Zoom:** Pinch-to-zoom on mobile, scroll wheel on desktop
- **Pan:** Drag to pan map
- **Download:** Button to download full-resolution map

### 4.3 Responsive Breakpoints

**Mobile (< 768px):**
- Card maps: Full width, stacked vertically
- Detail maps: Full width, height: 50vh

**Tablet (768px - 1024px):**
- Card maps: 2 columns, 300px × 200px each
- Detail maps: Full width, height: 70vh

**Desktop (> 1024px):**
- Card maps: 3 columns, 300px × 200px each
- Detail maps: Full width, height: 80vh

### 4.4 Image Optimization

**Web Formats:**
- **Primary:** WebP (with PNG fallback)
- **Fallback:** PNG or JPEG
- **Compression:** Lossy WebP at 85% quality, or lossless PNG
- **Lazy Loading:** Implement lazy loading for below-the-fold maps
- **Responsive Images:** Serve different sizes based on viewport

**Implementation:**
```tsx
<picture>
  <source srcSet={`${mapUrl}.webp`} type="image/webp" />
  <img 
    src={`${mapUrl}.png`} 
    alt="Rainfall Distribution"
    loading="lazy"
    className="w-full h-auto"
  />
</picture>
```

### 4.5 Loading Strategies

**Progressive Loading:**
1. Show placeholder/skeleton while loading
2. Load low-resolution preview first (< 50KB)
3. Load full-resolution image in background
4. Smooth transition when full image loads

**Caching:**
- Cache map images in browser cache
- Use CDN for map image delivery
- Implement cache headers (Cache-Control: max-age=3600)

**Error Handling:**
- Show error message if map fails to load
- Provide retry button
- Fallback to placeholder with error state

---

## 5. Map Generation Specifications

### 5.1 Base Map Requirements

**Projection:**
- **Primary:** UTM Zone 37N (EPSG:32637) - appropriate for Kenya
- **Alternative:** WGS84 (EPSG:4326) for web maps
- **Note:** All maps must use consistent projection within a report

**Coordinate System:**
- **Bounds:** County extent with 10% buffer
- **Aspect Ratio:** Maintained to prevent distortion
- **Centering:** County centered in map frame

**Base Map Elements:**
- **Minimal Base:** Ward boundaries, county boundary only
- **No Background:** White or transparent background
- **No Labels:** Ward labels optional, only if readable

### 5.2 Data Visualization

**Aggregation Method:**
- **Ward Values:** Mean or total value per ward
- **Color Assignment:** Based on value ranges (see Color Schemes)
- **Missing Data:** Clearly indicated with gray color and "No Data" label

**Value Ranges:**
- **Dynamic Ranges:** Based on actual data distribution
- **Fixed Ranges:** Use standard meteorological ranges (see Color Schemes)
- **Legend:** Always show all range categories, even if not present in data

### 5.3 Quality Standards

**Resolution Requirements:**
- **PDF Section Maps:** 300 DPI minimum
- **PDF Full-Page Maps:** 400 DPI preferred
- **Web Dashboard Cards:** 150 DPI (displayed at 2x for retina)
- **Web Detail Views:** 200 DPI (displayed at 2x for retina)

**File Size Targets:**
- **PDF Section Maps:** < 500KB (PNG)
- **PDF Full-Page Maps:** < 2MB (PNG)
- **Web Dashboard Cards:** < 200KB (WebP/PNG)
- **Web Detail Views:** < 1MB (WebP/PNG)

**Visual Quality:**
- **Sharp Boundaries:** Clear, anti-aliased ward boundaries
- **Smooth Gradients:** No banding in color scales
- **Readable Text:** All text must be legible at intended size
- **Professional Appearance:** Suitable for government/institutional use

---

## 6. Integration Points

### 6.1 Report Structure Integration

**Section Maps (Sections 4, 5, 6):**
- Rainfall Outlook: Rainfall distribution map
- Temperature Outlook: Temperature distribution map
- Wind Outlook: Wind speed distribution map

**Full-Page Maps (Section 7):**
- Ward-Level Visualizations: Three full-page maps (one per variable)

**Map References:**
- Maps referenced by `imagePath` in report structure interfaces
- Path can be file path, base64 string, or URL

### 6.2 Data Interface Integration

**ReportMaps Interface:**
```typescript
interface ReportMaps {
  rainfallWard: string // file path, base64, or URL
  temperatureWard: string
  windSpeedWard: string
  countyOverview?: string
  mapMetadata: {
    resolution: number
    format: "PNG" | "JPEG" | "SVG"
    projection: string
    generatedAt: string
  }
}
```

**WardLevelVisualizations Interface:**
```typescript
interface WardLevelVisualizations {
  rainfallMap: {
    imagePath: string
    title: string
    resolution: string
    projection: string
  }
  temperatureMap: { ... }
  windSpeedMap: { ... }
}
```

### 6.3 Web Component Integration

**MapPlaceholder Component:**
- Used for dashboard cards before maps are generated
- Provides consistent placeholder styling
- Color-coded by variable type

**Map Display Component (Future):**
- Reusable component for displaying maps
- Handles loading, error states, interactions
- Supports both static images and interactive maps

---

## 7. Implementation Guidelines

### 7.1 Map Generation Pipeline

**Step 1: Data Preparation**
- Aggregate ward-level data
- Calculate value ranges for color assignment
- Identify missing data wards

**Step 2: Map Rendering**
- Generate base map with boundaries
- Apply color scheme based on data values
- Add cartographic elements (legend, scale, north arrow)
- Add title and metadata

**Step 3: Format Export**
- Export at required resolutions (300 DPI, 400 DPI)
- Optimize file sizes
- Generate web-optimized versions (WebP, compressed PNG)

**Step 4: Storage**
- Store maps in organized directory structure
- Generate metadata (file paths, sizes, timestamps)
- Update report structure with map references

### 7.2 PDF Embedding Process

**Method 1: Base64 Embedding (Preferred)**
1. Generate map at required resolution
2. Convert to base64 string
3. Embed directly in PDF using PDF library
4. Include in report structure as base64 string

**Method 2: File Reference**
1. Generate map and save to file system
2. Reference file path in report structure
3. PDF library includes file during PDF generation
4. Note: Requires file system access for PDF viewing

### 7.3 Web Dashboard Integration

**API Endpoints:**
- `GET /api/maps/[county-id]/[variable]/[date]` - Get map image
- `GET /api/maps/[county-id]/[variable]/[date]/metadata` - Get map metadata

**Response Format:**
```json
{
  "imageUrl": "/maps/31/rainfall/2026-01-19.png",
  "webpUrl": "/maps/31/rainfall/2026-01-19.webp",
  "metadata": {
    "resolution": 300,
    "format": "PNG",
    "generatedAt": "2026-01-18T09:30:00Z",
    "fileSize": 245678
  }
}
```

---

## 8. Quality Assurance

### 8.1 Validation Checklist

**Before PDF Generation:**
- [ ] All maps generated at correct resolution
- [ ] Color schemes applied correctly
- [ ] All cartographic elements present
- [ ] File sizes within targets
- [ ] Projection consistent across all maps
- [ ] No missing data without indication

**Before Web Deployment:**
- [ ] Web-optimized versions generated
- [ ] Responsive images configured
- [ ] Lazy loading implemented
- [ ] Error handling in place
- [ ] Loading states implemented
- [ ] Accessibility (alt text, ARIA labels)

### 8.2 Testing Requirements

**Visual Testing:**
- Print test: Generate PDF and print at 100% scale
- Screen test: View maps on various screen sizes
- Color test: Verify colorblind-friendly alternatives
- Quality test: Check for pixelation, banding, artifacts

**Functional Testing:**
- PDF: Verify all maps render correctly in PDF
- Web: Test loading, interactions, responsive behavior
- Performance: Measure load times, file sizes
- Cross-browser: Test in Chrome, Firefox, Safari, Edge

---

## 9. Future Enhancements

**Potential Additions:**
- Interactive web maps (Leaflet, Mapbox, D3.js)
- Animated maps (temporal sequences)
- 3D visualizations (elevation-based)
- Multi-variable overlay maps
- Export to GeoJSON/KML formats
- Print-optimized PDF generation
- Mobile app map integration

---

## 10. Document Control

**Version History:**
- v1.0 (2026-01-18): Initial specification by Person B

**Change Log:**
- All changes must be documented with version number and date

---

**End of Specification Document**

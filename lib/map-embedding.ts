/**
 * Map Embedding Strategy Type Definitions
 * Based on MAP_EMBEDDING_STRATEGY.md
 * 
 * This file defines the TypeScript interfaces for map embedding, formatting,
 * and integration into PDF reports and web dashboards.
 * 
 * @author Person B
 * @version 1.0
 */

/**
 * Map Image Format
 */
export type MapImageFormat = "PNG" | "JPEG" | "SVG" | "WEBP"

/**
 * Map Context - Where the map appears
 */
export type MapContext = 
  | "section-inline"      // Inline map in variable sections
  | "full-page"           // Full-page map in Ward-Level Visualizations
  | "dashboard-card"      // Compact preview in web dashboard
  | "detail-view"         // Full-screen interactive view

/**
 * Map Variable Type
 */
export type MapVariableType = "rainfall" | "temperature" | "wind"

/**
 * Map Projection
 */
export type MapProjection = "EPSG:32637" | "EPSG:4326" | string

/**
 * Map Resolution Configuration
 */
export interface MapResolution {
  /** DPI for PDF generation */
  pdfSection: number      // Default: 300
  /** DPI for PDF full-page maps */
  pdfFullPage: number     // Default: 400
  /** DPI for web dashboard cards */
  webCard: number         // Default: 150
  /** DPI for web detail views */
  webDetail: number       // Default: 200
}

/**
 * Map Size Configuration
 */
export interface MapSize {
  /** Width in millimeters (for PDF) or pixels (for web) */
  width: number
  /** Height in millimeters (for PDF) or pixels (for web) */
  height: number
  /** Aspect ratio (width/height) */
  aspectRatio: number
  /** Unit: "mm" for PDF, "px" for web */
  unit: "mm" | "px"
}

/**
 * Map Color Scale Range
 */
export interface ColorScaleRange {
  /** Value range (e.g., "0-20mm", "<18°C") */
  range: string
  /** Hex color code */
  color: string
  /** Minimum value (numeric) */
  min?: number
  /** Maximum value (numeric) */
  max?: number
}

/**
 * Map Color Scheme
 */
export interface MapColorScheme {
  /** Variable type */
  variable: MapVariableType
  /** Color scale ranges */
  ranges: ColorScaleRange[]
  /** No data color */
  noDataColor: string
  /** Colorblind-friendly alternative (optional) */
  colorblindFriendly?: ColorScaleRange[]
}

/**
 * Cartographic Elements Configuration
 */
export interface CartographicElements {
  /** Show title block */
  showTitle: boolean
  /** Show legend */
  showLegend: boolean
  /** Legend position */
  legendPosition: "bottom-right" | "bottom-center" | "top-right"
  /** Show scale bar */
  showScaleBar: boolean
  /** Scale bar position */
  scaleBarPosition: "bottom-left" | "bottom-right"
  /** Show north arrow */
  showNorthArrow: boolean
  /** North arrow position */
  northArrowPosition: "top-right" | "top-left"
  /** Show ward labels */
  showWardLabels: boolean
  /** Show coordinate grid */
  showGrid: boolean
  /** Ward boundary line width (points) */
  wardBoundaryWidth: number
  /** County boundary line width (points) */
  countyBoundaryWidth: number
  /** Boundary colors */
  boundaryColors: {
    ward: string
    county: string
  }
}

/**
 * Map Generation Configuration
 */
export interface MapGenerationConfig {
  /** Variable type */
  variable: MapVariableType
  /** Context where map will be used */
  context: MapContext
  /** County ID */
  countyId: string
  /** County name */
  countyName: string
  /** Period start date (ISO format) */
  periodStart: string
  /** Period end date (ISO format) */
  periodEnd: string
  /** Projection */
  projection: MapProjection
  /** Resolution configuration */
  resolution: MapResolution
  /** Size configuration */
  size: MapSize
  /** Color scheme */
  colorScheme: MapColorScheme
  /** Cartographic elements */
  cartographicElements: CartographicElements
  /** Output format */
  format: MapImageFormat
  /** File size target (bytes) */
  fileSizeTarget?: number
}

/**
 * Generated Map Metadata
 */
export interface MapMetadata {
  /** File path, base64 string, or URL */
  imagePath: string
  /** Web-optimized version (WebP) path/URL */
  webpPath?: string
  /** Map title */
  title: string
  /** Resolution (DPI) */
  resolution: number
  /** Format */
  format: MapImageFormat
  /** Projection */
  projection: MapProjection
  /** File size in bytes */
  fileSize: number
  /** Generation timestamp (ISO) */
  generatedAt: string
  /** Width in pixels */
  width: number
  /** Height in pixels */
  height: number
  /** Context */
  context: MapContext
  /** Variable type */
  variable: MapVariableType
}

/**
 * PDF Map Embedding Configuration
 */
export interface PDFMapEmbedding {
  /** Map metadata */
  map: MapMetadata
  /** Embedding method */
  embeddingMethod: "base64" | "file-reference"
  /** Base64 string (if using base64 method) */
  base64Data?: string
  /** File path (if using file-reference method) */
  filePath?: string
  /** Position on page */
  position: {
    x: number  // X coordinate in points
    y: number  // Y coordinate in points
  }
  /** Size on page */
  size: {
    width: number   // Width in points
    height: number  // Height in points
  }
  /** Caption text */
  caption?: string
  /** Figure number */
  figureNumber?: number
}

/**
 * Web Map Display Configuration
 */
export interface WebMapDisplay {
  /** Map metadata */
  map: MapMetadata
  /** Image URL */
  imageUrl: string
  /** WebP URL (for optimization) */
  webpUrl?: string
  /** Alt text for accessibility */
  altText: string
  /** Responsive breakpoints */
  responsive: {
    mobile: MapSize
    tablet: MapSize
    desktop: MapSize
  }
  /** Loading strategy */
  loading: "lazy" | "eager"
  /** Interactive features */
  interactive?: {
    /** Enable hover tooltips */
    hoverTooltip: boolean
    /** Enable click navigation */
    clickNavigation: boolean
    /** Enable zoom/pan */
    zoomPan: boolean
    /** Enable download */
    download: boolean
    /** Enable fullscreen */
    fullscreen: boolean
  }
  /** CSS classes */
  className?: string
}

/**
 * Map Storage Configuration
 */
export interface MapStorageConfig {
  /** Storage method */
  method: "filesystem" | "base64" | "cloud"
  /** Base directory (for filesystem) */
  baseDirectory?: string
  /** File naming pattern */
  namingPattern: string
  /** Cloud storage bucket (for cloud method) */
  bucket?: string
  /** Cloud storage region */
  region?: string
  /** Public URL prefix (for cloud/CDN) */
  publicUrlPrefix?: string
}

/**
 * Complete Map Embedding Strategy
 */
export interface MapEmbeddingStrategy {
  /** Generation configuration */
  generation: MapGenerationConfig
  /** PDF embedding configuration */
  pdfEmbedding?: PDFMapEmbedding
  /** Web display configuration */
  webDisplay?: WebMapDisplay
  /** Storage configuration */
  storage: MapStorageConfig
  /** Metadata */
  metadata: MapMetadata
}

/**
 * Default Map Resolutions
 */
export const DEFAULT_MAP_RESOLUTIONS: MapResolution = {
  pdfSection: 300,
  pdfFullPage: 400,
  webCard: 150,
  webDetail: 200,
}

/**
 * Default Map Sizes by Context
 */
export const DEFAULT_MAP_SIZES: Record<MapContext, MapSize> = {
  "section-inline": {
    width: 170,
    height: 120,
    aspectRatio: 170 / 120,
    unit: "mm",
  },
  "full-page": {
    width: 170,
    height: 257,
    aspectRatio: 170 / 257,
    unit: "mm",
  },
  "dashboard-card": {
    width: 300,
    height: 200,
    aspectRatio: 300 / 200,
    unit: "px",
  },
  "detail-view": {
    width: 1200,
    height: 800,
    aspectRatio: 1200 / 800,
    unit: "px",
  },
}

/**
 * Default Color Schemes
 */
export const DEFAULT_COLOR_SCHEMES: Record<MapVariableType, MapColorScheme> = {
  rainfall: {
    variable: "rainfall",
    ranges: [
      { range: "0-20mm", color: "#E3F2FD", min: 0, max: 20 },
      { range: "20-40mm", color: "#90CAF9", min: 20, max: 40 },
      { range: "40-60mm", color: "#42A5F5", min: 40, max: 60 },
      { range: "60-80mm", color: "#1E88E5", min: 60, max: 80 },
      { range: "80mm+", color: "#0D47A1", min: 80 },
    ],
    noDataColor: "#CCCCCC",
  },
  temperature: {
    variable: "temperature",
    ranges: [
      { range: "<18°C", color: "#2196F3", max: 18 },
      { range: "18-22°C", color: "#4CAF50", min: 18, max: 22 },
      { range: "22-26°C", color: "#FFEB3B", min: 22, max: 26 },
      { range: "26-30°C", color: "#FF9800", min: 26, max: 30 },
      { range: ">30°C", color: "#F44336", min: 30 },
    ],
    noDataColor: "#CCCCCC",
  },
  wind: {
    variable: "wind",
    ranges: [
      { range: "0-10 km/h", color: "#E8F5E9", min: 0, max: 10 },
      { range: "10-15 km/h", color: "#A5D6A7", min: 10, max: 15 },
      { range: "15-20 km/h", color: "#66BB6A", min: 15, max: 20 },
      { range: "20-25 km/h", color: "#43A047", min: 20, max: 25 },
      { range: "25+ km/h", color: "#2E7D32", min: 25 },
    ],
    noDataColor: "#CCCCCC",
  },
}

/**
 * Default Cartographic Elements
 */
export const DEFAULT_CARTOGRAPHIC_ELEMENTS: CartographicElements = {
  showTitle: true,
  showLegend: true,
  legendPosition: "bottom-right",
  showScaleBar: true,
  scaleBarPosition: "bottom-left",
  showNorthArrow: true,
  northArrowPosition: "top-right",
  showWardLabels: false,
  showGrid: false,
  wardBoundaryWidth: 0.5,
  countyBoundaryWidth: 1.0,
  boundaryColors: {
    ward: "#333333",
    county: "#000000",
  },
}

/**
 * Generate map file name
 */
export function generateMapFileName(
  countyId: string,
  variable: MapVariableType,
  periodStart: string,
  context: MapContext,
  resolution: number,
  format: MapImageFormat = "PNG"
): string {
  const dateStr = periodStart.split("T")[0] // Extract date part
  const contextStr = context === "full-page" ? "fullpage" : "section"
  const ext = format.toLowerCase()
  return `${countyId}_${variable}_${dateStr}_${contextStr}_${resolution}dpi.${ext}`
}

/**
 * Generate map storage path
 */
export function generateMapStoragePath(
  countyId: string,
  date: string,
  fileName: string,
  baseDirectory: string = "reports/maps"
): string {
  return `${baseDirectory}/${countyId}/${date}/${fileName}`
}

/**
 * Create map generation configuration
 */
export function createMapGenerationConfig(
  variable: MapVariableType,
  context: MapContext,
  countyId: string,
  countyName: string,
  periodStart: string,
  periodEnd: string,
  customConfig?: Partial<MapGenerationConfig>
): MapGenerationConfig {
  const resolution = customConfig?.resolution || DEFAULT_MAP_RESOLUTIONS
  const size = customConfig?.size || DEFAULT_MAP_SIZES[context]
  const colorScheme = customConfig?.colorScheme || DEFAULT_COLOR_SCHEMES[variable]
  const cartographicElements = customConfig?.cartographicElements || DEFAULT_CARTOGRAPHIC_ELEMENTS

  // Determine resolution based on context
  let dpi: number
  if (context === "full-page") {
    dpi = resolution.pdfFullPage
  } else if (context === "section-inline") {
    dpi = resolution.pdfSection
  } else if (context === "dashboard-card") {
    dpi = resolution.webCard
  } else {
    dpi = resolution.webDetail
  }

  return {
    variable,
    context,
    countyId,
    countyName,
    periodStart,
    periodEnd,
    projection: customConfig?.projection || "EPSG:32637",
    resolution,
    size,
    colorScheme,
    cartographicElements,
    format: customConfig?.format || (context.startsWith("web") ? "WEBP" : "PNG"),
    fileSizeTarget: customConfig?.fileSizeTarget,
  }
}

/**
 * Validate map metadata
 */
export function validateMapMetadata(metadata: MapMetadata): {
  isValid: boolean
  errors: string[]
} {
  const errors: string[] = []

  if (!metadata.imagePath) {
    errors.push("Image path is required")
  }

  if (metadata.resolution < 150) {
    errors.push("Resolution must be at least 150 DPI")
  }

  if (!["PNG", "JPEG", "SVG", "WEBP"].includes(metadata.format)) {
    errors.push("Invalid format")
  }

  if (metadata.width <= 0 || metadata.height <= 0) {
    errors.push("Width and height must be positive")
  }

  if (!metadata.generatedAt) {
    errors.push("Generation timestamp is required")
  }

  return {
    isValid: errors.length === 0,
    errors,
  }
}

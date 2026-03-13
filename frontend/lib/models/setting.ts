export interface SharedFile {
    id: string
    file_name: string
    file_type: "template" | "templates" | "shapefile" | "shapefiles"
    upload_date: string
    file_path?: string | null
}
  
export interface UserSettings {
    pdf_template_id: string | null
    selected_template?: SharedFile | null
    show_constituencies: boolean
    show_wards: boolean
    show_labels: boolean
    label_font_size: number
}

export interface SettingsResponse {
    shapefile_path: string
    shapefile_name: string
    templates: SharedFile[]
    user_settings: UserSettings
}

export interface UpdateSettingsPayload {
    pdf_template_id?: string | null
    show_constituencies?: boolean
    show_wards?: boolean
    show_labels?: boolean
    label_font_size?: number
}

export interface MapPreviewLabel {
    name: string
    lon: number
    lat: number
}

export interface MapPreviewGeometry {
    type: "Polygon" | "MultiPolygon" | "LineString" | "MultiLineString" | "GeometryCollection"
    coordinates?: unknown
    geometries?: unknown
}

export interface MapPreviewResponse {
    county: string
    bbox: [number, number, number, number]
    county_geometry: MapPreviewGeometry
    constituency_boundaries?: MapPreviewGeometry | null
    ward_boundaries?: MapPreviewGeometry | null
    labels?: MapPreviewLabel[]
}

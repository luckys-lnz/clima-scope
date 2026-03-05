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
}

export interface SettingsResponse {
    shapefile_path: string
    shapefile_name: string
    templates: SharedFile[]
    user_settings: UserSettings
}

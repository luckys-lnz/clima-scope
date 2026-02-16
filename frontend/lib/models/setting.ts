export interface SharedFile {
    id: string
    file_name: string
    file_type: "template"
    upload_date: string
}
  
export interface UserSettings {
    pdf_template_id: string | null
}

export interface SettingsResponse {
    shapefile_name: string
    templates: SharedFile[]
    user_settings: UserSettings
}

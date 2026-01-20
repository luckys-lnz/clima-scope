"use client"

import { ChevronLeft, Upload, Check, AlertTriangle } from "lucide-react"

interface DataUploadProps {
  onBack: () => void
}

export function DataUpload({ onBack }: DataUploadProps) {
  return (
    <div className="p-6 space-y-6">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-primary hover:text-primary/80 transition-colors mb-4"
      >
        <ChevronLeft className="w-4 h-4" />
        <span className="text-sm">Back to Dashboard</span>
      </button>

      <div className="max-w-3xl space-y-6">
        {/* County Shapefile Upload */}
        <div className="bg-card rounded-lg border border-border p-6">
          <h2 className="font-bold text-lg text-card-foreground mb-4">County Boundaries Shapefile</h2>
          <div className="border-2 border-dashed border-border rounded-lg p-12 text-center hover:bg-muted/50 transition-colors cursor-pointer">
            <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-sm text-card-foreground font-medium mb-1">Drag and drop shapefile or click to select</p>
            <p className="text-xs text-muted-foreground">Supported: .shp, .shx, .dbf, .prj</p>
          </div>
        </div>

        {/* Ward Shapefile Upload */}
        <div className="bg-card rounded-lg border border-border p-6">
          <h2 className="font-bold text-lg text-card-foreground mb-4">Ward Boundaries Shapefile</h2>
          <div className="border-2 border-dashed border-border rounded-lg p-12 text-center hover:bg-muted/50 transition-colors cursor-pointer">
            <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-sm text-card-foreground font-medium mb-1">Drag and drop shapefile or click to select</p>
            <p className="text-xs text-muted-foreground">Supported: .shp, .shx, .dbf, .prj</p>
          </div>
        </div>

        {/* Observation Data Upload */}
        <div className="bg-card rounded-lg border border-border p-6">
          <h2 className="font-bold text-lg text-card-foreground mb-4">Station Observations (CSV)</h2>
          <div className="border-2 border-dashed border-border rounded-lg p-12 text-center hover:bg-muted/50 transition-colors cursor-pointer">
            <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-sm text-card-foreground font-medium mb-1">Drag and drop CSV file or click to select</p>
            <p className="text-xs text-muted-foreground">
              Format: Station_ID, Latitude, Longitude, Temperature, Rainfall, Wind_Speed
            </p>
          </div>
        </div>

        {/* Validation Results */}
        <div className="bg-card rounded-lg border border-border p-6">
          <h2 className="font-bold text-lg text-card-foreground mb-4">Validation Results</h2>
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-green-700">CRS Alignment: Valid</p>
                <p className="text-xs text-green-600 mt-1">
                  County and ward shapefiles use consistent EPSG:4326 projection
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-green-700">Boundary Completeness: 100%</p>
                <p className="text-xs text-green-600 mt-1">All 47 counties and 1,450 wards have valid geometries</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-amber-700">Missing Wards Detection: 3 wards missing</p>
                <p className="text-xs text-amber-600 mt-1">
                  Wards: Nairobi #023, Kiambu #045, Mombasa #067 (historical data will be used)
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Visual Preview Map */}
        <div className="bg-card rounded-lg border border-border p-6">
          <h2 className="font-bold text-lg text-card-foreground mb-4">Uploaded Shapefile Preview</h2>
          <div className="bg-muted rounded-lg h-96 flex items-center justify-center">
            <p className="text-muted-foreground text-sm">Map preview of uploaded boundaries will appear here</p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground py-2 px-4 rounded-lg font-medium transition-colors">
            Validate & Save
          </button>
          <button className="flex-1 bg-card hover:bg-muted border border-border text-card-foreground py-2 px-4 rounded-lg font-medium transition-colors">
            Clear All
          </button>
        </div>
      </div>
    </div>
  )
}

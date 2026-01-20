"use client"

import { ChevronLeft, AlertCircle } from "lucide-react"
import { TextInput } from "@/components/text-input"
import { SelectInput } from "@/components/select-input"

interface SystemConfigurationProps {
  onBack: () => void
}

export function SystemConfiguration({ onBack }: SystemConfigurationProps) {
  return (
    <div className="p-6 space-y-6">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-primary hover:text-primary/80 transition-colors mb-4"
      >
        <ChevronLeft className="w-4 h-4" />
        <span className="text-sm">Back to Dashboard</span>
      </button>

      <div className="max-w-2xl space-y-6">
        {/* GRIB Storage */}
        <div className="bg-card rounded-lg border border-border p-6">
          <h2 className="font-bold text-lg text-card-foreground mb-4">GRIB Data Storage</h2>
          <div className="space-y-4">
            <TextInput
              label="GRIB Storage Path"
              value="/mnt/data/grib_forecasts"
              placeholder="/path/to/grib"
              readOnly
            />
            <TextInput
              label="Archive Path"
              value="/mnt/archive/weekly_reports"
              placeholder="/path/to/archive"
              readOnly
            />
          </div>
        </div>

        {/* Shapefile Configuration */}
        <div className="bg-card rounded-lg border border-border p-6">
          <h2 className="font-bold text-lg text-card-foreground mb-4">Geospatial Configuration</h2>
          <div className="space-y-4">
            <TextInput
              label="County Shapefile Path"
              value="/mnt/data/shapefiles/counties.shp"
              placeholder="/path/to/county.shp"
              readOnly
            />
            <TextInput
              label="Ward Shapefile Path"
              value="/mnt/data/shapefiles/wards.shp"
              placeholder="/path/to/wards.shp"
              readOnly
            />
          </div>
        </div>

        {/* Email Configuration */}
        <div className="bg-card rounded-lg border border-border p-6">
          <h2 className="font-bold text-lg text-card-foreground mb-4">Email Distribution</h2>
          <div className="space-y-4">
            <TextInput
              label="Email Recipients (comma-separated)"
              value="forecast@weather.ke,reports@agriculture.ke"
              placeholder="email1@example.com, email2@example.com"
            />
            <div className="flex items-center gap-2 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              <span className="text-xs text-amber-700">
                Email configuration changes will take effect on next scheduled run
              </span>
            </div>
          </div>
        </div>

        {/* Automatic Scheduling */}
        <div className="bg-card rounded-lg border border-border p-6">
          <h2 className="font-bold text-lg text-card-foreground mb-4">Automated Scheduling</h2>
          <div className="space-y-4">
            <TextInput
              label="Cron Expression"
              value="0 0 * * 0"
              placeholder="0 0 * * 0"
              description="Runs every Sunday at 00:00 UTC (format: minute hour day month weekday)"
            />
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-sm text-card-foreground">Next scheduled run: Dec 15, 2024 at 00:00 UTC</span>
            </div>
          </div>
        </div>

        {/* Model Configuration */}
        <div className="bg-card rounded-lg border border-border p-6">
          <h2 className="font-bold text-lg text-card-foreground mb-4">Forecast Model Selection</h2>
          <div className="space-y-4">
            <SelectInput
              value="gfs-v15.1"
              onChange={() => {}}
              options={[
                { value: "gfs-v15.1", label: "GFS v15.1 (Current)" },
                { value: "gfs-v15.0", label: "GFS v15.0" },
                { value: "gfs-v14.2", label: "GFS v14.2" },
              ]}
            />
            <p className="text-xs text-muted-foreground">GFS provides 7-day forecasts with 0.25° resolution</p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground py-2 px-4 rounded-lg font-medium transition-colors">
            Save Configuration
          </button>
          <button className="flex-1 bg-card hover:bg-muted border border-border text-card-foreground py-2 px-4 rounded-lg font-medium transition-colors">
            Reset to Defaults
          </button>
        </div>
      </div>
    </div>
  )
}

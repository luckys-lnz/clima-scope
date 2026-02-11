"use client"

import { ChevronLeft, Download, RefreshCw, Eye, TrendingUp, TrendingDown } from "lucide-react"
import { MapPlaceholder } from "@/components/map-placeholder"

interface CountyDetailProps {
  county: string
  onBack: () => void
}

export function CountyDetail({ county, onBack }: CountyDetailProps) {
  return (
    <div className="p-6 space-y-6">
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-primary hover:text-primary/80 transition-colors mb-4"
      >
        <ChevronLeft className="w-4 h-4" />
        <span className="text-sm">Back to Archive</span>
      </button>

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card rounded-lg border border-border p-6">
          <div className="flex items-start justify-between mb-2">
            <h3 className="text-sm text-muted-foreground font-medium">Total Rainfall</h3>
            <TrendingUp className="w-4 h-4 text-weather-rainfall" />
          </div>
          <p className="text-3xl font-bold text-card-foreground">248.5 mm</p>
          <p className="text-xs text-muted-foreground mt-2">7-day forecast total</p>
        </div>

        <div className="bg-card rounded-lg border border-border p-6">
          <div className="flex items-start justify-between mb-2">
            <h3 className="text-sm text-muted-foreground font-medium">Mean Temperature</h3>
            <TrendingDown className="w-4 h-4 text-weather-temperature" />
          </div>
          <p className="text-3xl font-bold text-card-foreground">22.3°C</p>
          <p className="text-xs text-muted-foreground mt-2">Average over 7 days</p>
        </div>

        <div className="bg-card rounded-lg border border-border p-6">
          <div className="flex items-start justify-between mb-2">
            <h3 className="text-sm text-muted-foreground font-medium">Max Wind Speed</h3>
            <TrendingUp className="w-4 h-4 text-weather-wind" />
          </div>
          <p className="text-3xl font-bold text-card-foreground">18 km/h</p>
          <p className="text-xs text-muted-foreground mt-2">Peak gust expected</p>
        </div>
      </div>

      {/* Narrative Text */}
      <div className="bg-card rounded-lg border border-border p-6">
        <h2 className="font-bold text-lg text-card-foreground mb-4">Weekly Narrative Summary</h2>
        <div className="prose prose-invert max-w-none">
          <p className="text-sm text-card-foreground leading-relaxed">
            Week 50 of 2024 in {county} county is expected to experience variable weather patterns. The early part of
            the week (Dec 2-4) will see moderate rainfall of 40-65 mm across the county, with temperatures ranging from
            18-26°C. Mid-week (Dec 5-6) will be drier with isolated showers, while the latter part (Dec 7-8) will see
            increased cloud cover and renewed rainfall activity totaling 35-52 mm.
          </p>
          <p className="text-sm text-card-foreground leading-relaxed mt-3">
            Wind speeds will generally remain moderate at 8-15 km/h, with occasional gusts up to 18 km/h particularly
            during rainy periods. Night-time temperatures will drop to 12-16°C, while daytime highs reach 24-28°C.
            Relative humidity will fluctuate between 60-85% depending on rainfall activity.
          </p>
        </div>
      </div>

      {/* Ward-Level Maps */}
      <div>
        <h2 className="font-bold text-lg text-card-foreground mb-4">Ward-Level Map Visualizations</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-card rounded-lg border border-border overflow-hidden">
            <MapPlaceholder title="Rainfall Distribution" color="rainfall" />
            <div className="p-4 flex justify-between items-center">
              <div className="text-xs text-muted-foreground">7-day total (mm)</div>
              <button className="flex items-center gap-1 text-primary hover:text-primary/80 transition-colors text-xs font-medium">
                <Eye className="w-3 h-3" />
                View
              </button>
            </div>
          </div>

          <div className="bg-card rounded-lg border border-border overflow-hidden">
            <MapPlaceholder title="Temperature Avg" color="temperature" />
            <div className="p-4 flex justify-between items-center">
              <div className="text-xs text-muted-foreground">Mean (°C)</div>
              <button className="flex items-center gap-1 text-primary hover:text-primary/80 transition-colors text-xs font-medium">
                <Eye className="w-3 h-3" />
                View
              </button>
            </div>
          </div>

          <div className="bg-card rounded-lg border border-border overflow-hidden">
            <MapPlaceholder title="Wind Speed" color="wind" />
            <div className="p-4 flex justify-between items-center">
              <div className="text-xs text-muted-foreground">Max (km/h)</div>
              <button className="flex items-center gap-1 text-primary hover:text-primary/80 transition-colors text-xs font-medium">
                <Eye className="w-3 h-3" />
                View
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground py-2 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2">
          <Download className="w-4 h-4" />
          Download PDF
        </button>
        <button className="flex-1 bg-card hover:bg-muted border border-border text-card-foreground py-2 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4" />
          Regenerate Report
        </button>
      </div>
    </div>
  )
}

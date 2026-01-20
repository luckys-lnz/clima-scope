"use client"

import { useState } from "react"
import { ChevronLeft, Download, RefreshCw } from "lucide-react"
import { motion } from "framer-motion"
import { SelectInput } from "@/components/select-input"
import { LogViewer } from "@/components/log-viewer"

interface ManualGenerationProps {
  onBack: () => void
}

const COUNTIES = [
  "Nairobi",
  "Mombasa",
  "Kisumu",
  "Nakuru",
  "Eldoret",
  "Kericho",
  "Nyeri",
  "Thika",
  "Machakos",
  "Voi",
  "Kimalayo",
  "Kwale",
  "Kilifi",
  "Lamu",
  "Garissa",
  "Wajir",
  "Mandera",
  "Isiolo",
  "Marsabit",
  "Turkana",
  "Samburu",
  "Embu",
  "Meru",
  "Tharaka",
  "Kitui",
  "Makueni",
  "Taita",
  "Narok",
  "Kajiado",
  "Bomet",
  "Bungoma",
  "Busia",
  "Siaya",
  "Kisii",
  "Nyamira",
  "Kiambu",
  "Muranga",
  "Laikipia",
  "West Pokot",
  "Baringo",
  "Kabarnet",
]

export function ManualGeneration({ onBack }: ManualGenerationProps) {
  const [selectedCounty, setSelectedCounty] = useState("")
  const [selectedWeek, setSelectedWeek] = useState("week-50-2024")
  const [includeObservations, setIncludeObservations] = useState(true)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [logs, setLogs] = useState<string[]>([])

  const handleGenerate = () => {
    setIsGenerating(true)
    setLogs([])
    setIsComplete(false)

    const newLogs = [
      `[${new Date().toLocaleTimeString()}] Starting report generation for ${selectedCounty}...`,
      `[${new Date().toLocaleTimeString()}] Fetching GFS 7-day forecast data...`,
    ]
    setLogs(newLogs)

    setTimeout(() => {
      setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] Parsing GRIB files...`])
    }, 1000)

    setTimeout(() => {
      setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] Performing spatial aggregation...`])
    }, 2000)

    setTimeout(() => {
      setLogs((prev) => [
        ...prev,
        `[${new Date().toLocaleTimeString()}] Generating ward-level maps (rainfall, temperature, wind)...`,
      ])
    }, 3000)

    setTimeout(() => {
      setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] Creating PDF report...`])
    }, 4000)

    setTimeout(() => {
      setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ✓ Report generation completed successfully`])
      setIsGenerating(false)
      setIsComplete(true)
    }, 5000)
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="p-4 sm:p-6 space-y-6 lg:pt-0"
    >
      <motion.button
        onClick={onBack}
        whileHover={{ x: -4 }}
        className="flex items-center gap-2 text-primary hover:text-primary/80 transition-colors mb-4"
      >
        <ChevronLeft className="w-4 h-4" />
        <span className="text-sm">Back to Dashboard</span>
      </motion.button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* Form Section */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="lg:col-span-1"
        >
          <div className="bg-card rounded-lg border border-border p-4 sm:p-6 space-y-4">
            <h2 className="font-bold text-base sm:text-lg text-card-foreground">Report Parameters</h2>

            <div>
              <label className="block text-xs sm:text-sm font-medium text-card-foreground mb-2">County</label>
              <SelectInput
                value={selectedCounty}
                onChange={setSelectedCounty}
                options={COUNTIES.map((c) => ({ value: c, label: c }))}
                placeholder="Select county..."
              />
            </div>

            <div>
              <label className="block text-xs sm:text-sm font-medium text-card-foreground mb-2">Week</label>
              <SelectInput
                value={selectedWeek}
                onChange={setSelectedWeek}
                options={[
                  { value: "week-50-2024", label: "Week 50, 2024 (Dec 2-8)" },
                  { value: "week-51-2024", label: "Week 51, 2024 (Dec 9-15)" },
                  { value: "week-52-2024", label: "Week 52, 2024 (Dec 16-22)" },
                ]}
              />
            </div>

            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="observations"
                checked={includeObservations}
                onChange={(e) => setIncludeObservations(e.target.checked)}
                className="w-4 h-4 rounded border-border"
              />
              <label htmlFor="observations" className="text-xs sm:text-sm text-card-foreground">
                Include station observations
              </label>
            </div>

            <motion.button
              onClick={handleGenerate}
              disabled={!selectedCounty || isGenerating}
              whileHover={{ scale: !selectedCounty || isGenerating ? 1 : 1.02 }}
              whileTap={{ scale: !selectedCounty || isGenerating ? 1 : 0.98 }}
              className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-primary-foreground py-2 px-4 rounded-lg font-medium transition-colors"
            >
              {isGenerating ? "Generating..." : "Generate Report"}
            </motion.button>
          </div>
        </motion.div>

        {/* Logs Section */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2"
        >
          <div className="bg-card rounded-lg border border-border p-4 sm:p-6">
            <h2 className="font-bold text-base sm:text-lg text-card-foreground mb-4">Processing Logs</h2>
            <LogViewer logs={logs} />

            {isComplete && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
                className="mt-6 space-y-3"
              >
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                  <p className="text-xs sm:text-sm text-green-600 font-medium">✓ Report generated successfully</p>
                </div>
                <div className="flex flex-col sm:flex-row gap-3">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground py-2 px-4 rounded-lg text-xs sm:text-sm font-medium transition-colors flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Download PDF
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="flex-1 bg-card hover:bg-muted border border-border text-card-foreground py-2 px-4 rounded-lg text-xs sm:text-sm font-medium transition-colors flex items-center justify-center gap-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Regenerate
                  </motion.button>
                </div>
              </motion.div>
            )}
          </div>
        </motion.div>
      </div>
    </motion.div>
  )
}

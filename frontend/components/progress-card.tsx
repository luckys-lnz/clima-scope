"use client"

import { motion } from "framer-motion"

interface Step {
  name: string
  status: "completed" | "in-progress" | "pending"
}

interface ProgressCardProps {
  title: string
  currentWeek: string
  progress: number
  status: "processing" | "completed" | "failed"
  steps: Step[]
}

export function ProgressCard({ title, currentWeek, progress, status, steps }: ProgressCardProps) {
  const statusColor = {
    processing: "text-blue-600",
    completed: "text-green-600",
    failed: "text-red-600",
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-card rounded-lg border border-border p-4 sm:p-6"
    >
      <div className="flex flex-col sm:flex-row items-start sm:items-start justify-between mb-4 gap-2 sm:gap-0">
        <div>
          <h2 className="font-bold text-base sm:text-lg text-card-foreground">{title}</h2>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">{currentWeek}</p>
        </div>
        <motion.div
          animate={{
            opacity: status === "processing" ? [0.5, 1, 0.5] : 1,
          }}
          transition={{ duration: 2, repeat: status === "processing" ? Infinity : 0 }}
          className={`text-xs sm:text-sm font-medium ${statusColor[status]} flex-shrink-0`}
        >
          {status === "processing" ? "⏳ Processing" : status === "completed" ? "✓ Completed" : "✗ Failed"}
        </motion.div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs sm:text-sm text-muted-foreground">Overall Progress</span>
          <span className="text-xs sm:text-sm font-semibold text-card-foreground">{progress}%</span>
        </div>
        <div className="w-full bg-muted rounded-full h-2 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 1.5, ease: "easeOut" }}
            className="bg-primary h-2 rounded-full"
          />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {steps.map((step, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.05 }}
            className="flex items-center gap-3"
          >
            <motion.div
              animate={{
                scale: step.status === "in-progress" ? [1, 1.1, 1] : 1,
              }}
              transition={{ duration: 1, repeat: step.status === "in-progress" ? Infinity : 0 }}
              className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-medium"
              style={{
                backgroundColor:
                  step.status === "completed" ? "#10b981" : step.status === "in-progress" ? "#3b82f6" : "#6b7280",
                color: "white",
              }}
            >
              {step.status === "completed" ? "✓" : step.status === "in-progress" ? "→" : "○"}
            </motion.div>
            <span
              className={`text-xs sm:text-sm ${
                step.status === "completed"
                  ? "text-card-foreground"
                  : step.status === "in-progress"
                    ? "text-blue-600 font-medium"
                    : "text-muted-foreground"
              }`}
            >
              {step.name}
            </span>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

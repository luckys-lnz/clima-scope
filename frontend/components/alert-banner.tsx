"use client"

import { AlertCircle, AlertTriangle, Info } from "lucide-react"
import { motion } from "framer-motion"

interface AlertBannerProps {
  severity: "critical" | "warning" | "info"
  title: string
  message: string
  timestamp: string
}

export function AlertBanner({ severity, title, message, timestamp }: AlertBannerProps) {
  const alertColors = {
    critical: "bg-red-500/10 border-red-500/30 text-red-700",
    warning: "bg-amber-500/10 border-amber-500/30 text-amber-700",
    info: "bg-blue-500/10 border-blue-500/30 text-blue-700",
  }

  const icons = {
    critical: AlertCircle,
    warning: AlertTriangle,
    info: Info,
  }

  const Icon = icons[severity]

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.3 }}
      whileHover={{ x: 4 }}
      className={`rounded-lg border ${alertColors[severity]} p-3 sm:p-4 flex items-start gap-3 cursor-default`}
    >
      <motion.div animate={{ y: [0, -2, 0] }} transition={{ duration: 2, repeat: Infinity }}>
        <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
      </motion.div>
      <div className="flex-1 min-w-0">
        <h3 className="font-semibold text-xs sm:text-sm mb-1">{title}</h3>
        <p className="text-xs opacity-90">{message}</p>
        <p className="text-xs opacity-70 mt-2">{timestamp}</p>
      </div>
    </motion.div>
  )
}

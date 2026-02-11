"use client"

import type { LucideIcon } from "lucide-react"
import { motion } from "framer-motion"

interface StatCardProps {
  label: string
  value: string
  icon: LucideIcon
  status: "success" | "warning" | "info"
}

export function StatCard({ label, value, icon: Icon, status }: StatCardProps) {
  const statusConfig = {
    success: {
      color: "text-green-500",
      bg: "from-green-500/20 to-transparent",
      border: "border-green-500/40",
      glow: "shadow-lg shadow-green-500/20",
    },
    warning: {
      color: "text-amber-500",
      bg: "from-amber-500/20 to-transparent",
      border: "border-amber-500/40",
      glow: "shadow-lg shadow-amber-500/20",
    },
    info: {
      color: "text-blue-500",
      bg: "from-blue-500/20 to-transparent",
      border: "border-blue-500/40",
      glow: "shadow-lg shadow-blue-500/20",
    },
  }

  const config = statusConfig[status]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, type: "spring", stiffness: 300, damping: 20 }}
      whileHover={{
        y: -6,
        scale: 1.02,
        transition: { duration: 0.3 },
      }}
      whileTap={{ scale: 0.98 }}
      className={`relative group cursor-pointer overflow-hidden rounded-xl border ${config.border} p-4 sm:p-6 transition-all duration-300 ${config.glow}`}
    >
      {/* Gradient Background */}
      <div className={`absolute inset-0 bg-gradient-to-br ${config.bg} pointer-events-none`} />
      <div className="absolute inset-0 glass-effect pointer-events-none" />

      {/* Content */}
      <div className="relative z-10 flex flex-col gap-3">
        <div className="flex items-start justify-between">
          <h3 className="text-xs sm:text-sm font-semibold text-muted-foreground leading-tight">{label}</h3>
          <motion.div
            animate={{
              scale: [1, 1.15, 0.95, 1.1, 1],
              rotate: [0, -10, 10, -5, 0],
            }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            className={`p-2 rounded-lg glass-effect ${config.glow}`}
          >
            <Icon className={`w-5 h-5 ${config.color}`} />
          </motion.div>
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-card-foreground to-card-foreground/70 bg-clip-text text-transparent"
        >
          {value}
        </motion.p>
      </div>

      {/* Hover Effect Border */}
      <motion.div
        className={`absolute inset-0 rounded-xl border ${config.border} opacity-0 group-hover:opacity-100 pointer-events-none`}
        animate={{ opacity: [0, 0.5, 0] }}
        transition={{ duration: 2, repeat: Infinity }}
      />
    </motion.div>
  )
}

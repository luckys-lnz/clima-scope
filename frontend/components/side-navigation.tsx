"use client"

import { BarChart3, FileText, Archive, Settings, Upload, Activity, MapPin, ChevronDown, Menu, X } from "lucide-react"
import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"

interface SideNavigationProps {
  currentScreen: string
  onNavigate: (screen: string) => void
}

export function SideNavigation({ currentScreen, onNavigate }: SideNavigationProps) {
  const [isOpen, setIsOpen] = useState(false)

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: BarChart3, description: "System overview" },
    { id: "generate", label: "Generate Report", icon: FileText, description: "Create reports" },
    { id: "archive", label: "Report Archive", icon: Archive, description: "View history" },
    { id: "logs", label: "Logs & Diagnostics", icon: Activity, description: "System logs" },
    { id: "upload", label: "Data Upload", icon: Upload, description: "Import data" },
    { id: "config", label: "Configuration", icon: Settings, description: "Settings" },
  ]

  const handleNavigate = (screen: string) => {
    onNavigate(screen)
    setIsOpen(false)
  }

  return (
    <>
      {/* Mobile Menu Button */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg glass-effect glass-effect-hover"
      >
        {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </motion.button>

      {/* Mobile Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
            className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{ x: isOpen ? 0 : "-100%", opacity: isOpen ? 1 : 0 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="lg:static lg:translate-x-0 lg:opacity-100 fixed top-0 left-0 h-screen lg:h-full z-40 w-72 sm:w-80 lg:w-64 glass-effect overflow-y-auto"
      >
        {/* Logo Section */}
        <div className="sticky top-0 p-6 border-b border-sidebar-border backdrop-blur-xl">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="hidden lg:block"
          >
            <div className="flex items-center gap-3 mb-3">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                className="p-2 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20"
              >
                <MapPin className="w-5 h-5 text-primary" />
              </motion.div>
              <div>
                <h2 className="text-lg font-bold text-sidebar-foreground">Kenya Weather</h2>
                <p className="text-xs text-sidebar-foreground/60">Automated County Reporting</p>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-1">
          {navItems.map((item, idx) => {
            const Icon = item.icon
            const isActive = currentScreen === item.id
            return (
              <motion.button
                key={item.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.06, type: "spring", stiffness: 300 }}
                onClick={() => handleNavigate(item.id)}
                className={`w-full flex flex-col gap-1 px-4 py-3 rounded-xl transition-all relative overflow-hidden group ${
                  isActive
                    ? "bg-gradient-to-r from-primary/20 to-accent/10 text-sidebar-foreground"
                    : "text-sidebar-foreground/70 hover:text-sidebar-foreground"
                }`}
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
              >
                {/* Active indicator */}
                {isActive && (
                  <motion.div
                    layoutId="sidebar-indicator"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-primary to-accent rounded-r-full"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}

                <div className="flex items-center gap-3 relative z-10">
                  <motion.div
                    animate={isActive ? { scale: 1.1 } : { scale: 1 }}
                    transition={{ duration: 0.2 }}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                  </motion.div>
                  <div className="text-left flex-1 hidden sm:block">
                    <p className="text-sm font-medium">{item.label}</p>
                    <p className="text-xs opacity-60">{item.description}</p>
                  </div>
                  <div className="sm:hidden">
                    <p className="text-sm font-medium">{item.label}</p>
                  </div>
                </div>
              </motion.button>
            )
          })}
        </nav>

        {/* Status Section */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="absolute bottom-0 left-0 right-0 p-4 border-t border-sidebar-border bg-gradient-to-t from-sidebar to-transparent"
        >
          <p className="text-xs text-sidebar-foreground/60 mb-3 font-semibold">System Status</p>
          <div className="space-y-3">
            <motion.div
              animate={{ opacity: [0.6, 1, 0.6] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="flex items-center gap-3 text-xs text-sidebar-foreground"
            >
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0"
              />
              <span>Pipeline Active</span>
            </motion.div>
            <div className="flex items-center gap-3 text-xs text-sidebar-foreground">
              <div className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
              <span>Data Updated</span>
            </div>
          </div>
        </motion.div>
      </motion.aside>
    </>
  )
}

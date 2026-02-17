"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import {
  BarChart3,
  FileText,
  Archive,
  Upload,
  Settings,
  MapPin,
  Menu,
  X,
  LogOut,
} from "lucide-react"

import { DashboardOverview } from "@/components/ui-panels/dashboard-overview"
import { ManualGeneration } from "@/components/ui-panels/manual-generation"
import { ReportArchive } from "@/components/ui-panels/report-archive"
import { SystemConfiguration } from "@/components/ui-panels/system-configuration"
import { DataUpload } from "@/components/data-upload"

type Screen = "dashboard" | "generate" | "archive" | "config" | "upload"

export default function Dashboard() {
  const router = useRouter()
  const [currentScreen, setCurrentScreen] = useState<Screen>("dashboard")
  const [selectedCounty, setSelectedCounty] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [isLoggingOut, setIsLoggingOut] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  const handleLogout = async () => {
    setIsLoggingOut(true)
    try {
      const token = localStorage.getItem("access_token")

      localStorage.removeItem("access_token")
      localStorage.removeItem("refresh_token")
      localStorage.removeItem("user")

      if (token) {
        await fetch("http://localhost:8000/api/v1/auth/logout", {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        })
      }

      window.location.replace("/sign-in")
    } catch (error) {
      console.error("Logout error:", error)
      window.location.replace("/sign-in")
    }
  }

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: BarChart3 },
    { id: "generate", label: "Generate Report", icon: FileText },
    { id: "archive", label: "Report Archive", icon: Archive },
    { id: "upload", label: "Data Upload", icon: Upload },
    { id: "config", label: "Settings", icon: Settings },
  ]

  const renderScreen = () => {
    switch (currentScreen) {
      case "dashboard":
        return (
          <DashboardOverview
            onNavigate={(screen: string) =>
              setCurrentScreen(screen as Screen)
            }
          />
        )
      case "generate":
        return <ManualGeneration onBack={() => setCurrentScreen("dashboard")} />
      case "archive":
        return (
          <ReportArchive
            onSelectCounty={(county) => {
              setSelectedCounty(county)
            }}
          />
        )
      case "config":
        return (
          <SystemConfiguration onBack={() => setCurrentScreen("dashboard")} />
        )
      case "upload":
        return <DataUpload onBack={() => setCurrentScreen("dashboard")} />
      default:
        return (
          <DashboardOverview
            onNavigate={(screen: string) =>
              setCurrentScreen(screen as Screen)
            }
          />
        )
    }
  }

  const getTitle = (screen: string) => {
    const titles: Record<string, string> = {
      dashboard: "Dashboard",
      generate: "Generate Report",
      archive: "Report Archive",
      config: "Settings",
      upload: "Data Upload",
    }
    return titles[screen] || "Dashboard"
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-full w-64 bg-sidebar border-r border-border transform transition-transform md:relative md:translate-x-0 z-40 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center gap-3 px-6 py-6 border-b border-border">
          <MapPin className="w-6 h-6 text-primary" />
          <div>
            <h1 className="font-bold text-lg">Clima Scope</h1>
            <p className="text-xs text-muted-foreground">Mombasa County</p>
          </div>
        </div>

        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = currentScreen === item.id
            return (
              <button
                key={item.id}
                onClick={() => {
                  setCurrentScreen(item.id as Screen)
                  setSidebarOpen(false)
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-sm font-medium ${
                  isActive
                    ? "bg-primary/20 text-primary border border-primary/50"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            )
          })}
        </nav>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-card border-b border-border sticky top-0 z-20">
          <div className="flex items-center justify-between px-4 md:px-8 py-4">
            {/* Left */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden p-2 hover:bg-muted rounded-lg"
              >
                {sidebarOpen ? (
                  <X className="w-5 h-5" />
                ) : (
                  <Menu className="w-5 h-5" />
                )}
              </button>
              <h2 className="text-2xl font-bold">
                {getTitle(currentScreen as string)}
              </h2>
            </div>

            {/* Right: Avatar vertical */}
            <div className="relative flex flex-col items-center">
              {/* Avatar ONLY clickable */}
              <button
                onClick={() => setUserMenuOpen((s) => !s)}
                className="w-9 h-9 rounded-full border border-gray-400 flex items-center justify-center text-gray-400 font-semibold hover:bg-muted transition-colors"
              >
                U
              </button>

              {/* Welcome text NOT clickable */}
              <span className="text-xs text-muted-foreground mt-1">
                Welcome, Username
              </span>

              {/* Dropdown */}
              {userMenuOpen && (
                <div className="absolute right-0 top-12 w-36 bg-card border border-border rounded-lg shadow-lg z-50">
                  <button
                    onClick={handleLogout}
                    disabled={isLoggingOut}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg"
                  >
                    <LogOut className="w-4 h-4" />
                    {isLoggingOut ? "Logging out…" : "Logout"}
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-auto">
          <div className="min-h-full">{renderScreen()}</div>
        </div>
      </main>
    </div>
  )
}

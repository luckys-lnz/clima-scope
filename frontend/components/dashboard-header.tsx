"use client"

interface DashboardHeaderProps {
  currentScreen: string
}

export function DashboardHeader({ currentScreen }: DashboardHeaderProps) {
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
    <div className="px-6 py-4 border-b border-border">
      <h1 className="text-2xl font-semibold text-foreground">{getTitle(currentScreen as string)}</h1>
    </div>
  )
}

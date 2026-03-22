interface MapPlaceholderProps {
  title: string
  color: "rainfall" | "temperature" | "wind"
}

export function MapPlaceholder({ title, color }: MapPlaceholderProps) {
  const colorMap = {
    rainfall: "#55a3d4",
    temperature: "#e67e22",
    wind: "#3498db",
  }

  return (
    <div className="h-48 rounded-lg bg-muted flex items-center justify-center relative overflow-hidden">
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundColor: colorMap[color],
          backgroundImage: `url("data:image/svg+xml,%3Csvg width='100' height='100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0,50 Q25,25 50,50 T100,50' stroke='white' fill='none'/%3E%3C/svg%3E")`,
        }}
      ></div>
      <div className="relative z-10 text-center">
        <p className="text-sm font-medium text-card-foreground">{title}</p>
        <p className="text-xs text-muted-foreground mt-1">Ward-level visualization</p>
      </div>
    </div>
  )
}

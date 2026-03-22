import { AlertTriangle } from "lucide-react"

interface AlertCardProps {
  title: string
  text: string
}

export function AlertCard({ title, text }: AlertCardProps) {
  return (
    <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-500 mt-0.5" />
        <div>
          <p className="font-semibold text-sm">{title}</p>
          <p className="text-xs text-muted-foreground mt-1">{text}</p>
        </div>
      </div>
    </div>
  )
}

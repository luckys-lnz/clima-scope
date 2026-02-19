import { CheckCircle } from "lucide-react"

interface InfoCardProps {
  title: string
  text: string
}

export function InfoCard({ title, text }: InfoCardProps) {
  return (
    <div className="bg-blue-900/20 border border-blue-700/40 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <CheckCircle className="w-5 h-5 text-blue-500 mt-0.5" />
        <div>
          <p className="font-semibold text-sm">{title}</p>
          <p className="text-xs text-muted-foreground mt-1">{text}</p>
        </div>
      </div>
    </div>
  )
}

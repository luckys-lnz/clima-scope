import { ArrowRight } from "lucide-react"
import { ReactNode } from "react"

interface ActionButtonProps {
  children: ReactNode
  onClick: () => void
}

export function ActionButton({ children, onClick }: ActionButtonProps) {
  return (
    <button
      onClick={onClick}
      className="w-full bg-primary text-primary-foreground py-2 px-4 rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
    >
      {children} <ArrowRight className="w-4 h-4" />
    </button>
  )
}

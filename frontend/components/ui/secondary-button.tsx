import { ReactNode } from "react"

interface SecondaryButtonProps {
  children: ReactNode
  onClick: () => void
}

export function SecondaryButton({ children, onClick }: SecondaryButtonProps) {
  return (
    <button
      onClick={onClick}
      className="w-full bg-muted text-foreground py-2 px-4 rounded-lg text-sm font-medium hover:bg-muted/80 transition-colors"
    >
      {children}
    </button>
  )
}

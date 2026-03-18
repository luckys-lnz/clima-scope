"use client"

import type { LucideIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import { DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"

type StatusVariant = "dialog" | "inline"

const STATUS_TONES = {
  primary: {
    ring: "border-primary/30 bg-primary/15",
    icon: "text-primary",
    bar: "bg-primary/60",
  },
  accent: {
    ring: "border-accent/30 bg-accent/15",
    icon: "text-accent",
    bar: "bg-accent/60",
  },
  muted: {
    ring: "border-border/60 bg-muted/40",
    icon: "text-muted-foreground",
    bar: "bg-muted-foreground/60",
  },
} as const

type StatusTone = keyof typeof STATUS_TONES

interface StatusPanelProps {
  title: string
  description?: string
  icon: LucideIcon
  variant?: StatusVariant
  tone?: StatusTone
  showProgress?: boolean
  className?: string
}

export function StatusPanel({
  title,
  description,
  icon: Icon,
  variant = "inline",
  tone = "primary",
  showProgress = true,
  className,
}: StatusPanelProps) {
  const toneStyles = STATUS_TONES[tone]

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-start gap-4">
        <div
          className={cn(
            "mt-1 flex h-10 w-10 items-center justify-center rounded-full border",
            toneStyles.ring,
          )}
        >
          <Icon className={cn("h-5 w-5", toneStyles.icon)} />
        </div>
        {variant === "dialog" ? (
          <DialogHeader className="space-y-1 text-left">
            <DialogTitle>{title}</DialogTitle>
            {description ? (
              <DialogDescription>{description}</DialogDescription>
            ) : null}
          </DialogHeader>
        ) : (
          <div className="space-y-1 text-left">
            <p className="text-lg font-semibold leading-none">{title}</p>
            {description ? (
              <p className="text-sm text-muted-foreground">{description}</p>
            ) : null}
          </div>
        )}
      </div>
      {showProgress ? (
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted/60">
          <div
            className={cn(
              "h-full w-full animate-pulse rounded-full",
              toneStyles.bar,
            )}
          />
        </div>
      ) : null}
    </div>
  )
}

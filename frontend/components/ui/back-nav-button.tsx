"use client";

import { ArrowLeft } from "lucide-react";

interface BackNavButtonProps {
  onClick: () => void;
  label: string;
  className?: string;
}

export function BackNavButton({
  onClick,
  label,
  className = "",
}: BackNavButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-2 text-sm font-medium text-sky-600 transition-colors hover:text-sky-700 ${className}`.trim()}
      aria-label={label}
    >
      <ArrowLeft className="h-4 w-4" />
      {label}
    </button>
  );
}

// components/upload/file-item.tsx
"use client"

import { X } from "lucide-react"

interface FileItemProps {
  file: File
  onDelete: () => void
}

export const FileItem = ({ file, onDelete }: FileItemProps) => {
  return (
    <div className="flex items-center justify-between bg-muted rounded-md px-3 py-2">
      <div className="text-sm truncate">
        {file.name}
      </div>
      <button
        onClick={onDelete}
        className="text-muted-foreground hover:text-destructive"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

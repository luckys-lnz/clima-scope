// components/upload/FileUploadSection.tsx
"use client"

import { Upload } from "lucide-react"
import { FileItem } from "./file-item"

interface FileUploadSectionProps {
  title: string
  description: string
  files: File[]
  onFileSelect: (files: FileList | null) => void
  onDeleteFile: (index: number) => void
  accept: string
  uploadRef: React.RefObject<HTMLInputElement | null>
  onDragOver?: (e: React.DragEvent) => void
  onDrop?: (e: React.DragEvent) => void
}

export const FileUploadSection = ({
  title,
  description,
  files,
  onFileSelect,
  onDeleteFile,
  accept,
  uploadRef,
  onDragOver,
  onDrop,
}: FileUploadSectionProps) => {
  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <h2 className="font-bold text-lg text-card-foreground mb-4">{title}</h2>

      {/* Dropzone */}
      <div
        onClick={() => uploadRef.current?.click()}
        onDrop={onDrop}
        onDragOver={onDragOver}
        className="border-2 border-dashed border-border rounded-lg p-12 text-center hover:bg-muted/50 transition-colors cursor-pointer"
      >
        <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
        <p className="text-sm font-medium mb-1">
          Drag and drop files or click to select
        </p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>

      {/* Hidden input */}
      <input
        type="file"
        ref={uploadRef}
        accept={accept}
        multiple
        onChange={(e) => onFileSelect(e.target.files)}
        className="hidden"
      />

      {/* Files list */}
      {files.length > 0 && (
        <div className="mt-4 space-y-2">
          {files.map((file, index) => (
            <FileItem
              key={`${file.name}-${index}`}
              file={file}
              onDelete={() => onDeleteFile(index)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

"use client"

interface TextInputProps {
  label: string
  value: string
  placeholder?: string
  readOnly?: boolean
  description?: string
  onChange?: (value: string) => void
}

export function TextInput({ label, value, placeholder, readOnly, description, onChange }: TextInputProps) {
  return (
    <div>
      <label className="block text-sm font-medium text-card-foreground mb-2">{label}</label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        placeholder={placeholder}
        readOnly={readOnly}
        className={`w-full px-4 py-2 rounded-lg border border-border bg-card text-card-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary ${
          readOnly ? "opacity-60 cursor-not-allowed" : ""
        }`}
      />
      {description && <p className="text-xs text-muted-foreground mt-2">{description}</p>}
    </div>
  )
}

"use client"

interface SelectOption {
  value: string
  label: string
}

interface SelectInputProps {
  value: string
  onChange: (value: string) => void
  options: SelectOption[]
  placeholder?: string
}

export function SelectInput({ value, onChange, options, placeholder }: SelectInputProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-4 py-2 rounded-lg border border-border bg-card text-card-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
    >
      {placeholder && <option value="">{placeholder}</option>}
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}

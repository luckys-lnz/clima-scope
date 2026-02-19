interface UsageRowProps {
    label: string
    value: string | number
  }
  
  export function UsageRow({ label, value }: UsageRowProps) {
    return (
      <div className="flex justify-between">
        <span>{label}</span>
        <span className="font-semibold">{value}</span>
      </div>
    )
  }
  
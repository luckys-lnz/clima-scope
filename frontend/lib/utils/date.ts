export function formatRelativeDate(iso?: string | null): string {
    if (!iso) return "—"
  
    const date = new Date(iso)
    if (isNaN(date.getTime())) return "—"
  
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    if (diffMs < 0) return "—"
  
    const minutes = Math.floor(diffMs / 60000)
    const hours = Math.floor(diffMs / 3600000)
    const days = Math.floor(diffMs / 86400000)
    const weeks = Math.floor(days / 7)
  
    if (minutes < 1) return "Just now"
    if (minutes < 60) return `${minutes} min ago`
    if (hours < 24) return `${hours} hr ago`
    if (days < 7) return `${days} day${days > 1 ? "s" : ""} ago`
    if (days < 30) return `${weeks} week${weeks > 1 ? "s" : ""} ago`
  
    // ≥ 30 days → absolute date
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
}
  
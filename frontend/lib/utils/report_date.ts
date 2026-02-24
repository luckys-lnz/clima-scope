export interface WeeklyReportWindow {
    start: Date
    end: Date
    week: number
    year: number
  }
  
  /**
   * ISO week number
   * Monday-based week (ISO-8601)
   */
  export function getISOWeek(date: Date): number {
    const tmp = new Date(date.getTime())
    tmp.setHours(0, 0, 0, 0)
  
    // Thursday in current week decides the year
    tmp.setDate(tmp.getDate() + 3 - ((tmp.getDay() + 6) % 7))
  
    const week1 = new Date(tmp.getFullYear(), 0, 4)
    return (
      1 +
      Math.round(
        ((tmp.getTime() - week1.getTime()) / 86400000 - 3 + ((week1.getDay() + 6) % 7)) / 7
      )
    )
  }
  
  /**
   * Weekly report window (Tue → next Mon)
   * Anchored from the Monday of the current week
   */
  export function getWeeklyReportWindowFromMonday(monday: Date): WeeklyReportWindow {
    const start = new Date(monday)
    start.setDate(monday.getDate() + 1) // Tuesday
  
    const end = new Date(monday)
    end.setDate(monday.getDate() + 7) // next Monday
  
    const week = getISOWeek(monday) // ISO week based on Monday
    const year = monday.getFullYear()
  
    return { start, end, week, year }
  }
  
  /**
   * Get the weekly report window for TODAY
   * Always returns current week's Tue → next Mon
   */
  export function getCurrentWeeklyReportWindow(today = new Date()): WeeklyReportWindow {
    const day = today.getDay() // 0=Sun,1=Mon,2=Tue...
    const monday = new Date(today)
  
    // Find Monday of the current week
    const diff = day === 0 ? -6 : 1 - day // Sunday → go back 6 days, else 1 - day
    monday.setDate(today.getDate() + diff)
  
    return getWeeklyReportWindowFromMonday(monday)
  }
  
  /**
   * Format window for display in UI
   * Example: Week 9 (Feb 17 - Feb 23) - 2026
   */
  export function formatWeeklyReportWindow(window: WeeklyReportWindow): string {
    const opts: Intl.DateTimeFormatOptions = { month: "short", day: "numeric" }
    const start = window.start.toLocaleDateString("en-US", opts)
    const end = window.end.toLocaleDateString("en-US", opts)
    return `Week ${window.week} (${start} - ${end}) - ${window.year}`
  }
  
  /**
   * Forecast window from any day
   * Returns the report window for the current week if today is Tue–Mon
   * If today is Monday → current week
   * If today is Sunday → still current week
   */
  export function getForecastWindowFromAnyDay(today = new Date()): WeeklyReportWindow {
    return getCurrentWeeklyReportWindow(today)
  }

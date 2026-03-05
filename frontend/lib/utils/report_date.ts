export interface WeeklyReportWindow {
    start: Date
    end: Date
    week: number
    year: number
  }

export interface ISOWeekInfo {
  week: number
  year: number
}
  
  /**
   * ISO week number
   * Monday-based week (ISO-8601)
   */
export function getISOWeek(date: Date): number {
    return getISOWeekInfo(date).week
  }

  /**
   * ISO week + ISO year
   */
  export function getISOWeekInfo(date: Date): ISOWeekInfo {
    const tmp = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
    const day = tmp.getUTCDay() || 7 // Sunday => 7
    tmp.setUTCDate(tmp.getUTCDate() + 4 - day) // Thursday of this ISO week
    const isoYear = tmp.getUTCFullYear()
    const yearStart = new Date(Date.UTC(isoYear, 0, 1))
    const week = Math.ceil((((tmp.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
    return { week, year: isoYear }
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
  
    const iso = getISOWeekInfo(monday)
    const week = iso.week
    const year = iso.year
  
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

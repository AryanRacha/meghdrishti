import { useEffect, useMemo, useRef, useState } from 'react'
import { formatDate } from '../../lib/format'

interface DateDropdownProps {
  dates: string[]
  date: string
  onDate: (date: string) => void
  onOpenChange?: (open: boolean) => void
}

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
]

const WEEK_DAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']

function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate()
}

function getFirstDayOfWeek(year: number, month: number): number {
  return new Date(year, month, 1).getDay()
}

function pad(n: number): string {
  return String(n).padStart(2, '0')
}

function toIso(year: number, month: number, day: number): string {
  return `${year}-${pad(month + 1)}-${pad(day)}`
}

export function DateDropdown({ dates, date, onDate, onOpenChange }: DateDropdownProps) {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  // Maximum initialization date: Strictly Today (the future is navigated via the Lead Time slider)
  const { todayIso, maxIso, minYear, maxYear } = useMemo(() => {
    const now = new Date()
    const tIso = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
    const maxDate = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const mIso = tIso
    return {
      todayIso: tIso,
      maxIso: mIso,
      minYear: 2021,
      maxYear: maxDate.getFullYear(),
    }
  }, [])

  // Parse currently selected date
  const parsedDate = useMemo(() => {
    if (!date) return new Date()
    const parts = date.split('-').map(Number)
    if (parts.length === 3 && !isNaN(parts[0]) && !isNaN(parts[1]) && !isNaN(parts[2])) {
      return new Date(parts[0], parts[1] - 1, parts[2])
    }
    return new Date()
  }, [date])

  const [viewYear, setViewYear] = useState(parsedDate.getFullYear())
  const [viewMonth, setViewMonth] = useState(parsedDate.getMonth())

  // Keep view aligned when date prop updates
  useEffect(() => {
    setViewYear(parsedDate.getFullYear())
    setViewMonth(parsedDate.getMonth())
  }, [parsedDate])

  // Notify parent of open state
  useEffect(() => {
    onOpenChange?.(open)
  }, [open, onOpenChange])

  // Close on click outside or Escape key
  useEffect(() => {
    if (!open) return
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('mousedown', handleClickOutside)
    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('mousedown', handleClickOutside)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [open])

  // Navigation handlers
  const canGoNext = useMemo(() => {
    const nextMonth = viewMonth === 11 ? 0 : viewMonth + 1
    const nextYear = viewMonth === 11 ? viewYear + 1 : viewYear
    const firstDayNextMonth = toIso(nextYear, nextMonth, 1)
    return firstDayNextMonth <= maxIso
  }, [viewMonth, viewYear, maxIso])

  const handlePrevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11)
      setViewYear((y) => Math.max(minYear, y - 1))
    } else {
      setViewMonth((m) => m - 1)
    }
  }

  const handleNextMonth = () => {
    if (!canGoNext) return
    if (viewMonth === 11) {
      setViewMonth(0)
      setViewYear((y) => Math.min(maxYear, y + 1))
    } else {
      setViewMonth((m) => m + 1)
    }
  }

  // Generate calendar days
  const daysInMonth = getDaysInMonth(viewYear, viewMonth)
  const firstDayOfWeek = getFirstDayOfWeek(viewYear, viewMonth)

  // Year options for selector
  const yearOptions = useMemo(() => {
    const list: number[] = []
    for (let y = minYear; y <= maxYear; y++) {
      list.push(y)
    }
    return list
  }, [minYear, maxYear])

  return (
    <div ref={containerRef} className="relative min-w-0 flex-1">
      {/* Trigger Button */}
      <button
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label="Select forecast date from calendar"
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between gap-2 rounded-xl bg-white/5 px-3 py-2 text-sm text-slate-100 ring-1 ring-white/10 outline-none transition-colors hover:bg-white/10 hover:ring-white/20 focus-visible:ring-cyan-400/60 cursor-pointer"
      >
        <div className="flex items-center gap-2 min-w-0 truncate">
          <svg className="h-4 w-4 shrink-0 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span className="truncate font-medium">{formatDate(date)}</span>
        </div>
        <svg
          className={`h-4 w-4 shrink-0 text-cyan-400/80 transition-transform duration-200 ${
            open ? 'rotate-180 text-cyan-300' : ''
          }`}
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {/* Interactive Calendar Popover */}
      {open && (
        <div
          role="dialog"
          aria-label="Calendar date picker"
          className="absolute left-0 bottom-[calc(100%+0.5rem)] sm:bottom-auto sm:top-[calc(100%+0.5rem)] z-50 w-76 sm:w-80 rounded-2xl bg-slate-900/98 backdrop-blur-2xl p-3.5 shadow-2xl ring-1 ring-white/15 outline-none select-none animate-in fade-in zoom-in-95 duration-150"
        >
          {/* Calendar Header with Month/Year Navigation */}
          <div className="flex items-center justify-between gap-1.5 pb-2.5 border-b border-white/10">
            <button
              type="button"
              onClick={handlePrevMonth}
              aria-label="Previous month"
              className="grid h-7 w-7 place-items-center rounded-lg text-slate-300 hover:bg-white/10 hover:text-white transition-colors cursor-pointer"
            >
              ‹
            </button>

            <div className="flex items-center gap-1.5 font-medium text-sm text-slate-100">
              <select
                aria-label="Select month"
                value={viewMonth}
                onChange={(e) => setViewMonth(Number(e.target.value))}
                className="bg-slate-800/80 hover:bg-slate-800 text-cyan-200 text-xs font-semibold py-1 px-2 rounded-lg border border-white/10 outline-none cursor-pointer focus:ring-1 focus:ring-cyan-400"
              >
                {MONTH_NAMES.map((m, idx) => (
                  <option key={m} value={idx} className="bg-slate-900 text-slate-200">
                    {m}
                  </option>
                ))}
              </select>

              <select
                aria-label="Select year"
                value={viewYear}
                onChange={(e) => setViewYear(Number(e.target.value))}
                className="bg-slate-800/80 hover:bg-slate-800 text-cyan-200 text-xs font-semibold py-1 px-2 rounded-lg border border-white/10 outline-none cursor-pointer focus:ring-1 focus:ring-cyan-400"
              >
                {yearOptions.map((y) => (
                  <option key={y} value={y} className="bg-slate-900 text-slate-200">
                    {y}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="button"
              onClick={handleNextMonth}
              disabled={!canGoNext}
              aria-label="Next month"
              className={`grid h-7 w-7 place-items-center rounded-lg text-slate-300 transition-colors cursor-pointer ${
                canGoNext ? 'hover:bg-white/10 hover:text-white' : 'opacity-20 cursor-not-allowed pointer-events-none'
              }`}
            >
              ›
            </button>
          </div>

          {/* Days of Week Header */}
          <div className="grid grid-cols-7 gap-1 pt-2 pb-1 text-center font-mono text-[10px] font-semibold text-slate-400">
            {WEEK_DAYS.map((d) => (
              <div key={d}>{d}</div>
            ))}
          </div>

          {/* Days Grid */}
          <div className="grid grid-cols-7 gap-1 text-center text-xs">
            {/* Empty slots for start of month */}
            {Array.from({ length: firstDayOfWeek }).map((_, i) => (
              <div key={`empty-${i}`} className="h-8 w-full" />
            ))}

            {/* Days in Month */}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const dayNum = i + 1
              const dayIso = toIso(viewYear, viewMonth, dayNum)
              const isSelected = dayIso === date
              const isToday = dayIso === todayIso
              const isFutureUnpredictable = dayIso > maxIso
              const isBenchmarkDate = dates.includes(dayIso)

              return (
                <button
                  key={dayIso}
                  type="button"
                  disabled={isFutureUnpredictable}
                  onClick={() => {
                    onDate(dayIso)
                    setOpen(false)
                  }}
                  className={`relative flex h-8 w-full items-center justify-center rounded-lg text-xs font-medium transition-all ${
                    isFutureUnpredictable
                      ? 'opacity-20 text-slate-500 cursor-not-allowed pointer-events-none'
                      : isSelected
                      ? 'bg-cyan-500 text-slate-950 font-bold shadow-lg shadow-cyan-500/40 ring-1 ring-cyan-300 scale-105 cursor-pointer'
                      : 'text-slate-200 hover:bg-white/15 hover:text-white cursor-pointer'
                  } ${isToday && !isSelected ? 'ring-1 ring-cyan-400/60 font-semibold text-cyan-300' : ''}`}
                >
                  <span>{dayNum}</span>

                  {/* Indicator dot for benchmark/cached dates */}
                  {isBenchmarkDate && !isSelected && (
                    <span className="absolute bottom-1 h-1 w-1 rounded-full bg-cyan-400" />
                  )}
                </button>
              )
            })}
          </div>

          {/* Quick-Jump Presets */}
          <div className="mt-3 pt-2.5 border-t border-white/10 flex items-center justify-between gap-1 text-[11px]">
            <button
              type="button"
              onClick={() => {
                onDate('2023-08-15')
                setOpen(false)
              }}
              className="text-cyan-300 hover:text-cyan-200 hover:underline py-0.5 px-1.5 rounded cursor-pointer font-medium"
            >
              🌧️ Aug 2023 Monsoon
            </button>
            <button
              type="button"
              onClick={() => {
                onDate(todayIso)
                setOpen(false)
              }}
              className="bg-white/10 hover:bg-white/20 text-slate-100 font-semibold py-1 px-2.5 rounded-lg cursor-pointer transition-colors"
            >
              Today
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

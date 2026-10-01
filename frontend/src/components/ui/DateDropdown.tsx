import { useEffect, useRef, useState } from 'react'
import { formatDate } from '../../lib/format'

interface DateDropdownProps {
  dates: string[]
  date: string
  onDate: (date: string) => void
  onOpenChange?: (open: boolean) => void
}

export function DateDropdown({ dates, date, onDate, onOpenChange }: DateDropdownProps) {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const activeItemRef = useRef<HTMLButtonElement>(null)

  // Notify parent of open state
  useEffect(() => {
    onOpenChange?.(open)
  }, [open, onOpenChange])

  // Close on click outside
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

  // Scroll active item into view within the dropdown list
  useEffect(() => {
    if (open && activeItemRef.current && listRef.current) {
      const item = activeItemRef.current
      const list = listRef.current
      const itemTop = item.offsetTop
      const itemBottom = itemTop + item.offsetHeight
      if (itemTop < list.scrollTop) {
        list.scrollTop = itemTop
      } else if (itemBottom > list.scrollTop + list.clientHeight) {
        list.scrollTop = itemBottom - list.clientHeight
      }
    }
  }, [open])

  return (
    <div ref={containerRef} className="relative min-w-0 flex-1">
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label="Forecast date"
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between rounded-xl bg-white/5 px-3.5 py-2 text-sm text-slate-100 ring-1 ring-white/10 outline-none transition-colors hover:bg-white/10 hover:ring-white/20 focus-visible:ring-cyan-400/60 cursor-pointer"
      >
        <span className="truncate font-medium">{formatDate(date)}</span>
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

      {open && (
        <div
          ref={listRef}
          role="listbox"
          aria-label="Forecast dates"
          className="custom-scrollbar absolute left-0 top-[calc(100%+0.35rem)] z-50 w-full min-w-[11rem] max-h-72 overflow-y-auto overflow-x-hidden rounded-xl bg-slate-900/95 backdrop-blur-xl p-1 shadow-2xl ring-1 ring-white/15 outline-none"
        >
          {dates.map((d) => {
            const isSelected = d === date
            return (
              <button
                key={d}
                ref={isSelected ? activeItemRef : null}
                type="button"
                role="option"
                aria-selected={isSelected}
                onClick={() => {
                  onDate(d)
                  setOpen(false)
                }}
                className={`flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm font-medium transition-colors cursor-pointer ${
                  isSelected
                    ? 'bg-cyan-500/20 text-cyan-200 ring-1 ring-cyan-400/40'
                    : 'text-slate-200 hover:bg-white/10 hover:text-white'
                }`}
              >
                <span>{formatDate(d)}</span>
                {isSelected && (
                  <span className="text-xs text-cyan-400">●</span>
                )}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

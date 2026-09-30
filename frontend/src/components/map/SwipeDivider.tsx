import { useRef } from 'react'

interface SwipeDividerProps {
  position: number
  onChange: (position: number) => void
  leftLabel: string
  rightLabel: string
}

const MIN = 0.02
const MAX = 0.98

/** Draggable vertical divider overlay for the swipe comparison (map container = full viewport). */
export function SwipeDivider({ position, onChange, leftLabel, rightLabel }: SwipeDividerProps) {
  const dragging = useRef(false)

  const move = (clientX: number) => {
    onChange(Math.min(MAX, Math.max(MIN, clientX / window.innerWidth)))
  }

  return (
    <div className="pointer-events-none absolute inset-y-0 z-[1050]" style={{ left: `${position * 100}%` }}>
      <div className="absolute inset-y-0 -left-px w-0.5 bg-white/80 shadow-[0_0_12px_rgba(255,255,255,0.6)]" />

      <div className="absolute top-[38%] right-4 rounded-md bg-slate-950/70 px-2 py-1 text-[11px] font-semibold tracking-wide whitespace-nowrap text-slate-200 uppercase ring-1 ring-white/15 backdrop-blur">
        {leftLabel}
      </div>
      <div className="absolute top-[38%] left-4 rounded-md bg-cyan-500/20 px-2 py-1 text-[11px] font-semibold tracking-wide whitespace-nowrap text-cyan-100 uppercase ring-1 ring-cyan-300/40 backdrop-blur">
        {rightLabel}
      </div>

      <button
        type="button"
        aria-label="Drag to compare"
        onPointerDown={(e) => {
          dragging.current = true
          e.currentTarget.setPointerCapture(e.pointerId)
        }}
        onPointerMove={(e) => dragging.current && move(e.clientX)}
        onPointerUp={() => (dragging.current = false)}
        onKeyDown={(e) => {
          if (e.key === 'ArrowLeft') onChange(Math.max(MIN, position - 0.02))
          if (e.key === 'ArrowRight') onChange(Math.min(MAX, position + 0.02))
        }}
        className="pointer-events-auto absolute top-1/2 -left-5 grid size-10 -translate-y-1/2 cursor-ew-resize touch-none place-items-center rounded-full bg-white text-slate-900 shadow-xl ring-4 ring-white/20"
      >
        <span aria-hidden className="text-sm font-bold">⇆</span>
      </button>
    </div>
  )
}

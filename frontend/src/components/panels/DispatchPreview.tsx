import { useEffect, useState } from 'react'
import { formatPeople } from '../../lib/format'
import type { Threat } from '../../types/forecast'

interface DispatchPreviewProps {
  threat: Threat
  text: string
  speechLang: string
  onClose: () => void
}

const CHANNELS = ['Cell Broadcast', 'SMS', 'WhatsApp', 'District Control Room']

export function DispatchPreview({ threat, text, speechLang, onClose }: DispatchPreviewProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const [time] = useState(() => new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }))

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Alert dispatch preview"
      onClick={onClose}
      className="pointer-events-auto absolute inset-0 z-10 grid place-items-center bg-slate-950/60 p-4 backdrop-blur-sm"
    >
      <div onClick={(e) => e.stopPropagation()} className="flex flex-col items-center gap-6 md:flex-row md:items-stretch">
        {/* Phone */}
        <div className="appear relative h-[30rem] w-64 shrink-0 rounded-[2.5rem] border-[6px] border-slate-700 bg-gradient-to-b from-slate-800 to-slate-950 p-3 shadow-2xl">
          <div className="mx-auto mb-4 h-5 w-24 rounded-full bg-slate-900" />
          <p className="text-center font-mono text-3xl font-light text-white">{time}</p>
          <div className="appear mt-6 rounded-2xl bg-slate-100/95 p-3 text-slate-900 shadow-lg" style={{ animationDelay: '0.4s' }}>
            <div className="flex items-center gap-2">
              <span className="grid size-6 place-items-center rounded-md bg-red-600 text-xs font-bold text-white">!</span>
              <span className="text-[11px] font-bold tracking-wide uppercase">Emergency alert · Severe</span>
            </div>
            <p lang={speechLang} className="mt-2 line-clamp-[12] text-[11px] leading-snug">
              {text}
            </p>
          </div>
        </div>

        {/* Dispatch status */}
        <div className="appear glass w-72 rounded-2xl p-5" style={{ animationDelay: '0.2s' }}>
          <p className="text-[11px] font-semibold tracking-[0.14em] text-slate-400 uppercase">Alert preview</p>
          <p className="mt-1 text-lg font-semibold text-white">{threat.district}</p>
          <p className="text-sm text-slate-400">
            Target reach <span className="font-semibold text-slate-100">{formatPeople(threat.population_exposed)}</span>
          </p>
          <ul className="mt-4 space-y-2.5">
            {CHANNELS.map((channel, i) => (
              <li key={channel} className="appear flex items-center gap-3 text-sm" style={{ animationDelay: `${0.8 + i * 0.45}s` }}>
                <span className="grid size-5 place-items-center rounded-full bg-emerald-400/15 text-xs text-emerald-300 ring-1 ring-emerald-400/40">
                  ✓
                </span>
                <span className="text-slate-200">{channel}</span>
                <span className="ml-auto font-mono text-[11px] text-emerald-300">queued</span>
              </li>
            ))}
          </ul>
          <button
            type="button"
            onClick={onClose}
            className="mt-5 w-full rounded-lg bg-white/5 py-2 text-sm text-slate-200 ring-1 ring-white/15 hover:bg-white/10"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

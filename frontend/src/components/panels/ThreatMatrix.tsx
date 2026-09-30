import { useState } from 'react'
import { GlassPanel, PanelTitle } from '../ui/GlassPanel'
import { CATEGORY_LABELS, CATEGORY_STYLES, formatPeople } from '../../lib/format'
import type { Threat } from '../../types/forecast'

interface ThreatMatrixProps {
  threats: Threat[]
  loading: boolean
  selectedId: string | null
  onSelect: (id: string) => void
  onOpenBulletin?: () => void
}

const NEAR_KM = 60

function riskTone(risk: number): string {
  if (risk >= 70) return 'text-red-300 ring-red-500/40 bg-red-600/15'
  if (risk >= 50) return 'text-orange-300 ring-orange-500/30 bg-orange-500/10'
  return 'text-yellow-200 ring-yellow-400/30 bg-yellow-400/10'
}

function TrustBar({ gfsTrust }: { gfsTrust: number }) {
  const gfs = Math.round(gfsTrust * 100)
  return (
    <div className="space-y-1">
      <div className="flex h-1.5 overflow-hidden rounded-full bg-white/5">
        <div className="bg-teal-400" style={{ width: `${gfs}%` }} />
        <div className="flex-1 bg-violet-500" />
      </div>
      <div className="flex justify-between text-[10px] text-slate-500">
        <span>GFS {gfs}%</span>
        <span>AI {100 - gfs}%</span>
      </div>
    </div>
  )
}

function ThreatCard({ threat, selected, onSelect }: { threat: Threat; selected: boolean; onSelect: () => void }) {
  const t = threat
  return (
    <li>
      <button
        type="button"
        onClick={onSelect}
        aria-pressed={selected}
        className={`w-full rounded-xl p-3 text-left ring-1 transition-colors focus-visible:outline-2 focus-visible:outline-accent ${
          selected ? 'bg-white/10 ring-cyan-400/50' : 'bg-white/[0.03] ring-white/10 hover:bg-white/[0.07]'
        }`}
      >
        <div className="flex items-start gap-3">
          <span className="mt-0.5 font-mono text-xs text-slate-500">#{t.severity_rank}</span>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-white">{t.district}</p>
                <p className="truncate text-xs text-slate-400">
                  {t.distance_km > NEAR_KM ? `~${Math.round(t.distance_km)} km from HQ · ` : ''}
                  {t.state}
                </p>
              </div>
              <div className="text-right">
                <p className="font-mono text-lg leading-none font-semibold text-white tabular-nums">{t.peak_mm}</p>
                <p className="text-[10px] text-slate-500">mm peak</p>
              </div>
            </div>

            <div className="mt-2 flex items-center gap-2">
              <span className={`rounded-md px-1.5 py-0.5 text-[10px] font-semibold uppercase ring-1 ${CATEGORY_STYLES[t.category]}`}>
                {CATEGORY_LABELS[t.category]}
              </span>
              <span className={`rounded-md px-1.5 py-0.5 font-mono text-[10px] font-semibold ring-1 ${riskTone(t.risk_index)}`}>
                RISK {t.risk_index}
              </span>
              <span className="ml-auto font-mono text-[11px] text-slate-500">{t.area_km2.toLocaleString('en-IN')} km²</span>
            </div>

            <p className="mt-2 text-xs text-slate-300">
              <span className="font-semibold text-white">{formatPeople(t.population_exposed)}</span> people in affected area
            </p>

            <dl className="mt-2.5 grid grid-cols-2 gap-x-3 font-mono text-[11px]">
              <div className="flex justify-between">
                <dt className="text-slate-500">GFS</dt>
                <dd className="text-slate-300 tabular-nums">{t.gfs_mm} mm</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">AI</dt>
                <dd className="text-slate-300 tabular-nums">{t.ai_mm} mm</dd>
              </div>
            </dl>
            <div className="mt-2">
              <TrustBar gfsTrust={t.gfs_trust} />
            </div>
          </div>
        </div>
      </button>
    </li>
  )
}

export function ThreatMatrix({ threats, loading, selectedId, onSelect, onOpenBulletin }: ThreatMatrixProps) {
  const [open, setOpen] = useState(false) // mobile bottom sheet only
  const extreme = threats.filter((t) => t.category !== 'heavy').length
  const exposed = threats.reduce((sum, t) => sum + t.population_exposed, 0)

  return (
    <GlassPanel
      as="aside"
      label="Threat matrix"
      className={`flex flex-col overflow-hidden rounded-b-none lg:rounded-2xl ${open ? 'max-h-[60vh]' : 'max-h-16'} lg:max-h-none lg:h-full`}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex items-center justify-between gap-3 border-b border-white/10 px-4 py-3 text-left lg:pointer-events-none"
      >
        <div>
          <PanelTitle>Threat Matrix</PanelTitle>
          <p className="mt-0.5 text-xs text-slate-400">
            IMD heavy rain ≥ 64.5 mm{exposed > 0 && <> · <span className="text-slate-200">{formatPeople(exposed)}</span> exposed</>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {extreme > 0 && (
            <span className="rounded-md bg-red-600/20 px-2 py-0.5 font-mono text-xs font-semibold text-red-300 ring-1 ring-red-500/40">
              {extreme} severe
            </span>
          )}
          <span className="rounded-md bg-white/5 px-2 py-0.5 font-mono text-xs text-slate-300 ring-1 ring-white/10">{threats.length}</span>
        </div>
      </button>

      <ul className={`scrollbar-thin flex-1 space-y-2 overflow-y-auto p-3 transition-opacity ${loading ? 'opacity-50' : ''}`}>
        {threats.length === 0 && !loading && (
          <li className="px-2 py-8 text-center text-sm text-slate-400">No heavy-rain regions in this forecast.</li>
        )}
        {threats.map((t) => (
          <ThreatCard key={t.id} threat={t} selected={t.id === selectedId} onSelect={() => onSelect(t.id)} />
        ))}
      </ul>

      {onOpenBulletin && (
        <div className="border-t border-white/10 p-2.5">
          <button
            type="button"
            onClick={onOpenBulletin}
            className="flex w-full items-center justify-center gap-1.5 rounded-xl bg-red-600/20 py-2 text-xs font-semibold text-red-200 ring-1 ring-red-500/40 transition-colors hover:bg-red-600/30 hover:text-white"
          >
            <span>Generate Official IMD Bulletin</span>
            <span>📄</span>
          </button>
        </div>
      )}
    </GlassPanel>
  )
}

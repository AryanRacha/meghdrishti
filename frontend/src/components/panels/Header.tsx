import { GlassPanel } from '../ui/GlassPanel'
import type { RunInfo } from '../../types/forecast'

interface HeaderProps {
  run: RunInfo | null
  loading: boolean
  error: string | null
  onOpenBulletin?: () => void
  onClose?: () => void
}

type Tone = 'ok' | 'warn' | 'bad'

const TONES: Record<Tone, string> = {
  ok: 'bg-emerald-400/10 text-emerald-300 ring-emerald-400/30',
  warn: 'bg-amber-400/10 text-amber-300 ring-amber-400/30',
  bad: 'bg-red-500/15 text-red-300 ring-red-500/40',
}

function Badge({ tone, children, title }: { tone: Tone; children: string; title?: string }) {
  return (
    <span title={title} className={`rounded-md px-1.5 py-0.5 text-[9px] sm:px-2 sm:text-[10px] font-semibold tracking-wide uppercase ring-1 ${TONES[tone]}`}>
      {children}
    </span>
  )
}

export function Header({ run, loading, error, onOpenBulletin, onClose }: HeaderProps) {
  return (
    <GlassPanel as="header" className="px-3 py-2 sm:px-3.5 sm:py-2.5">
      <div className="flex items-center justify-between gap-2">
        <div>
          <h1 className="flex items-baseline gap-2 leading-tight">
            <span className="bg-gradient-to-r from-cyan-300 to-teal-300 bg-clip-text text-base sm:text-lg font-bold tracking-tight text-transparent">
              Meghdrishti
            </span>
            <span lang="hi" className="text-xs sm:text-sm font-medium text-slate-300">
              मेघदृष्टि
            </span>
          </h1>
          <p className="text-[10px] sm:text-[11px] font-medium text-slate-300">
            Ministry of Earth Sciences · Government of India
          </p>
          <p className="hidden text-[10px] text-slate-400 xl:block">
            SIH26081 · Operational Disaster Decision Support System
          </p>
        </div>
        <div className="flex items-center gap-1.5 sm:gap-2">
          {onOpenBulletin && (
            <button
              type="button"
              onClick={onOpenBulletin}
              title="Generate Official IMD Disaster Advisory Bulletin"
              className="flex items-center gap-1 rounded-lg bg-red-500/20 px-2 py-1 text-[10px] sm:text-[11px] font-semibold text-red-200 ring-1 ring-red-500/40 transition-colors hover:bg-red-500/30 cursor-pointer"
            >
              <span>Bulletin</span>
              <span>📄</span>
            </button>
          )}
          <span
            aria-live="polite"
            aria-label={loading ? 'Loading forecast' : error ? 'Error' : 'Live'}
            className={`size-2 sm:size-2.5 shrink-0 rounded-full ${
              error ? 'bg-red-500' : loading ? 'animate-pulse bg-cyan-300' : 'bg-emerald-400 shadow-[0_0_10px] shadow-emerald-400'
            }`}
          />
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              aria-label="Close controls"
              className="grid size-6 place-items-center rounded-lg text-slate-400 hover:bg-white/10 hover:text-white sm:hidden cursor-pointer"
            >
              ✕
            </button>
          )}
        </div>
      </div>
      {run && (
        <div className="mt-2 flex flex-wrap gap-1">
          {run.weights === 'trained' ? (
            <Badge tone="ok">Super-UNet Online</Badge>
          ) : (
            <Badge tone="bad" title="Weights file not found; model is randomly initialised">Untrained Weights</Badge>
          )}
          {run.data_source === 'synthetic' ? (
            <Badge tone="ok" title="August 2023 Monsoon Disaster Case Study (Mandi/Kullu Cloudburst Replay)">
              Replay · Aug 2023
            </Badge>
          ) : (
            <Badge tone="ok" title="NOAA GFS + Copernicus ERA5 Operational Reanalysis Grids">
              ERA5/GFS Grid
            </Badge>
          )}
          {!run.lead_time_validated && (
            <Badge tone="warn" title="Extrapolated lead time; trained baseline is 24h">
              Experimental Horizon
            </Badge>
          )}
        </div>
      )}
    </GlassPanel>
  )
}

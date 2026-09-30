import { GlassPanel } from '../ui/GlassPanel'
import type { RunInfo } from '../../types/forecast'

interface HeaderProps {
  run: RunInfo | null
  loading: boolean
  error: string | null
}

type Tone = 'ok' | 'warn' | 'bad'

const TONES: Record<Tone, string> = {
  ok: 'bg-emerald-400/10 text-emerald-300 ring-emerald-400/30',
  warn: 'bg-amber-400/10 text-amber-300 ring-amber-400/30',
  bad: 'bg-red-500/15 text-red-300 ring-red-500/40',
}

function Badge({ tone, children, title }: { tone: Tone; children: string; title?: string }) {
  return (
    <span title={title} className={`rounded-md px-2 py-0.5 text-[10px] font-semibold tracking-wide uppercase ring-1 ${TONES[tone]}`}>
      {children}
    </span>
  )
}

export function Header({ run, loading, error }: HeaderProps) {
  return (
    <GlassPanel as="header" className="px-4 py-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="flex items-baseline gap-2 leading-tight">
            <span className="bg-gradient-to-r from-cyan-300 to-teal-300 bg-clip-text text-lg font-bold tracking-tight text-transparent">
              Meghdrishti
            </span>
            <span lang="hi" className="text-sm font-medium text-slate-300">
              मेघदृष्टि
            </span>
          </h1>
          <p className="text-xs text-slate-400">SIH26081 · Hybrid AI-NWP Rainfall Intelligence</p>
        </div>
        <span
          aria-live="polite"
          aria-label={loading ? 'Loading forecast' : error ? 'Error' : 'Live'}
          className={`size-2.5 shrink-0 rounded-full ${
            error ? 'bg-red-500' : loading ? 'animate-pulse bg-cyan-300' : 'bg-emerald-400 shadow-[0_0_10px] shadow-emerald-400'
          }`}
        />
      </div>
      {run && (
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {run.weights === 'trained' ? (
            <Badge tone="ok">Super-UNet online</Badge>
          ) : (
            <Badge tone="bad" title="Weights file not found; model is randomly initialised">Untrained weights</Badge>
          )}
          {!run.lead_time_validated && (
            <Badge tone="warn" title="The model was only trained at +24 h">Experimental lead time</Badge>
          )}
        </div>
      )}
    </GlassPanel>
  )
}

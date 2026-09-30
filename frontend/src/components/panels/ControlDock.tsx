import { DateDropdown } from '../ui/DateDropdown'
import { GlassPanel, PanelTitle } from '../ui/GlassPanel'
import { Segmented } from '../ui/Segmented'
import { LAYER_LABELS, VARIABLE_LABELS, leadTimeLabel } from '../../lib/format'
import type { Layer, Variable } from '../../types/forecast'

const VARIABLES: readonly Variable[] = ['rain', 'temp', 'wind']
const LAYERS: readonly Layer[] = ['gfs', 'ai', 'blended', 'trust']

const LAYER_HINTS: Record<Layer, string> = {
  gfs: 'NOAA GFS physical model (raw input).',
  ai: 'AI forecast model (raw input).',
  blended: 'Super-UNet per-pixel blend of GFS and AI.',
  trust: 'Explainable AI: how much the U-Net trusts GFS vs AI at each pixel.',
}

interface ControlDockProps {
  dates: string[]
  date: string
  onDate: (d: string) => void
  leadTimes: number[]
  trainedLeadTimes: number[]
  leadTime: number
  onLeadTime: (h: number) => void
  variable: Variable
  onVariable: (v: Variable) => void
  layer: Layer
  onLayer: (l: Layer) => void
  compare: boolean
  onCompare: (on: boolean) => void
  playing: boolean
  onPlaying: (on: boolean) => void
  onTour: () => void
}

export function ControlDock(props: ControlDockProps) {
  const { dates, date, onDate, leadTimes, trainedLeadTimes, leadTime, onLeadTime } = props
  const leadIndex = Math.max(0, leadTimes.indexOf(leadTime))
  const validated = trainedLeadTimes.includes(leadTime)

  return (
    <GlassPanel as="section" label="Forecast controls" className="space-y-4 p-4">
      <div className="space-y-2">
        <PanelTitle>Variable</PanelTitle>
        <Segmented label="Variable" options={VARIABLES} value={props.variable} onChange={props.onVariable} renderLabel={(v) => VARIABLE_LABELS[v]} />
      </div>

      <div className="space-y-2">
        <PanelTitle>Layer</PanelTitle>
        <div className={props.compare ? 'pointer-events-none opacity-40' : undefined}>
          <Segmented label="Layer" options={LAYERS} value={props.layer} onChange={props.onLayer} renderLabel={(l) => LAYER_LABELS[l]} />
        </div>
        <p className="text-xs leading-relaxed text-slate-400">
          {props.compare ? 'Drag the divider: raw GFS vs Super-UNet blend.' : LAYER_HINTS[props.layer]}
        </p>
      </div>

      <div className="space-y-2">
        <div className="flex items-baseline justify-between">
          <PanelTitle>Lead time</PanelTitle>
          <span className={`font-mono text-xs ${validated ? 'text-cyan-200' : 'text-amber-300'}`}>{leadTimeLabel(leadTime)}</span>
        </div>
        <input
          type="range"
          aria-label="Lead time"
          min={0}
          max={leadTimes.length - 1}
          step={1}
          value={leadIndex}
          onChange={(e) => onLeadTime(leadTimes[Number(e.target.value)])}
          className="w-full accent-cyan-400"
        />
        <div className="flex justify-between font-mono text-[10px] text-slate-500">
          {leadTimes.map((h) => (
            <span key={h} className={trainedLeadTimes.includes(h) ? 'text-slate-300' : undefined}>
              {h}h
            </span>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <PanelTitle>Forecast date</PanelTitle>
        <div className="flex gap-2">
          <DateDropdown dates={dates} date={date} onDate={onDate} />
          <button
            type="button"
            onClick={() => props.onPlaying(!props.playing)}
            aria-label={props.playing ? 'Pause time-lapse' : 'Play time-lapse'}
            aria-pressed={props.playing}
            className={`grid w-10 place-items-center rounded-xl text-sm ring-1 transition-colors ${
              props.playing ? 'bg-cyan-400/20 text-cyan-100 ring-cyan-400/50' : 'bg-white/5 text-slate-200 ring-white/10 hover:text-white'
            }`}
          >
            {props.playing ? '❚❚' : '▶'}
          </button>
        </div>
      </div>

      <button
        type="button"
        aria-pressed={props.compare}
        onClick={() => props.onCompare(!props.compare)}
        className={`w-full rounded-xl px-3 py-2 text-xs font-medium ring-1 transition-colors ${
          props.compare ? 'bg-cyan-400/15 text-cyan-100 ring-cyan-400/40' : 'bg-white/5 text-slate-300 ring-white/10 hover:text-white'
        }`}
      >
        ⇆ Compare GFS vs Blend
      </button>

      <button
        type="button"
        onClick={props.onTour}
        className="w-full rounded-xl bg-gradient-to-r from-cyan-400 to-teal-400 py-2.5 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-900/40 transition-transform hover:scale-[1.01]"
      >
        ▶ Guided Tour
      </button>
    </GlassPanel>
  )
}

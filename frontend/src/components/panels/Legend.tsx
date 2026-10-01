import { GlassPanel, PanelTitle } from '../ui/GlassPanel'
import { cssGradient, type Scale } from '../../lib/colorScales'
import { LAYER_LABELS, VARIABLE_LABELS } from '../../lib/format'
import type { LayerMetadata } from '../../types/forecast'

interface LegendProps {
  metadata: LayerMetadata
  scale: Scale
}

function fmt(v: number, layer: LayerMetadata['layer']): string {
  return layer === 'trust' ? v.toFixed(2) : v.toFixed(1)
}

export function Legend({ metadata, scale }: LegendProps) {
  const { variable, layer, units, min, max } = metadata
  const title = layer === 'trust' ? `Trust map · ${VARIABLE_LABELS[variable]}` : `${LAYER_LABELS[layer]} · ${VARIABLE_LABELS[variable]} (${units})`

  return (
    <GlassPanel as="section" label="Map legend" className="w-64 space-y-2.5 p-4">
      <PanelTitle>{title}</PanelTitle>

      {scale.kind === 'stepped' ? (
        <ul className="space-y-1">
          {[...scale.bins].reverse().map((bin) => (
            <li key={bin.label} className="flex items-center gap-2 text-xs">
              <span className="size-3 rounded-sm ring-1 ring-white/20" style={{ background: bin.color }} />
              <span className="flex-1 text-slate-300">{bin.label}</span>
              <span className="font-mono text-slate-500">≥{bin.min}</span>
            </li>
          ))}
        </ul>
      ) : (
        <div>
          <div className="h-2.5 rounded-full ring-1 ring-white/15" style={{ background: cssGradient(scale.stops) }} />
          <div className="mt-1 flex justify-between text-[11px] text-slate-400">
            <span>{scale.minLabel}</span>
            <span>{scale.maxLabel}</span>
          </div>
        </div>
      )}

      <p className="border-t border-white/10 pt-2 font-mono text-[11px] text-slate-400">
        Range {fmt(min, layer)} – {fmt(max, layer)}
      </p>
    </GlassPanel>
  )
}

import { useState } from 'react'
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
  const [collapsed, setCollapsed] = useState(false)
  const { variable, layer, units, min, max } = metadata
  const title = layer === 'trust' ? `Trust map · ${VARIABLE_LABELS[variable]}` : `${LAYER_LABELS[layer]} · ${VARIABLE_LABELS[variable]} (${units})`

  return (
    <GlassPanel as="section" label="Map legend" className="w-full space-y-1.5 p-2.5 sm:space-y-2 sm:p-3">
      <div
        className="flex items-center justify-between cursor-pointer select-none"
        onClick={() => setCollapsed(!collapsed)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            setCollapsed(!collapsed)
          }
        }}
        aria-expanded={!collapsed}
        aria-label="Toggle map legend"
      >
        <PanelTitle>{title}</PanelTitle>
        <button
          type="button"
          aria-label={collapsed ? 'Expand legend' : 'Collapse legend'}
          className="text-xs text-slate-400 hover:text-cyan-300 transition-colors"
        >
          {collapsed ? '▲' : '▼'}
        </button>
      </div>

      {!collapsed && (
        <>
          {scale.kind === 'stepped' ? (
            <ul className="grid grid-cols-2 gap-x-2.5 gap-y-0.5 sm:gap-y-1">
              {[...scale.bins].reverse().map((bin) => (
                <li key={bin.label} className="flex items-center gap-1.5 text-[10px] sm:text-[11px]">
                  <span className="size-2 sm:size-2.5 rounded-sm ring-1 ring-white/20 shrink-0" style={{ background: bin.color }} />
                  <span className="flex-1 text-slate-300 truncate">{bin.label}</span>
                  <span className="font-mono text-slate-500 shrink-0">≥{bin.min}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div>
              <div className="h-2 sm:h-2.5 rounded-full ring-1 ring-white/15" style={{ background: cssGradient(scale.stops) }} />
              <div className="mt-1 flex justify-between text-[10px] sm:text-[11px] text-slate-400">
                <span>{scale.minLabel}</span>
                <span>{scale.maxLabel}</span>
              </div>
            </div>
          )}

          <p className="border-t border-white/10 pt-1 font-mono text-[9px] sm:text-[10px] text-slate-400">
            Range {fmt(min, layer)} – {fmt(max, layer)}
          </p>
        </>
      )}
    </GlassPanel>
  )
}

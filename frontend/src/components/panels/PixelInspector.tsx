import { useEffect, useState } from 'react'
import { fetchJson, gridUrl } from '../../api/client'
import { formatValue } from '../../lib/format'
import { valueAt } from '../../lib/rasterize'
import type { ForecastGrid, Variable } from '../../types/forecast'
import { GlassPanel, PanelTitle } from '../ui/GlassPanel'

interface PixelInspectorProps {
  lat: number
  lon: number
  date: string
  leadTime: number
  variable: Variable
  onClose: () => void
}

interface PixelSample {
  key: string
  gfs: number | null
  ai: number | null
  blended: number | null
  trust: number | null // GFS weight 0-1
  units: string
}

export function PixelInspector({ lat, lon, date, leadTime, variable, onClose }: PixelInspectorProps) {
  const [sample, setSample] = useState<PixelSample | null>(null)
  const currentKey = `${lat},${lon},${date},${leadTime},${variable}`
  const loading = !sample || sample.key !== currentKey

  useEffect(() => {
    let active = true

    Promise.all([
      fetchJson<ForecastGrid>(gridUrl({ date, leadTime, variable, layer: 'gfs' })),
      fetchJson<ForecastGrid>(gridUrl({ date, leadTime, variable, layer: 'ai' })),
      fetchJson<ForecastGrid>(gridUrl({ date, leadTime, variable, layer: 'blended' })),
      fetchJson<ForecastGrid>(gridUrl({ date, leadTime, variable, layer: 'trust' })),
    ])
      .then(([gfsGrid, aiGrid, blendGrid, trustGrid]) => {
        if (!active) return
        setSample({
          key: currentKey,
          gfs: valueAt(gfsGrid, lat, lon),
          ai: valueAt(aiGrid, lat, lon),
          blended: valueAt(blendGrid, lat, lon),
          trust: valueAt(trustGrid, lat, lon),
          units: blendGrid.metadata.units,
        })
      })
      .catch((err) => {
        console.error('Inspector sample error:', err)
      })

    return () => {
      active = false
    }
  }, [lat, lon, date, leadTime, variable, currentKey])

  const gfsWeight = sample?.trust !== null && sample?.trust !== undefined ? Math.round(sample.trust * 100) : 50
  const aiWeight = 100 - gfsWeight

  return (
    <GlassPanel
      as="aside"
      label="XAI Pixel Inspector"
      strong
      className="absolute bottom-20 left-4 z-[950] w-84 p-4 shadow-2xl transition-all sm:bottom-6 sm:left-auto sm:right-104"
    >
      <div className="flex items-start justify-between gap-2 border-b border-white/10 pb-2.5">
        <div>
          <div className="flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-cyan-400 animate-ping" />
            <PanelTitle>XAI Pixel Inspector</PanelTitle>
          </div>
          <p className="mt-0.5 font-mono text-[11px] text-slate-400">
            {lat.toFixed(3)}°N, {lon.toFixed(3)}°E · Cell ~26 km
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close inspector"
          className="rounded-md px-1.5 py-0.5 text-xs text-slate-400 ring-1 ring-white/10 hover:text-white"
        >
          ✕
        </button>
      </div>

      {loading ? (
        <div className="py-6 text-center text-xs text-slate-400 animate-pulse">Decomposing Super-UNet weights...</div>
      ) : !sample || sample.blended === null ? (
        <div className="py-4 text-center text-xs text-slate-400">Coordinates fall outside the Indian forecast grid.</div>
      ) : (
        <div className="mt-3 space-y-3">
          {/* Blended Result */}
          <div className="rounded-xl bg-cyan-400/10 p-2.5 ring-1 ring-cyan-400/30">
            <p className="text-[10px] font-semibold tracking-wider text-cyan-200 uppercase">Super-UNet Blended Output</p>
            <p className="mt-1 font-mono text-xl font-bold text-white">
              {formatValue(sample.blended, 'blended', sample.units)}
            </p>
            {variable === 'rain' && (
              <p className="mt-0.5 text-[11px] text-slate-300">
                {sample.blended >= 204.5
                  ? '🔴 IMD Extremely Heavy Rainfall'
                  : sample.blended >= 115.6
                    ? '🟠 IMD Very Heavy Rainfall'
                    : sample.blended >= 64.5
                      ? '🟡 IMD Heavy Rainfall'
                      : sample.blended >= 15.6
                        ? 'IMD Moderate Rainfall'
                        : sample.blended >= 2.5
                          ? 'IMD Light Rainfall'
                          : 'Dry / Trace Rainfall'}
              </p>
            )}
          </div>

          {/* Model Inputs */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="rounded-lg bg-teal-500/10 p-2 ring-1 ring-teal-500/20">
              <span className="text-[10px] font-semibold text-teal-300 uppercase">NOAA GFS (Physics)</span>
              <p className="mt-1 font-mono text-sm font-semibold text-white">
                {sample.gfs !== null ? formatValue(sample.gfs, 'gfs', sample.units) : '—'}
              </p>
            </div>
            <div className="rounded-lg bg-violet-500/10 p-2 ring-1 ring-violet-500/20">
              <span className="text-[10px] font-semibold text-violet-300 uppercase">AI Model Proxy</span>
              <p className="mt-1 font-mono text-sm font-semibold text-white">
                {sample.ai !== null ? formatValue(sample.ai, 'ai', sample.units) : '—'}
              </p>
            </div>
          </div>

          {/* Dynamic Trust Weights (XAI) */}
          <div className="space-y-1.5 pt-1">
            <div className="flex justify-between text-[11px]">
              <span className="text-teal-300 font-medium">Physics Trust: {gfsWeight}%</span>
              <span className="text-violet-300 font-medium">AI Trust: {aiWeight}%</span>
            </div>
            <div className="flex h-2 overflow-hidden rounded-full bg-white/10">
              <div className="bg-teal-400 transition-all duration-300" style={{ width: `${gfsWeight}%` }} />
              <div className="bg-violet-500 transition-all duration-300" style={{ width: `${aiWeight}%` }} />
            </div>
            <p className="font-mono text-[10px] text-slate-400 text-center">
              Blend = ({sample.trust?.toFixed(2)} × GFS) + ({((1 - (sample.trust ?? 0.5))).toFixed(2)} × AI)
            </p>
          </div>
        </div>
      )}
    </GlassPanel>
  )
}

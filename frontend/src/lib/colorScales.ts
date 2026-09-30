import type { Layer, Variable } from '../types/forecast'

export type RGB = [number, number, number]

export interface Bin {
  min: number
  color: string
  label: string
}

interface Stop {
  at: number
  color: RGB
}

interface ScaleBase {
  /** RGB for a value, or null when it should be fully transparent. */
  rgb: (v: number) => RGB | null
  /** Opacity for a value, before edge feathering (0..1). */
  alpha: (v: number) => number
}

export type Scale =
  | (ScaleBase & { kind: 'stepped'; bins: Bin[] })
  | (ScaleBase & { kind: 'continuous'; stops: Stop[]; minLabel: string; maxLabel: string })

function hexToRgb(hex: string): RGB {
  const n = parseInt(hex.slice(1), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

const css = (rgb: RGB) => `rgb(${rgb.map(Math.round).join(',')})`

// IMD 24 h rainfall categories (mm). Red is reserved for Extremely Heavy.
const RAIN_BINS: Bin[] = [
  { min: 1, color: '#a5f3fc', label: 'Very light' },
  { min: 2.5, color: '#38bdf8', label: 'Light' },
  { min: 15.6, color: '#2563eb', label: 'Moderate' },
  { min: 64.5, color: '#facc15', label: 'Heavy' },
  { min: 115.6, color: '#f97316', label: 'Very heavy' },
  { min: 204.5, color: '#dc2626', label: 'Extremely heavy' },
]

const RAIN_RGB = RAIN_BINS.map((b) => hexToRgb(b.color))

const RAIN: Scale = {
  kind: 'stepped',
  bins: RAIN_BINS,
  rgb: (v) => {
    for (let i = RAIN_BINS.length - 1; i >= 0; i--) if (v >= RAIN_BINS[i].min) return RAIN_RGB[i]
    return null
  },
  // Light rain fades into the basemap; heavy rain is near-opaque
  alpha: (v) => (v < 1 ? 0 : v < 15.6 ? 0.35 + ((v - 1) / 14.6) * 0.3 : v < 64.5 ? 0.7 : 0.88),
}

function continuous(stops: Stop[], minLabel: string, maxLabel: string, opacity: number): Scale {
  const rgb = (v: number): RGB => {
    if (v <= stops[0].at) return stops[0].color
    for (let i = 1; i < stops.length; i++) {
      const a = stops[i - 1]
      const b = stops[i]
      if (v <= b.at) {
        const t = (v - a.at) / (b.at - a.at)
        return [0, 1, 2].map((k) => a.color[k] + t * (b.color[k] - a.color[k])) as RGB
      }
    }
    return stops[stops.length - 1].color
  }
  return { kind: 'continuous', stops, minLabel, maxLabel, rgb, alpha: () => opacity }
}

const TEMP = continuous(
  [
    { at: 10, color: [37, 99, 235] },
    { at: 22, color: [56, 189, 248] },
    { at: 30, color: [250, 204, 21] },
    { at: 36, color: [249, 115, 22] },
    { at: 42, color: [185, 28, 28] },
  ],
  '10 °C',
  '42 °C',
  0.62,
)

const WIND = continuous(
  [
    { at: 0, color: [20, 83, 99] },
    { at: 6, color: [20, 184, 166] },
    { at: 12, color: [129, 140, 248] },
    { at: 20, color: [217, 70, 239] },
  ],
  '0 m/s',
  '20 m/s',
  0.62,
)

// XAI trust map: 0 = trust AI (violet), 1 = trust GFS (teal)
const TRUST = continuous(
  [
    { at: 0, color: [168, 85, 247] },
    { at: 0.5, color: [100, 116, 139] },
    { at: 1, color: [20, 184, 166] },
  ],
  'Trust AI',
  'Trust GFS',
  0.6,
)

export function scaleFor(variable: Variable, layer: Layer): Scale {
  if (layer === 'trust') return TRUST
  return { rain: RAIN, temp: TEMP, wind: WIND }[variable]
}

export function cssGradient(stops: Stop[]): string {
  const lo = stops[0].at
  const hi = stops[stops.length - 1].at
  return `linear-gradient(to right, ${stops.map((s) => `${css(s.color)} ${((s.at - lo) / (hi - lo)) * 100}%`).join(', ')})`
}

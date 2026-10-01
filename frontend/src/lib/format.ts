import type { Layer, ThreatCategory, ThreatLevel, Variable } from '../types/forecast'

export const VARIABLE_LABELS: Record<Variable, string> = {
  rain: 'Rain',
  temp: 'Temp',
  wind: 'Wind',
}

export const LAYER_LABELS: Record<Layer, string> = {
  gfs: 'GFS',
  ai: 'AI',
  blended: 'Blended',
  trust: 'Trust',
}

export const CATEGORY_LABELS: Record<ThreatCategory, string> = {
  heavy: 'Heavy',
  very_heavy: 'Very heavy',
  extremely_heavy: 'Extremely heavy',
  strong_wind: 'Strong wind',
  gale: 'Gale',
  storm: 'Storm-force',
  heat_watch: 'Heat watch',
  heatwave: 'Heatwave',
  severe_heatwave: 'Severe heatwave',
}

/** Styles by severity level, shared by every hazard (yellow / orange / red). */
export const LEVEL_STYLES: Record<ThreatLevel, string> = {
  1: 'bg-yellow-400/15 text-yellow-300 ring-yellow-400/30',
  2: 'bg-orange-500/15 text-orange-300 ring-orange-500/30',
  3: 'bg-red-600/20 text-red-300 ring-red-500/40',
}

export const LEVEL_COLORS: Record<ThreatLevel, string> = {
  1: '#facc15',
  2: '#f97316',
  3: '#dc2626',
}

export function formatValue(v: number, layer: Layer, units: string): string {
  if (layer === 'trust') return `${Math.round(v * 100)}% GFS · ${Math.round((1 - v) * 100)}% AI`
  return `${v.toFixed(1)} ${units}`
}

export function formatDate(iso: string): string {
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  })
}

export function leadTimeLabel(hours: number): string {
  return `Day ${hours / 24} · +${hours} h`
}

/** Indian number style: 4.8 lakh, 3.4 crore. */
export function formatPeople(n: number): string {
  if (n >= 1e7) return `${(n / 1e7).toFixed(1)} crore`
  if (n >= 1e5) return `${(n / 1e5).toFixed(1)} lakh`
  return n.toLocaleString('en-IN')
}

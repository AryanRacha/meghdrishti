import type { ThreatLevel, Variable } from '../types/forecast'

/** Display text per hazard; thresholds mirror backend/app/services/threat_detector.py. */
export interface HazardInfo {
  name: string // "heavy-rain", used in sentences
  rule: string // Threat Matrix subtitle
  empty: string
  valueLabel: string // "Peak rain"
  bulletinTitle: string
  levelRanges: Record<ThreatLevel, string>
  directive: { title: string; text: string }
}

export const HAZARDS: Record<Variable, HazardInfo> = {
  rain: {
    name: 'heavy-rain',
    rule: 'IMD heavy rain ≥ 64.5 mm',
    empty: 'No heavy-rain regions in this forecast.',
    valueLabel: 'Peak rain',
    bulletinTitle: 'Special Impact-Based Severe Rainfall Advisory Bulletin',
    levelRanges: { 3: '≥ 204.5 mm / 24h', 2: '115.6 – 204.4 mm', 1: '64.5 – 115.5 mm' },
    directive: {
      title: 'Vulnerable Terrains',
      text: 'Prohibit civilian movement along landslide-prone mountain routes and riverbanks in hilly catchment areas.',
    },
  },
  wind: {
    name: 'strong-wind',
    rule: 'IMD strong wind ≥ 40 km/h',
    empty: 'No strong-wind regions in this forecast.',
    valueLabel: 'Peak wind',
    bulletinTitle: 'Special Impact-Based Strong Wind Advisory Bulletin',
    levelRanges: { 3: '≥ 89 km/h (storm)', 2: '62 – 88 km/h (gale)', 1: '40 – 61 km/h' },
    directive: {
      title: 'Coast & Infrastructure',
      text: 'Suspend fishing operations, secure hoardings and temporary structures, and pre-position power-line restoration crews.',
    },
  },
  temp: {
    name: 'heat',
    rule: 'Hottest 2% of land (≥ 28 °C) · IMD heatwave ≥ 40 °C',
    empty: 'No unusual heat in this forecast.',
    valueLabel: 'Peak temp',
    bulletinTitle: 'Special Impact-Based Heat Advisory Bulletin',
    levelRanges: { 3: '≥ 45 °C (severe heatwave)', 2: '40 – 44.9 °C (heatwave)', 1: 'Hottest 2% of land today' },
    directive: {
      title: 'Heat Action Plan',
      text: 'Open cooling shelters and drinking-water points, reschedule outdoor work away from 12–4 pm, and alert hospitals for heat-stroke cases.',
    },
  },
}

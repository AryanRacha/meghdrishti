import type { Layer, Threat, Variable } from '../types/forecast'
import { LANGUAGES, alertText, languagesFor, type LangCode } from './alerts'
import { CATEGORY_LABELS, formatPeople } from './format'

export type StoryPanelId = 'intro' | 'problem' | 'architecture' | 'loss' | 'outro'

/** Which sidebars are open: left = controls, right = Threat Matrix. */
export interface Panels {
  left: boolean
  right: boolean
}

export const PANELS_HIDDEN: Panels = { left: false, right: false }
const CONTROLS: Panels = { left: true, right: false }
const THREATS: Panels = { left: false, right: true }

export interface StoryControls {
  dates: string[]
  date: string | null
  threats: Threat[]
  panels: Panels
  setPanels: (p: Panels) => void
  setDate: (d: string) => void
  setVariable: (v: Variable) => void
  setLayer: (l: Layer) => void
  setLeadTime: (h: number) => void
  setCompare: (on: boolean) => void
  setSwipe: (p: number) => void
  selectThreat: (id: string | null) => void
  setLang: (l: LangCode) => void
  setDispatch: (open: boolean) => void
  setBulletin: (open: boolean) => void
  setInspectPoint: (pt: { lat: number; lon: number } | null) => void
  setPlaying: (on: boolean) => void
  resetView: () => void
  speak: (text: string, speechLang: string, fallback?: { text: string; lang: string }) => Promise<void>
  stopSpeech: () => void
}

export interface StoryTools {
  animate: (from: number, to: number, ms: number, set: (v: number) => void) => Promise<void>
  wait: (ms: number) => Promise<void>
}

export interface Step {
  title: string
  text: (c: StoryControls) => string
  durationMs: number // minimum; async steps (speech) may run longer
  panel?: StoryPanelId
  /** Sidebars to show during this step (default: both hidden for a clean map). */
  panels?: Panels
  run?: (c: StoryControls, t: StoryTools) => Promise<void> | void
}

// A monsoon day with threats across several language regions
const TOUR_DATE = '2023-08-27'
const TIMELAPSE_START = '2023-08-20'

const top = (c: StoryControls): Threat | null => c.threats[0] ?? null
/** First two sentences, so the spoken part of the tour stays short (full text stays on screen). */
const headline = (text: string) => text.split(/(?<=[।.])\s+/).slice(0, 2).join(' ')
const regional = (t: Threat | null): LangCode => (t ? languagesFor(t.state)[0] : 'hi')
const pick = (c: StoryControls, d: string) => (c.dates.includes(d) ? d : (c.dates.at(-1) ?? d))

function resetMap(c: StoryControls) {
  c.setPlaying(false)
  c.setDispatch(false)
  c.setBulletin(false)
  c.setInspectPoint(null)
  c.selectThreat(null)
  c.setCompare(false)
  c.setLeadTime(24)
  c.setVariable('rain')
  c.resetView()
}

export const STORY: Step[] = [
  // --- Act 1: Context & Architecture (fast) ---
  {
    title: 'Meghdrishti · मेघदृष्टि',
    text: () => 'Real-time AI-NWP weather blending and disaster decision support. SIH26081.',
    durationMs: 4000,
    panel: 'intro',
    run: (c) => {
      resetMap(c)
      c.setDate(pick(c, TOUR_DATE))
      c.setLayer('blended')
    },
  },
  {
    title: 'The Challenge',
    text: () => 'Physics models (GFS) miss local extremes; AI models smooth them; averaging dilutes both.',
    durationMs: 4500,
    panel: 'problem',
    run: (c) => {
      resetMap(c)
      c.setDate(pick(c, TOUR_DATE))
      c.setLayer('blended')
    },
  },
  {
    title: 'Super-UNet + Extreme Loss',
    text: () => 'Our PyTorch U-Net blends them using an extreme-weighted loss function that explicitly preserves cloudbursts.',
    durationMs: 6000,
    panel: 'loss',
    run: (c) => {
      resetMap(c)
      c.setDate(pick(c, TOUR_DATE))
      c.setLayer('blended')
    },
  },

  // --- Act 2: Live Data Ingestion ---
  {
    title: 'Input 1 · NOAA GFS (Live)',
    text: () => 'Real-time physics model at 0.25°, fetched via S3 byte-range perfectly cropped to India.',
    durationMs: 4000,
    run: (c) => {
      c.setCompare(false)
      c.setVariable('rain')
      c.setLayer('gfs')
    },
  },
  {
    title: 'Input 2 · ECMWF AIFS (Live)',
    text: () => 'Real-time operational AI weather model (GraphCast equivalent) fetched via Azure Open Data.',
    durationMs: 4500,
    run: (c) => {
      c.setCompare(false)
      c.setVariable('rain')
      c.setLayer('ai')
    },
  },
  {
    title: 'Output · Super-UNet Blend',
    text: () => 'Every ~26 km grid cell gets its own learned GFS/AI mix, computed in real-time.',
    durationMs: 4000,
    run: (c) => {
      c.setCompare(false)
      c.setVariable('rain')
      c.setLayer('blended')
    },
  },
  {
    title: 'Explainable AI · Trust Map',
    text: () => 'Teal: the network trusts physics (GFS). Violet: it trusts AI. Forecasters see exactly why it predicts what it does.',
    durationMs: 5500,
    run: (c) => {
      c.setCompare(false)
      c.setVariable('rain')
      c.setLayer('trust')
    },
  },
  {
    title: 'XAI · Pixel Inspector',
    text: () => 'Inspect any cell to see the mathematical blending equation and per-model spatial trust weights.',
    durationMs: 5000,
    run: (c) => {
      c.setCompare(false)
      c.setLayer('trust')
      c.setVariable('rain')
      c.setInspectPoint({ lat: 31.7, lon: 77.0 })
    },
  },

  // --- Act 3: Threat Matrix & Dispatch ---
  {
    title: 'Threat Matrix',
    text: (c) => `${c.threats.length} IMD heavy-rain regions auto-detected and ranked by severity in real-time.`,
    durationMs: 4500,
    panels: THREATS,
    run: (c) => {
      c.setPlaying(false)
      c.setVariable('rain')
      c.setLeadTime(24)
      c.setDate(pick(c, TOUR_DATE))
      c.selectThreat(null)
      c.setInspectPoint(null)
      c.setLayer('blended')
    },
  },
  {
    title: 'Impact-Based Early Warning',
    text: (c) => {
      const t = top(c)
      return t ? `${formatPeople(t.population_exposed)} people exposed in ${t.district}. Risk index: ${t.risk_index}/100.` : ''
    },
    durationMs: 4000,
    panels: THREATS,
    run: (c) => {
      c.selectThreat(top(c)?.id ?? null)
    },
  },
  {
    title: 'Regional Last-Mile Voice Alert',
    text: (c) => `Auto-generated public warning translated to ${LANGUAGES[regional(top(c))].label}, read aloud.`,
    durationMs: 6500,
    run: async (c) => {
      c.selectThreat(top(c)?.id ?? null)
      const t = top(c)
      if (!t || !c.date) return
      const lang = regional(t)
      c.setLang(lang)
      const english = { text: headline(alertText(t, c.date, 'en')), lang: LANGUAGES.en.speech }
      await c.speak(headline(alertText(t, c.date, lang)), LANGUAGES[lang].speech, english)
    },
  },
  {
    title: 'Official IMD Civil Bulletin',
    text: () => 'One-click official impact-based disaster advisory with NDMA protocols and print-ready PDF export.',
    durationMs: 5000,
    run: (c) => {
      c.setDispatch(false)
      c.setBulletin(true)
    },
  },
  // --- Close ---
  {
    title: 'Meghdrishti · मेघदृष्टि',
    text: () => 'Seeing into the clouds, from forecast to last-mile action.',
    durationMs: 4500,
    panel: 'outro',
    run: (c) => {
      c.setBulletin(false)
      c.setDispatch(false)
      c.selectThreat(null)
      c.setLayer('blended')
      c.resetView()
    },
  },
]

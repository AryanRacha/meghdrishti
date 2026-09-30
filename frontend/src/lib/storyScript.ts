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
  setPlaying: (on: boolean) => void
  resetView: () => void
  speak: (text: string, speechLang: string) => Promise<void>
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
  c.selectThreat(null)
  c.setCompare(false)
  c.setLeadTime(24)
  c.setVariable('rain')
  c.resetView()
}

export const STORY: Step[] = [
  // --- Act 1: context -------------------------------------------------------
  {
    title: 'Meghdrishti · मेघदृष्टि',
    text: () => 'Hybrid AI-NWP forecast blending for extreme rainfall. SIH26081 · Ministry of Earth Sciences',
    durationMs: 6000,
    panel: 'intro',
    run: (c) => {
      resetMap(c)
      c.setDate(pick(c, TOUR_DATE))
      c.setLayer('blended')
    },
  },
  {
    title: 'The problem',
    text: () => 'Physics models miss local extremes; AI models smooth them; plain averaging dilutes both.',
    durationMs: 8000,
    panel: 'problem',
  },
  {
    title: 'Super-UNet architecture',
    text: () => '7 input channels → residual U-Net with FiLM lead-time conditioning → 3 per-pixel trust heads.',
    durationMs: 9500,
    panel: 'architecture',
  },
  {
    title: 'Extreme-weighted loss',
    text: () => 'Missing a cloudburst costs exponentially more than missing a drizzle.',
    durationMs: 7000,
    panel: 'loss',
  },

  // --- Act 2: the forecast ---------------------------------------------------
  {
    title: 'Input 1 · NOAA GFS',
    text: () => 'Physics-based global model at 0.25°, cropped to India (8–38°N, 68–98°E).',
    durationMs: 4500,
    run: (c) => c.setLayer('gfs'),
  },
  {
    title: 'Input 2 · AI forecast',
    text: () => 'Data-driven AI model for the same day: fast, but tends to smooth extremes.',
    durationMs: 4500,
    run: (c) => c.setLayer('ai'),
  },
  {
    title: 'Output · Super-UNet blend',
    text: () => 'Every ~26 km cell gets its own GFS/AI mix, learned from ERA5 ground truth.',
    durationMs: 4500,
    run: (c) => c.setLayer('blended'),
  },
  {
    title: 'Side by side',
    text: () => 'Raw GFS on the left, the Super-UNet blend on the right.',
    durationMs: 8500,
    run: async (c, t) => {
      c.setSwipe(0.85)
      c.setCompare(true)
      await t.animate(0.85, 0.22, 3500, c.setSwipe)
      await t.animate(0.22, 0.55, 2200, c.setSwipe)
    },
  },
  {
    title: 'Explainable AI · Trust Map',
    text: () => 'Teal: the model trusts physics (GFS). Violet: it trusts AI. Forecasters see why.',
    durationMs: 6000,
    run: (c) => {
      c.setCompare(false)
      c.setLayer('trust')
    },
  },
  {
    title: 'Rain, temperature & wind',
    text: () => 'Each variable has its own trust head and its own blended field.',
    durationMs: 7500,
    run: async (c, t) => {
      c.setVariable('temp')
      await t.wait(2500)
      c.setLayer('blended')
      await t.wait(2500)
      c.setVariable('wind')
    },
  },
  {
    title: 'Lead time · FiLM conditioning',
    text: () => 'The blending strategy adapts to how far ahead we forecast: Day 1 to Day 5.',
    durationMs: 6500,
    panels: CONTROLS,
    run: async (c, t) => {
      c.setVariable('rain')
      for (const h of [48, 72, 96, 120]) {
        await t.wait(1300)
        c.setLeadTime(h)
      }
    },
  },
  {
    title: 'Monsoon time-lapse',
    text: () => 'Day-by-day evolution of the blended rainfall forecast.',
    durationMs: 9000,
    panels: CONTROLS,
    run: async (c, t) => {
      c.setLeadTime(24)
      c.setDate(pick(c, TIMELAPSE_START))
      await t.wait(800)
      c.setPlaying(true)
      await t.wait(7500)
      c.setPlaying(false)
      c.setDate(pick(c, TOUR_DATE))
    },
  },

  // --- Act 3: impact and action ----------------------------------------------
  {
    title: 'Threat Matrix',
    text: (c) => `${c.threats.length} IMD heavy-rain regions (≥ 64.5 mm) auto-detected and ranked by severity.`,
    durationMs: 5000,
    panels: THREATS,
  },
  {
    title: 'Threat #1',
    text: (c) => {
      const t = top(c)
      return t
        ? `${t.district}, ${t.state}: ${Math.round(t.peak_mm)} mm in 24 h · IMD ${CATEGORY_LABELS[t.category]}`
        : 'No heavy-rain regions in this forecast.'
    },
    durationMs: 5000,
    panels: THREATS,
    run: (c) => c.selectThreat(top(c)?.id ?? null),
  },
  {
    title: 'Impact-based forecasting',
    text: (c) => {
      const t = top(c)
      return t ? `${formatPeople(t.population_exposed)} people in the affected area · Risk index ${t.risk_index}/100` : ''
    },
    durationMs: 5000,
    panels: THREATS,
  },
  {
    title: 'Last-mile warning',
    text: (c) => `Auto-generated public warning in ${LANGUAGES[regional(top(c))].label}, read aloud.`,
    durationMs: 7000,
    run: async (c) => {
      const t = top(c)
      if (!t || !c.date) return
      const lang = regional(t)
      c.setLang(lang)
      await c.speak(headline(alertText(t, c.date, lang)), LANGUAGES[lang].speech)
    },
  },
  {
    title: '12 Indian languages',
    text: () => 'Hindi, English and the state language: Marathi, Bengali, Tamil, Telugu, Kannada, Malayalam and more.',
    durationMs: 5000,
    run: async (c, t) => {
      c.setLang('hi')
      await t.wait(2500)
      c.setLang('en')
    },
  },
  {
    title: 'Dispatch',
    text: () => 'One click to Cell Broadcast, SMS, WhatsApp and the District Control Room.',
    durationMs: 6500,
    run: (c) => c.setDispatch(true),
  },
  // --- Close -------------------------------------------------------------------
  {
    title: 'Meghdrishti · मेघदृष्टि',
    text: () => 'Seeing into the clouds, from forecast to last-mile action.',
    durationMs: 7000,
    panel: 'outro',
    run: (c) => {
      c.setDispatch(false)
      c.selectThreat(null)
      c.setLayer('blended')
      c.resetView()
    },
  },
]

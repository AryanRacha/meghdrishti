import type { ReactNode } from 'react'
import type { StoryPanelId } from '../../lib/storyScript'
import { GlassPanel } from '../ui/GlassPanel'

function Brand() {
  return (
    <div className="text-center">
      <p className="bg-gradient-to-r from-cyan-300 to-teal-300 bg-clip-text text-5xl font-bold tracking-tight text-transparent">
        Meghdrishti
      </p>
      <p lang="hi" className="mt-1 text-2xl text-slate-200">
        मेघदृष्टि
      </p>
    </div>
  )
}

function Chips({ items }: { items: string[] }) {
  return (
    <div className="mt-6 flex flex-wrap justify-center gap-2">
      {items.map((item) => (
        <span key={item} className="rounded-full bg-white/5 px-3 py-1 text-xs text-slate-200 ring-1 ring-white/15">
          {item}
        </span>
      ))}
    </div>
  )
}

function Box({ title, children, accent = false }: { title: string; children: ReactNode; accent?: boolean }) {
  return (
    <div className={`flex-1 rounded-xl p-3 ring-1 ${accent ? 'bg-cyan-400/10 ring-cyan-400/40' : 'bg-white/[0.04] ring-white/10'}`}>
      <p className={`text-[11px] font-semibold tracking-wider uppercase ${accent ? 'text-cyan-200' : 'text-slate-400'}`}>{title}</p>
      <div className="mt-1.5 space-y-0.5 text-xs leading-relaxed text-slate-200">{children}</div>
    </div>
  )
}

const Arrow = () => (
  <span aria-hidden className="self-center text-lg text-cyan-300">
    →
  </span>
)

// Penalty weight from ml_pipeline/train.py CompositeLoss: 1 + 0.5·exp(2·(y − 8)/8) above 8 mm
const PENALTIES: [string, string][] = [
  ['5 mm', '×1.0'],
  ['10 mm', '×1.8'],
  ['15 mm', '×3.9'],
  ['20 mm', '×11'],
]

const CONTENT: Record<StoryPanelId, ReactNode> = {
    intro: (
    <>
      <Brand />
      <p className="mt-4 text-center text-base font-medium text-slate-200">AI-NWP Weather Forecast Blending for India</p>
      <Chips items={['Physics + AI super-ensemble', 'Explainable Trust Maps', 'IMD-graded threats', 'Last-mile multilingual alerts']} />
      <p className="mt-6 text-center text-xs tracking-widest text-slate-500 uppercase">SIH26081 · Ministry of Earth Sciences</p>
    </>
  ),
  problem: (
    <>
      <p className="text-center text-xl font-semibold text-white">Why a single forecast isn’t enough</p>
      <div className="mt-5 flex gap-3">
        <Box title="Physics · GFS">Resolves dynamics, but coarse over the Himalaya and Western Ghats.</Box>
        <Box title="AI models">Fast and skilful on average, but smooth out extremes.</Box>
        <Box title="Plain average">Dilutes a cloudburst that only one model sees.</Box>
      </div>
      <div className="mt-3">
        <Box title="Meghdrishti" accent>
          Learns, pixel by pixel, which model to trust, and is trained to never wash out extreme rainfall.
        </Box>
      </div>
    </>
  ),
  architecture: (
    <>
      <p className="text-center text-xl font-semibold text-white">Super-UNet Blender</p>
      <div className="mt-5 flex items-stretch gap-2">
        <Box title="7 inputs">
          <p>GFS rain · temp · wind</p>
          <p>AI rain · temp · wind</p>
          <p>Topography (DEM)</p>
        </Box>
        <Arrow />
        <Box title="Super-UNet" accent>
          <p>4 residual encoder stages</p>
          <p>FiLM ← lead time</p>
          <p>Attention-gated decoder</p>
        </Box>
        <Arrow />
        <Box title="3 trust heads">
          <p>Rain weights</p>
          <p>Temp weights</p>
          <p>Wind weights</p>
        </Box>
        <Arrow />
        <Box title="Blend">
          <p className="font-mono">w·GFS + (1−w)·AI</p>
          <p>per 26 km cell</p>
        </Box>
      </div>
      <Chips items={['8.2 M parameters', '128 × 128 grid over India', '500 epochs · RTX 4090', '~0.3 s inference']} />
    </>
  ),
  loss: (
    <>
      <p className="text-center text-xl font-semibold text-white">Extreme-weighted loss</p>
      <p className="mt-4 text-center font-mono text-sm text-cyan-100">
        L<sub>rain</sub> = mean[ w(y) · (ŷ − y)² ], w(y) = 1 + α·e<sup>β(y−T)/T</sup> for y &gt; T
      </p>
      <div className="mx-auto mt-5 grid max-w-md grid-cols-4 gap-2">
        {PENALTIES.map(([rain, weight]) => (
          <div key={rain} className="rounded-xl bg-white/[0.04] p-3 text-center ring-1 ring-white/10">
            <p className="text-xs text-slate-400">{rain}</p>
            <p className="mt-1 font-mono text-lg font-semibold text-white">{weight}</p>
          </div>
        ))}
      </div>
      <p className="mt-4 text-center text-sm text-slate-300">
        Penalty grows exponentially with intensity, plus scale-balanced temperature and wind terms.
      </p>
    </>
  ),
  outro: (
    <>
      <Brand />
      <p className="mt-4 text-center text-base text-slate-300">Seeing into the clouds, from forecast to last-mile action.</p>
      <Chips items={['Super-UNet blending', 'Explainable AI', 'Impact-based risk', '12 languages + voice', 'Open GeoJSON API']} />
      <p className="mt-6 text-center text-xs tracking-widest text-slate-500 uppercase">SIH26081 · Ministry of Earth Sciences</p>
    </>
  ),
}

export function StoryPanel({ panel }: { panel: StoryPanelId }) {
  return (
    <div className="absolute inset-0 grid place-items-center bg-slate-950/55 p-4 backdrop-blur-[2px]">
      <div key={panel} className="appear w-[min(46rem,100%)]">
        <GlassPanel as="section" label="Guided tour" strong className="p-7">
          {CONTENT[panel]}
        </GlassPanel>
      </div>
    </div>
  )
}

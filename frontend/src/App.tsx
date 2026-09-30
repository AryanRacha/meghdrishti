import { useCallback, useEffect, useMemo, useState } from 'react'
import { alertsUrl, gridUrl, metaUrl, prefetch } from './api/client'
import { ForecastMap } from './components/map/ForecastMap'
import { MapController } from './components/map/MapController'
import { RainAnimation } from './components/map/RainAnimation'
import { RasterLayer } from './components/map/RasterLayer'
import { SwipeCompare } from './components/map/SwipeCompare'
import { SwipeDivider } from './components/map/SwipeDivider'
import { ThreatMarkers } from './components/map/ThreatMarkers'
import { AlertCard } from './components/panels/AlertCard'
import { ControlDock } from './components/panels/ControlDock'
import { DispatchPreview } from './components/panels/DispatchPreview'
import { Header } from './components/panels/Header'
import { Legend } from './components/panels/Legend'
import { StoryBar } from './components/panels/StoryBar'
import { StoryPanel } from './components/panels/StoryPanel'
import { ThreatMatrix } from './components/panels/ThreatMatrix'
import { EdgeToggle } from './components/ui/EdgeToggle'
import { GlassPanel } from './components/ui/GlassPanel'
import { useApi } from './hooks/useApi'
import { useSpeech } from './hooks/useSpeech'
import { useStoryMode } from './hooks/useStoryMode'
import { LANGUAGES, alertText, languagesFor, type LangCode } from './lib/alerts'
import { scaleFor } from './lib/colorScales'
import { CircleMarker } from 'react-leaflet'
import { BulletinModal } from './components/panels/BulletinModal'
import { PixelInspector } from './components/panels/PixelInspector'
import type { Panels } from './lib/storyScript'
import type { AlertsResponse, ForecastGrid, Layer, MetaResponse, Variable } from './types/forecast'

const PLAYBACK_FRAME_MS = 1400

// Slide panels off-screen; visibility is transitioned too so hidden panels can't be clicked
const SLIDE = 'transition-[transform,opacity,visibility] duration-500 ease-out'
const slide = (open: boolean, side: 'left' | 'right') =>
  open ? 'translate-x-0 opacity-100 visible' : `${side === 'left' ? '-translate-x-[110%]' : 'translate-x-[110%]'} opacity-0 invisible`

function App() {
  const meta = useApi<MetaResponse>(metaUrl())

  const [pickedDate, setPickedDate] = useState<string | null>(null)
  const [leadTime, setLeadTime] = useState(24)
  const [variable, setVariable] = useState<Variable>('rain')
  const [layer, setLayer] = useState<Layer>('blended')
  const [compare, setCompare] = useState(false)
  const [swipe, setSwipe] = useState(0.5)
  const [playing, setPlaying] = useState(false)
  const [selectedThreat, setSelectedThreat] = useState<string | null>(null)
  const [lang, setLang] = useState<LangCode | null>(null)
  const [dispatchOpen, setDispatchOpen] = useState(false)
  const [bulletinOpen, setBulletinOpen] = useState(
    () => typeof window !== 'undefined' && new URLSearchParams(window.location.search).has('bulletin'),
  )
  const [inspectPoint, setInspectPoint] = useState<{ lat: number; lon: number } | null>(null)
  const [resetKey, setResetKey] = useState(0)
  const [panels, setPanels] = useState<Panels>({ left: true, right: true })

  const dates = useMemo(() => meta.data?.dates ?? [], [meta.data])
  const date = pickedDate ?? dates.at(-1) ?? null
  const query = (l: Layer) => (date ? gridUrl({ date, leadTime, variable, layer: l }) : null)

  const single = useApi<ForecastGrid>(compare ? null : query(layer))
  const left = useApi<ForecastGrid>(compare ? query('gfs') : null)
  const right = useApi<ForecastGrid>(compare ? query('blended') : null)
  const alerts = useApi<AlertsResponse>(date ? alertsUrl({ date, leadTime }) : null)

  // Colour by what the data *is*, not what is selected, so stale data is never mis-coloured mid-fetch
  const shown = compare ? right.data : single.data
  const layerMeta = shown?.metadata
  const scale = useMemo(() => (layerMeta ? scaleFor(layerMeta.variable, layerMeta.layer) : null), [layerMeta])

  const threats = alerts.data?.threats ?? []
  const threat = threats.find((t) => t.id === selectedThreat) ?? null
  const activeLang = threat ? (lang && languagesFor(threat.state).includes(lang) ? lang : languagesFor(threat.state)[0]) : null
  const loading = (compare ? left.loading || right.loading : single.loading) || alerts.loading
  const error = meta.error ?? single.error ?? left.error ?? right.error ?? alerts.error

  const speech = useSpeech()

  const selectThreat = useCallback((id: string | null) => {
    setSelectedThreat(id)
    setLang(null)
  }, [])

  // Time-lapse: advance one day once the current frame is on screen, prefetching the next
  useEffect(() => {
    if (!playing || !date || loading || dates.length === 0) return
    const next = dates[(dates.indexOf(date) + 1) % dates.length]
    const nextLayers: Layer[] = compare ? ['gfs', 'blended'] : [layer]
    nextLayers.forEach((l) => prefetch(gridUrl({ date: next, leadTime, variable, layer: l })))
    prefetch(alertsUrl({ date: next, leadTime }))
    const timer = setTimeout(() => setPickedDate(next), PLAYBACK_FRAME_MS)
    return () => clearTimeout(timer)
  }, [playing, date, loading, dates, compare, layer, leadTime, variable])

  // Keyboard: [ toggles controls, ] toggles Threat Matrix
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) return
      if (e.key === '[') setPanels((p) => ({ ...p, left: !p.left }))
      if (e.key === ']') setPanels((p) => ({ ...p, right: !p.right }))
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const story = useStoryMode({
    dates,
    date,
    threats,
    panels,
    setPanels,
    setDate: setPickedDate,
    setVariable,
    setLayer,
    setLeadTime,
    setCompare,
    setSwipe,
    selectThreat,
    setLang,
    setDispatch: setDispatchOpen,
    setPlaying,
    resetView: () => setResetKey((k) => k + 1),
    speak: speech.speak,
    stopSpeech: speech.stop,
  })

  return (
    <main className={`relative h-full w-full overflow-hidden ${panels.right ? 'right-open' : ''} print:h-auto print:overflow-visible`}>
      <ForecastMap onMapClick={(lat, lon) => setInspectPoint({ lat, lon })}>
        {compare && left.data && right.data && scale ? (
          <SwipeCompare left={left.data} right={right.data} scale={scale} position={swipe} />
        ) : (
          !compare && single.data && scale && <RasterLayer grid={single.data} scale={scale} />
        )}
        {!compare && single.data?.metadata.variable === 'rain' && single.data.metadata.layer !== 'trust' && (
          <RainAnimation grid={single.data} />
        )}
        <ThreatMarkers threats={threats} selectedId={selectedThreat} onSelect={selectThreat} />
        {inspectPoint && (
          <CircleMarker
            center={[inspectPoint.lat, inspectPoint.lon]}
            radius={7}
            pathOptions={{ color: '#22d3ee', fillColor: '#06b6d4', fillOpacity: 0.9, weight: 2.5 }}
          />
        )}
        <MapController resetKey={resetKey} />
      </ForecastMap>

      {compare && (
        <div className="print:hidden">
          <SwipeDivider position={swipe} onChange={setSwipe} leftLabel="Raw GFS" rightLabel="Super-UNet blend" />
        </div>
      )}

      {/* Floating UI layer (above Leaflet panes/controls) */}
      <div className="pointer-events-none absolute inset-0 z-[1100] print:static print:inset-auto print:h-auto print:w-full print:overflow-visible">
        <div className="absolute top-4 left-4 flex w-[calc(100%-2rem)] flex-col gap-3 sm:w-80 print:hidden">
          <Header
            run={alerts.data?.metadata ?? null}
            loading={loading}
            error={error}
            onOpenBulletin={() => setBulletinOpen(true)}
          />
          {meta.data && date && (
            <div className={`${SLIDE} ${slide(panels.left, 'left')}`}>
              <ControlDock
                dates={dates}
                date={date}
                onDate={setPickedDate}
                leadTimes={meta.data.lead_times}
                trainedLeadTimes={meta.data.trained_lead_times}
                leadTime={leadTime}
                onLeadTime={setLeadTime}
                variable={variable}
                onVariable={setVariable}
                layer={layer}
                onLayer={setLayer}
                compare={compare}
                onCompare={setCompare}
                playing={playing}
                onPlaying={setPlaying}
                onTour={story.start}
              />
            </div>
          )}
        </div>

        {story.caption?.panel && (
          <div className="print:hidden">
            <StoryPanel panel={story.caption.panel} />
          </div>
        )}

        {story.caption && (
          <div className="absolute top-4 left-1/2 w-[min(36rem,calc(100%-2rem))] -translate-x-1/2 print:hidden">
            <StoryBar caption={story.caption} onNext={story.next} onStop={story.stop} />
          </div>
        )}

        {layerMeta && scale && (
          <div className="absolute bottom-4 left-4 hidden sm:block print:hidden">
            <Legend metadata={layerMeta} scale={scale} />
          </div>
        )}

        {threat && date && activeLang && (
          <div
            className={`absolute inset-x-4 bottom-20 transition-[left,right] duration-500 lg:bottom-4 ${panels.left ? 'lg:left-[22rem]' : 'lg:left-72'} ${panels.right ? 'lg:right-[26rem]' : 'lg:right-4'} print:hidden`}
          >
            <div className="appear mx-auto max-w-xl">
              <AlertCard
                threat={threat}
                date={date}
                lang={activeLang}
                onLang={setLang}
                speaking={speech.speaking}
                canSpeak={speech.canSpeak}
                onSpeak={(text, speechLang) => void speech.speak(text, speechLang)}
                onStop={speech.stop}
                onDispatch={() => setDispatchOpen(true)}
                onClose={() => selectThreat(null)}
              />
            </div>
          </div>
        )}

        <div
          className={`absolute inset-x-0 bottom-0 lg:inset-x-auto lg:top-4 lg:right-4 lg:bottom-4 lg:w-96 ${SLIDE} ${slide(panels.right, 'right')} print:hidden`}
        >
          <ThreatMatrix
            threats={threats}
            loading={alerts.loading}
            selectedId={selectedThreat}
            onSelect={selectThreat}
            onOpenBulletin={() => setBulletinOpen(true)}
          />
        </div>

        <div className="print:hidden">
          <EdgeToggle
            side="left"
            open={panels.left}
            onToggle={() => setPanels((p) => ({ ...p, left: !p.left }))}
            label="controls"
            shortcut="["
          />
          <EdgeToggle
            side="right"
            open={panels.right}
            onToggle={() => setPanels((p) => ({ ...p, right: !p.right }))}
            label="Threat Matrix"
            shortcut="]"
          />
        </div>

        {inspectPoint && date && (
          <div className="pointer-events-auto print:hidden">
            <PixelInspector
              lat={inspectPoint.lat}
              lon={inspectPoint.lon}
              date={date}
              leadTime={leadTime}
              variable={variable}
              onClose={() => setInspectPoint(null)}
            />
          </div>
        )}

        {bulletinOpen && date && (
          <div className="pointer-events-auto print:static print:w-full">
            <BulletinModal
              date={date}
              leadTime={leadTime}
              threats={threats}
              onClose={() => setBulletinOpen(false)}
            />
          </div>
        )}

        {dispatchOpen && threat && date && activeLang && (
          <div className="print:hidden">
            <DispatchPreview
              threat={threat}
              text={alertText(threat, date, activeLang)}
              speechLang={LANGUAGES[activeLang].speech}
              onClose={() => setDispatchOpen(false)}
            />
          </div>
        )}

        {error && !meta.data && (
          <div className="absolute inset-0 grid place-items-center p-4 print:hidden">
            <GlassPanel className="max-w-sm p-5 text-center">
              <p className="font-semibold text-white">Backend unreachable</p>
              <p className="mt-1 text-sm text-slate-400">
                Start the API: <code className="font-mono text-cyan-200">uvicorn app.main:app --port 8000</code> inside{' '}
                <code className="font-mono">backend/</code>.
              </p>
              <p className="mt-3 font-mono text-xs break-words text-red-300">{error}</p>
            </GlassPanel>
          </div>
        )}
      </div>
    </main>
  )
}

export default App

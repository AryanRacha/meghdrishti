import { useCallback, useEffect, useRef, useState } from 'react'
import { PANELS_HIDDEN, STORY, type Panels, type StoryControls, type StoryPanelId, type StoryTools } from '../lib/storyScript'

export interface StoryCaption {
  index: number
  total: number
  title: string
  text: string
  durationMs: number
  panel?: StoryPanelId
}

class Cancelled extends Error {}

export function useStoryMode(controls: StoryControls) {
  const controlsRef = useRef(controls)
  const runId = useRef(0)
  const savedPanels = useRef<Panels | null>(null)
  const [caption, setCaption] = useState<StoryCaption | null>(null)

  useEffect(() => {
    controlsRef.current = controls
  })

  const restorePanels = useCallback(() => {
    if (savedPanels.current) controlsRef.current.setPanels(savedPanels.current)
    savedPanels.current = null
  }, [])

  const stop = useCallback(() => {
    runId.current += 1
    controlsRef.current.stopSpeech()
    controlsRef.current.setPlaying(false)
    restorePanels()
    setCaption(null)
  }, [restorePanels])

  const start = useCallback(async () => {
    const id = ++runId.current
    savedPanels.current ??= controlsRef.current.panels
    const guard = () => {
      if (runId.current !== id) throw new Cancelled()
    }
    const wait = (ms: number) => new Promise<void>((r) => setTimeout(r, ms)).then(guard)
    const animate: StoryTools['animate'] = (from, to, ms, set) =>
      new Promise((resolve) => {
        const t0 = performance.now()
        const tick = (now: number) => {
          if (runId.current !== id) return resolve()
          const k = Math.min(1, (now - t0) / ms)
          const eased = k < 0.5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2
          set(from + (to - from) * eased)
          if (k < 1) requestAnimationFrame(tick)
          else resolve()
        }
        requestAnimationFrame(tick)
      })

    try {
      for (let i = 0; i < STORY.length; i++) {
        const step = STORY[i]
        // Let state from the previous step (date, selection, fetched threats) propagate before reading it
        await wait(80)
        const c = controlsRef.current
        c.setPanels(step.panels ?? PANELS_HIDDEN)
        setCaption({ index: i, total: STORY.length, title: step.title, text: step.text(c), durationMs: step.durationMs, panel: step.panel })
        await Promise.all([step.run?.(c, { animate, wait }), wait(step.durationMs)])
        guard()
      }
      restorePanels()
      setCaption(null)
    } catch (err) {
      if (!(err instanceof Cancelled)) throw err
    }
  }, [restorePanels])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && stop()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [stop])

  return { caption, start, stop, active: caption !== null }
}

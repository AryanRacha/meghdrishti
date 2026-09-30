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
  const stepIdRef = useRef(0)
  const nextResolver = useRef<(() => void) | null>(null)
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
    if (nextResolver.current) {
      nextResolver.current()
      nextResolver.current = null
    }
    controlsRef.current.stopSpeech()
    controlsRef.current.setPlaying(false)
    controlsRef.current.setCompare(false)
    controlsRef.current.setDispatch(false)
    controlsRef.current.selectThreat(null)
    restorePanels()
    setCaption(null)
  }, [restorePanels])

  const next = useCallback(() => {
    if (nextResolver.current) {
      const resolve = nextResolver.current
      nextResolver.current = null
      resolve()
    }
  }, [])

  const start = useCallback(async () => {
    const id = ++runId.current
    savedPanels.current ??= controlsRef.current.panels
    const guard = () => {
      if (runId.current !== id) throw new Cancelled()
    }
    const wait = (ms: number) => new Promise<void>((r) => setTimeout(r, ms)).then(guard)

    try {
      for (let i = 0; i < STORY.length; i++) {
        const step = STORY[i]
        const stepId = ++stepIdRef.current
        const stepGuard = () => {
          guard()
          if (stepIdRef.current !== stepId) throw new Cancelled()
        }
        const stepWait = (ms: number) => new Promise<void>((r) => setTimeout(r, ms)).then(stepGuard)
        const stepAnimate: StoryTools['animate'] = (from, to, ms, set) =>
          new Promise((resolve) => {
            const t0 = performance.now()
            const tick = (now: number) => {
              if (runId.current !== id || stepIdRef.current !== stepId) return resolve()
              const k = Math.min(1, (now - t0) / ms)
              const eased = k < 0.5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2
              set(from + (to - from) * eased)
              if (k < 1) requestAnimationFrame(tick)
              else resolve()
            }
            requestAnimationFrame(tick)
          })

        // Stop in-flight speech before moving to the next step
        controlsRef.current.stopSpeech()

        // Let state from the previous step (date, selection, fetched threats) propagate before reading it
        await wait(80)
        guard()

        const c = controlsRef.current
        c.setPanels(step.panels ?? PANELS_HIDDEN)
        setCaption({ index: i, total: STORY.length, title: step.title, text: step.text(c), durationMs: step.durationMs, panel: step.panel })

        // Trigger step's visual action/animations
        if (step.run) {
          step.run(c, { animate: stepAnimate, wait: stepWait })
        }

        // Wait for Enter key to advance to the next step
        await new Promise<void>((resolve) => {
          nextResolver.current = resolve
        }).then(guard)
      }
      restorePanels()
      setCaption(null)
    } catch (err) {
      if (!(err instanceof Cancelled)) throw err
    }
  }, [restorePanels])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (caption === null) return
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) return

      if (e.key === 'Escape') {
        e.preventDefault()
        stop()
      } else if (e.key === 'Enter') {
        e.preventDefault()
        next()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [caption, stop, next])

  return { caption, start, stop, next, active: caption !== null }
}

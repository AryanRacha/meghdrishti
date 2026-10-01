import { useCallback, useEffect, useRef, useState } from 'react'
import { fetchSpeech } from '../api/client'

const synth: SpeechSynthesis | undefined = typeof window !== 'undefined' ? window.speechSynthesis : undefined

/** Languages the backend can voice (see backend/app/services/tts_engine.py). */
const SERVER_LANGS = new Set(['en', 'hi', 'mr', 'bn', 'as', 'ta', 'te', 'kn', 'ml', 'gu', 'pa', 'or'])

/** Same-script siblings a browser voice can read reasonably when the exact language is missing. */
const SCRIPT_SIBLINGS: Record<string, string> = { mr: 'hi', as: 'bn' }

export interface SpeechFallback {
  text: string
  lang: string
}

const baseLang = (lang: string) => lang.split('-')[0]

/** Prefer natural/online (neural) voices, e.g. Edge's "Microsoft Swara Online (Natural)". */
function matchVoice(voices: SpeechSynthesisVoice[], lang: string): SpeechSynthesisVoice | undefined {
  const base = baseLang(lang)
  const matches = voices.filter((v) => {
    const vLang = v.lang.replace('_', '-')
    return vLang === lang || vLang === base || vLang.startsWith(`${base}-`)
  })
  return matches.find((v) => /natural|online|neural/i.test(v.name)) ?? matches[0]
}

function pickVoice(voices: SpeechSynthesisVoice[], lang: string): SpeechSynthesisVoice | undefined {
  const sibling = SCRIPT_SIBLINGS[baseLang(lang)]
  return matchVoice(voices, lang) ?? (sibling ? matchVoice(voices, sibling) : undefined)
}

/** Chrome silently stops utterances after ~15 s, so speak sentence by sentence. */
function chunk(text: string): string[] {
  return text.match(/[^.!?।]+[.!?।]*/g)?.map((s) => s.trim()).filter(Boolean) ?? [text]
}

interface Playback {
  abort: AbortController
  resolve: () => void
  audio?: HTMLAudioElement
  url?: string
  // Chrome garbage-collects queued utterances, which drops their onend events
  utterances: SpeechSynthesisUtterance[]
}

export function useSpeech() {
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>(() => synth?.getVoices() ?? [])
  const [speaking, setSpeaking] = useState(false)
  const current = useRef<Playback | null>(null)

  const release = useCallback((p: Playback) => {
    p.abort.abort()
    p.audio?.pause()
    if (p.url) URL.revokeObjectURL(p.url)
    synth?.cancel()
    p.resolve() // unblock awaiting callers (e.g. the guided tour) when stopped or superseded
  }, [])

  useEffect(() => {
    if (!synth) return
    const load = () => setVoices(synth.getVoices())
    load()
    synth.addEventListener('voiceschanged', load)
    return () => synth.removeEventListener('voiceschanged', load)
  }, [])

  useEffect(
    () => () => {
      if (current.current) release(current.current)
    },
    [release],
  )

  const supported = typeof Audio !== 'undefined' || synth !== undefined

  /** True when the backend or an installed browser voice can speak the language. */
  const canSpeak = useCallback(
    (lang: string) => SERVER_LANGS.has(baseLang(lang)) || pickVoice(voices, lang) !== undefined,
    [voices],
  )

  const stop = useCallback(() => {
    if (current.current) release(current.current)
    current.current = null
    setSpeaking(false)
  }, [release])

  const speakInBrowser = useCallback(
    (p: Playback, text: string, lang: string, fallback: SpeechFallback | undefined, done: () => void) => {
      if (!synth) return done()
      const available = voices.length > 0 ? voices : synth.getVoices()
      let voice = pickVoice(available, lang)
      let say = { text, lang }
      if (!voice && fallback) {
        voice = pickVoice(available, fallback.lang)
        say = fallback
      }
      const parts = chunk(say.text)
      p.utterances = parts.map((part, i) => {
        const u = new SpeechSynthesisUtterance(part)
        if (voice) u.voice = voice
        u.lang = voice?.lang ?? say.lang
        u.rate = 0.95
        u.onerror = done
        if (i === parts.length - 1) u.onend = done
        return u
      })
      synth.cancel()
      // Chrome can drop an utterance queued in the same tick as cancel()
      setTimeout(() => current.current === p && p.utterances.forEach((u) => synth.speak(u)), 60)
    },
    [voices],
  )

  /**
   * Speaks `text` using backend neural audio; falls back to a browser voice (or `fallback`,
   * e.g. the English alert) if the backend is unreachable. Resolves when speech ends or is stopped.
   */
  const speak = useCallback(
    (text: string, lang: string, fallback?: SpeechFallback): Promise<void> =>
      new Promise((resolve) => {
        if (current.current) release(current.current)
        const p: Playback = { abort: new AbortController(), resolve, utterances: [] }
        current.current = p
        setSpeaking(true)

        const done = () => {
          // A stopped or superseded request must not reset state owned by a newer one
          if (current.current === p) {
            release(p)
            current.current = null
            setSpeaking(false)
          }
          resolve()
        }
        const toBrowser = () => {
          if (current.current !== p) return resolve()
          speakInBrowser(p, text, lang, fallback, done)
        }

        if (!SERVER_LANGS.has(baseLang(lang))) return toBrowser()
        fetchSpeech(text, baseLang(lang), p.abort.signal)
          .then((blob) => {
            if (current.current !== p) return resolve()
            p.url = URL.createObjectURL(blob)
            p.audio = new Audio(p.url)
            p.audio.onended = done
            p.audio.onerror = toBrowser
            return p.audio.play()
          })
          .catch(toBrowser)
      }),
    [release, speakInBrowser],
  )

  return { speak, stop, speaking, canSpeak, supported }
}

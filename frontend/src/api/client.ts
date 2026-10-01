import type { ForecastQuery } from '../types/forecast'

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api/v1'

export const metaUrl = (): string => `${API_BASE}/forecast/meta`

export function gridUrl(q: ForecastQuery): string {
  const params = new URLSearchParams({
    date: q.date,
    lead_time: String(q.leadTime),
    variable: q.variable,
    layer: q.layer,
  })
  return `${API_BASE}/forecast/grid?${params}`
}

export function alertsUrl(q: Pick<ForecastQuery, 'date' | 'leadTime' | 'variable'>): string {
  const params = new URLSearchParams({ date: q.date, lead_time: String(q.leadTime), variable: q.variable })
  return `${API_BASE}/forecast/alerts?${params}`
}

async function request<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) {
    const detail = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText}${detail ? `: ${detail.slice(0, 200)}` : ''}`)
  }
  return res.json() as Promise<T>
}

// Small in-memory response cache so playback frames and toggles are instant after first load
const CACHE_LIMIT = 60
const cache = new Map<string, Promise<unknown>>()

export function fetchJson<T>(url: string): Promise<T> {
  const hit = cache.get(url)
  if (hit) {
    cache.delete(url)
    cache.set(url, hit) // refresh LRU position
    return hit as Promise<T>
  }
  const pending = request<T>(url).catch((err: unknown) => {
    cache.delete(url)
    throw err
  })
  cache.set(url, pending)
  if (cache.size > CACHE_LIMIT) cache.delete(cache.keys().next().value as string)
  return pending
}

export function prefetch(url: string): void {
  fetchJson(url).catch(() => undefined)
}

/** Spoken audio for a warning, synthesized by the backend (works in browsers without Indian voices). */
async function requestSpeech(text: string, lang: string): Promise<Blob> {
  const res = await fetch(`${API_BASE}/tts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, lang }),
  })
  if (!res.ok) throw new Error(`TTS ${res.status} ${res.statusText}`)
  return res.blob()
}

// Audio is preloaded when a warning opens, so "Listen" plays instantly; in-flight requests are shared
const SPEECH_CACHE_LIMIT = 24
const speechCache = new Map<string, Promise<Blob>>()

export function loadSpeech(text: string, lang: string): Promise<Blob> {
  const key = `${lang}|${text}`
  const hit = speechCache.get(key)
  if (hit) {
    speechCache.delete(key)
    speechCache.set(key, hit) // refresh LRU position
    return hit
  }
  const pending = requestSpeech(text, lang).catch((err: unknown) => {
    speechCache.delete(key) // let a later click retry
    throw err
  })
  speechCache.set(key, pending)
  if (speechCache.size > SPEECH_CACHE_LIMIT) speechCache.delete(speechCache.keys().next().value as string)
  return pending
}

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

export function alertsUrl(q: Pick<ForecastQuery, 'date' | 'leadTime'>): string {
  const params = new URLSearchParams({ date: q.date, lead_time: String(q.leadTime) })
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

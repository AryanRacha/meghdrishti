import { useEffect, useState } from 'react'
import { fetchJson } from '../api/client'

interface ApiState<T> {
  data: T | null
  error: string | null
  loading: boolean
}

interface Settled<T> {
  url: string | null
  data: T | null
  error: string | null
}

/** Fetches `url` whenever it changes. Keeps the previous data while loading; ignores superseded responses. */
export function useApi<T>(url: string | null): ApiState<T> {
  const [settled, setSettled] = useState<Settled<T>>({ url: null, data: null, error: null })

  useEffect(() => {
    if (url === null) return
    let active = true

    fetchJson<T>(url)
      .then((data) => active && setSettled({ url, data, error: null }))
      .catch((err: unknown) => {
        if (!active) return
        const message = err instanceof Error ? err.message : String(err)
        setSettled((s) => ({ url, data: s.data, error: message }))
      })

    return () => {
      active = false
    }
  }, [url])

  // Loading is derived: the latest settled response is for an older URL
  return { data: settled.data, error: settled.error, loading: url !== null && settled.url !== url }
}

import { useEffect } from 'react'
import { useMap } from 'react-leaflet'

const INDIA_VIEW = { center: [23, 82] as [number, number], zoom: 5 }

/** Flies the map to INDIA_VIEW whenever `resetKey` changes (after the first render). */
export function MapController({ resetKey }: { resetKey: number }) {
  const map = useMap()

  useEffect(() => {
    if (resetKey === 0) return
    map.flyTo(INDIA_VIEW.center, INDIA_VIEW.zoom, { duration: 1.2 })
  }, [resetKey, map])

  return null
}
